"""
Utility functions and classes for Vexo
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class DownloadProgress:
    """Download progress information"""
    downloaded_bytes: int
    total_bytes: int
    speed: float
    eta: int
    
    @property
    def percentage(self) -> float:
        """Download percentage"""
        if self.total_bytes > 0:
            return (self.downloaded_bytes / self.total_bytes) * 100
        return 0.0
    
    @property
    def downloaded_mb(self) -> float:
        """Downloaded data in MB"""
        return self.downloaded_bytes / (1024 * 1024)
    
    @property
    def total_mb(self) -> float:
        """Total data in MB"""
        return self.total_bytes / (1024 * 1024)
    
    @property
    def speed_mb(self) -> float:
        """Download speed in MB/s"""
        return self.speed / (1024 * 1024) if self.speed else 0.0


@dataclass
class VideoInfo:
    """Video information"""
    title: str
    duration: int
    uploader: str
    view_count: int
    upload_date: str
    formats: Optional[List[Dict]] = None
    file_path: Optional[str] = None
    metadata_file: Optional[str] = None
    
    @property
    def duration_formatted(self) -> str:
        """Formatted duration (minutes:seconds)"""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "Unknown"


@dataclass
class AudioInfo:
    """Audio information"""
    title: str
    duration: int
    uploader: str
    format: str
    file_path: Optional[str] = None
    
    @property
    def duration_formatted(self) -> str:
        """Formatted duration (minutes:seconds)"""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "Unknown"


def validate_youtube_url(url: str) -> bool:
    """
    Validate YouTube URL
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid
    """
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g., 15.2 MB)
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL
    
    Args:
        url: YouTube URL
        
    Returns:
        str: Video ID or None
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_thumbnail_path(video_id: str, output_dir: str = "downloads") -> Optional[str]:
    """Get thumbnail file path"""
    import os
    
    # Look for .jpg first (preferred format)
    thumbnail_path = os.path.join(output_dir, f"{video_id}.jpg")
    if os.path.exists(thumbnail_path):
        return thumbnail_path
    
    # Look for other formats
    extensions = ['.jpeg', '.png', '.webp']
    
    for ext in extensions:
        thumbnail_path = os.path.join(output_dir, f"{video_id}{ext}")
        if os.path.exists(thumbnail_path):
            return thumbnail_path
    
    return None


def get_metadata_path(video_id: str, output_dir: str = "downloads") -> Optional[str]:
    """Get metadata file path"""
    import os
    
    metadata_path = os.path.join(output_dir, f"{video_id}.json")
    return metadata_path if os.path.exists(metadata_path) else None