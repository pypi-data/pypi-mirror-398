"""
Vexo - YouTube Downloader Library
Python library for downloading videos and audio from YouTube
"""

__version__ = "2025.12.34"
__author__ = "Vexo Team"
__email__ = "contact@vexo.dev"

from .downloader import YouTubeDownloader
from .utils import VideoInfo, AudioInfo, DownloadProgress
from .service import DownloadService, download

__all__ = [
    "YouTubeDownloader",
    "VideoInfo",
    "AudioInfo", 
    "DownloadProgress",
    "DownloadService",
    "download",
]