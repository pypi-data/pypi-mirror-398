"""
Vexo Download Service
"""

import os
import asyncio
from typing import Union, Optional, Dict, Any
from .downloader import YouTubeDownloader


class DownloadService:
    """Download service for YouTube videos and audio"""
    
    def __init__(self, url: str, path: str = "downloads/%(id)s.%(ext)s", 
                 quality: str = "360p", is_audio: bool = False, 
                 download_thumbnail: Optional[bool] = None, 
                 export_metadata: Optional[bool] = None,
                 cookies_file: Optional[str] = None):
        """
        Initialize download service
        
        Args:
            url: Video URL
            path: Download path with pattern support
            quality: Video quality or "audio" for audio-only
            is_audio: Download audio only
            download_thumbnail: Download thumbnail
            export_metadata: Export metadata
            cookies_file: Path to cookies file (auto-detects if None)
        """
        self.url = url
        self.path = path
        self.quality = quality
        self.is_audio = is_audio
        
        # Set defaults
        self.download_thumbnail = download_thumbnail if download_thumbnail is not None else True
        self.export_metadata = export_metadata if export_metadata is not None else True
        
        # Determine output directory
        if "%(id)s" in path:
            self.output_dir = os.path.dirname(path) or "downloads"
        else:
            self.output_dir = path
        
        # Create downloader with auto-cookies detection
        self.downloader = YouTubeDownloader(
            cookies_file=cookies_file,  # Will auto-detect if None
            output_dir=self.output_dir,
            download_thumbnail=self.download_thumbnail,
            export_metadata=self.export_metadata
        )
    
    async def download_async(self) -> Dict[str, Any]:
        """Download with async support"""
        try:
            result = await self.downloader.download_async(
                url=self.url,
                quality=self.quality,
                is_audio=self.is_audio
            )
            
            # Handle custom path pattern
            if "%(id)s" in self.path and result.get("success"):
                from .utils import extract_video_id
                video_id = extract_video_id(self.url)
                
                if video_id:
                    ext = "mp3" if self.is_audio else "mp4"
                    new_path = self.path.replace("%(id)s", video_id).replace("%(ext)s", ext)
                    
                    if os.path.exists(result["file_path"]) and result["file_path"] != new_path:
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        os.rename(result["file_path"], new_path)
                        result["file_path"] = new_path
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": None,
                "metadata_file": None
            }


async def download(bot_username: str, link: str, video: Union[bool, str] = None, 
                  cookies_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple download function for YouTube videos and audio
    
    Args:
        bot_username: Bot username (for compatibility)
        link: Video URL
        video: True for video, False for audio, or quality string
        cookies_file: Path to cookies file (auto-detects if None)
    
    Returns:
        Dict: Download result
    """
    # Determine download type and quality
    if video is None or video is False:
        is_audio = True
        quality = "audio"
    elif video is True:
        is_audio = False
        quality = "360p"
    else:
        is_audio = False
        quality = str(video)
    
    # Create downloads directory
    voltpath = "downloads"
    os.makedirs(voltpath, exist_ok=True)
    
    # Create service with auto-cookies detection
    service = DownloadService(
        url=link,
        path=os.path.join(voltpath, "%(id)s.%(ext)s"),
        quality=quality,
        is_audio=is_audio,
        download_thumbnail=True,
        export_metadata=True,
        cookies_file=cookies_file  # Will auto-detect if None
    )
    
    return await service.download_async()