"""
Input validation utilities for YTSave
"""
import re
import os


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate if a URL is a valid YouTube video, shorts, or playlist URL.
    """
    patterns = [
        r'^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}',
        r'^(https?://)?(www\.)?youtu\.be/[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def is_playlist_url(url: str) -> bool:
    """Check if URL is a YouTube playlist."""
    return bool(re.match(r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+', url))


def extract_video_id(url: str) -> str | None:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'youtube\.com/watch\?v=([\w-]{11})',
        r'youtube\.com/shorts/([\w-]{11})',
        r'youtu\.be/([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing invalid characters.
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters and leading/trailing whitespace
    filename = ''.join(c for c in filename if ord(c) >= 32)
    filename = filename.strip()
    
    # Limit filename length
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename or "download"


def validate_quality(quality: str, available: list) -> str:
    """Validate and return the best matching quality."""
    if quality in available:
        return quality
    # Return highest available quality
    return available[0] if available else None


def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """Format file size to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"
