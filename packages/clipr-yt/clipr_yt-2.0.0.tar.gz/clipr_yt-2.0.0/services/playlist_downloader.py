"""
Playlist Downloader Service

Handles downloading videos from YouTube playlists.
"""
from dataclasses import dataclass
from typing import List, Optional, Callable
from pytubefix import Playlist

from youtube_downloader import YouTubeDownloader, VideoInfo
from utils.validators import is_playlist_url


@dataclass
class PlaylistInfo:
    """Playlist metadata container."""
    playlist_id: str
    title: str
    owner: str
    video_count: int
    views: int
    videos: List[VideoInfo]


class PlaylistDownloader:
    """
    Downloads all videos from a YouTube playlist.
    """

    def __init__(self, output_dir: str = None, progress_callback: Callable = None):
        self.downloader = YouTubeDownloader(
            output_dir=output_dir,
            progress_callback=progress_callback
        )
        self.output_dir = self.downloader.output_dir

    def get_playlist_info(self, url: str) -> PlaylistInfo:
        """
        Get playlist metadata and video list.
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            PlaylistInfo object with playlist metadata
        """
        if not is_playlist_url(url):
            raise ValueError("Invalid playlist URL")

        playlist = Playlist(url)
        
        videos = []
        for video_url in playlist.video_urls[:50]:  # Limit to 50 for performance
            try:
                info = self.downloader.get_video_info(video_url)
                videos.append(info)
            except Exception:
                continue

        return PlaylistInfo(
            playlist_id=playlist.playlist_id,
            title=playlist.title,
            owner=playlist.owner,
            video_count=len(playlist.video_urls),
            views=playlist.views or 0,
            videos=videos
        )

    def download_playlist(
        self,
        url: str,
        quality: str = None,
        audio_only: bool = False,
        skip_existing: bool = True,
        on_video_complete: Callable = None,
        on_video_error: Callable = None
    ) -> dict:
        """
        Download all videos from a playlist.
        
        Args:
            url: YouTube playlist URL
            quality: Desired video quality
            audio_only: If True, download audio only
            skip_existing: Skip videos that already exist
            on_video_complete: Callback when a video finishes
            on_video_error: Callback when a video fails
            
        Returns:
            Dictionary with download results
        """
        if not is_playlist_url(url):
            raise ValueError("Invalid playlist URL")

        playlist = Playlist(url)
        
        results = {
            "playlist_title": playlist.title,
            "total": len(playlist.video_urls),
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "files": []
        }

        for i, video_url in enumerate(playlist.video_urls):
            try:
                output_path = self.downloader.download_video(
                    url=video_url,
                    quality=quality,
                    audio_only=audio_only
                )
                
                results["completed"] += 1
                results["files"].append(output_path)
                
                if on_video_complete:
                    on_video_complete(i + 1, results["total"], output_path)

            except Exception as e:
                results["failed"] += 1
                
                if on_video_error:
                    on_video_error(i + 1, results["total"], str(e))

        return results
