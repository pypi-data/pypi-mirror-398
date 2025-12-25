"""
Download Manager Service

Manages concurrent downloads, queue, history, and progress tracking.
"""
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import uuid

from youtube_downloader import YouTubeDownloader, VideoInfo, DownloadProgress
from config import MAX_CONCURRENT_DOWNLOADS, DOWNLOAD_DIR


class DownloadStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class DownloadTask:
    """Represents a download task."""
    id: str
    url: str
    title: str = ""
    quality: str = None
    audio_only: bool = False
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    message: str = ""
    output_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = None
    error: str = None


class DownloadManager:
    """
    Manages multiple downloads with queue support and progress tracking.
    """

    def __init__(self, output_dir: str = None, max_concurrent: int = None):
        self.output_dir = output_dir or DOWNLOAD_DIR
        self.max_concurrent = max_concurrent or MAX_CONCURRENT_DOWNLOADS
        
        self.downloads: Dict[str, DownloadTask] = {}
        self.queue: List[str] = []
        self.active_downloads: List[str] = []
        
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
        
        self.downloader = YouTubeDownloader(
            output_dir=self.output_dir,
            progress_callback=self._handle_progress
        )

    def add_callback(self, callback: Callable):
        """Add a callback for progress updates."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remove a progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_video_info(self, url: str) -> VideoInfo:
        """Get video metadata."""
        return self.downloader.get_video_info(url)

    def add_download(
        self,
        url: str,
        quality: str = None,
        audio_only: bool = False
    ) -> str:
        """
        Add a new download to the queue.
        
        Returns:
            Download task ID
        """
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info for title
        try:
            info = self.get_video_info(url)
            title = info.title
        except Exception:
            title = "Unknown"

        task = DownloadTask(
            id=download_id,
            url=url,
            title=title,
            quality=quality,
            audio_only=audio_only
        )
        
        with self._lock:
            self.downloads[download_id] = task
            self.queue.append(download_id)
        
        # Start processing queue
        self._process_queue()
        
        return download_id

    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download."""
        with self._lock:
            if download_id not in self.downloads:
                return False
            
            task = self.downloads[download_id]
            
            if task.status in [DownloadStatus.COMPLETED, DownloadStatus.CANCELLED]:
                return False
            
            task.status = DownloadStatus.CANCELLED
            task.message = "Cancelled by user"
            
            if download_id in self.queue:
                self.queue.remove(download_id)
            
            if download_id in self.active_downloads:
                self.active_downloads.remove(download_id)
        
        self._notify_callbacks(download_id)
        return True

    def get_download(self, download_id: str) -> Optional[DownloadTask]:
        """Get a download task by ID."""
        return self.downloads.get(download_id)

    def get_all_downloads(self) -> List[DownloadTask]:
        """Get all download tasks."""
        return list(self.downloads.values())

    def get_history(self, limit: int = 50) -> List[DownloadTask]:
        """Get completed downloads history."""
        completed = [
            d for d in self.downloads.values()
            if d.status in [DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELLED]
        ]
        return sorted(completed, key=lambda x: x.created_at, reverse=True)[:limit]

    def clear_history(self):
        """Clear completed downloads from history."""
        with self._lock:
            to_remove = [
                did for did, task in self.downloads.items()
                if task.status in [DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELLED]
            ]
            for did in to_remove:
                del self.downloads[did]

    def _process_queue(self):
        """Process the download queue."""
        with self._lock:
            while self.queue and len(self.active_downloads) < self.max_concurrent:
                download_id = self.queue.pop(0)
                task = self.downloads.get(download_id)
                
                if not task or task.status == DownloadStatus.CANCELLED:
                    continue
                
                self.active_downloads.append(download_id)
                
                # Start download in a new thread
                thread = threading.Thread(
                    target=self._execute_download,
                    args=(download_id,)
                )
                thread.daemon = True
                thread.start()

    def _execute_download(self, download_id: str):
        """Execute a single download."""
        task = self.downloads.get(download_id)
        if not task:
            return

        try:
            task.status = DownloadStatus.DOWNLOADING
            self._notify_callbacks(download_id)
            
            output_path = self.downloader.download_video(
                url=task.url,
                quality=task.quality,
                audio_only=task.audio_only,
                download_id=download_id
            )
            
            task.output_path = output_path
            task.status = DownloadStatus.COMPLETED
            task.progress = 100.0
            task.completed_at = datetime.now()
            task.message = "Download complete!"

        except Exception as e:
            task.status = DownloadStatus.ERROR
            task.error = str(e)
            task.message = f"Error: {str(e)}"

        finally:
            with self._lock:
                if download_id in self.active_downloads:
                    self.active_downloads.remove(download_id)
            
            self._notify_callbacks(download_id)
            self._process_queue()

    def _handle_progress(self, progress: DownloadProgress):
        """Handle progress updates from the downloader."""
        task = self.downloads.get(progress.download_id)
        if task:
            task.progress = progress.progress
            task.message = progress.message
            
            if progress.status == 'merging':
                task.status = DownloadStatus.MERGING
            
            self._notify_callbacks(progress.download_id)

    def _notify_callbacks(self, download_id: str):
        """Notify all callbacks of a download update."""
        task = self.downloads.get(download_id)
        if task:
            for callback in self._callbacks:
                try:
                    callback(task)
                except Exception:
                    pass


# Global download manager instance
_manager: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """Get the global download manager instance."""
    global _manager
    if _manager is None:
        _manager = DownloadManager()
    return _manager
