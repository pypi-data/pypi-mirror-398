"""
YouTube Downloader Core Module
"""

import os
import yt_dlp
import json
from typing import Optional, Dict, List, Callable
from .utils import VideoInfo, AudioInfo, DownloadProgress


class YouTubeDownloader:
    """YouTube video and audio downloader"""
    
    def __init__(self, cookies_file: Optional[str] = None, output_dir: str = "downloads", 
                 download_thumbnail: bool = True, export_metadata: bool = True):
        """
        Initialize downloader
        
        Args:
            cookies_file: Path to cookies file (optional, auto-detects if None)
            output_dir: Download directory
            download_thumbnail: Download thumbnail
            export_metadata: Export video metadata
        """
        # Auto-detect cookies file if not provided
        if cookies_file is None:
            cookies_file = self._auto_detect_cookies()
        
        self.cookies_file = cookies_file
        self.output_dir = output_dir
        self.enable_thumbnail_download = download_thumbnail
        self.enable_metadata_export = export_metadata
        self._ensure_output_dir()
        
        # Print cookies status
        if self.cookies_file and os.path.exists(self.cookies_file):
            print(f"Using cookies file: {self.cookies_file}")
        else:
            print("No cookies file found - using public access only")
    
    def _auto_detect_cookies(self) -> Optional[str]:
        """Auto-detect cookies file in common locations"""
        possible_paths = [
            "cookies.txt",
            "./cookies.txt", 
            "youtube_cookies.txt",
            "./youtube_cookies.txt",
            "yt_cookies.txt",
            "./yt_cookies.txt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
        
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _get_ydl_opts(self, format_selector: str = "best", 
                      progress_hook: Optional[Callable] = None) -> Dict:
        """Configure yt-dlp options"""
        opts = {
            'format': format_selector,
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
            'noplaylist': True,
        }
        
        if self.enable_thumbnail_download:
            opts['writethumbnail'] = True
        
        if self.cookies_file and os.path.exists(self.cookies_file):
            opts['cookiefile'] = self.cookies_file
            
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
            
        return opts
    
    def _export_metadata(self, info: Dict, video_id: str) -> Optional[str]:
        """Export video metadata to JSON file"""
        if not self.enable_metadata_export:
            return None
        
        metadata = {
            "id": video_id,
            "title": info.get('title', 'Unknown'),
            "author": info.get('uploader', 'Unknown'),
            "channel_id": info.get('channel_id', 'Unknown'),
            "length": info.get('duration', 0),
            "views": info.get('view_count', 0),
            "publish_date": info.get('upload_date', 'None'),
            "description": info.get('description', ''),
            "url": info.get('webpage_url', ''),
            "thumbnail_url": info.get('thumbnail', '')
        }
        
        metadata_file = os.path.join(self.output_dir, f"{video_id}.json")
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return metadata_file
        except Exception:
            return None
    
    def get_video_info(self, url: str) -> VideoInfo:
        """
        Get video information
        
        Args:
            url: Video URL
            
        Returns:
            VideoInfo: Video information
        """
        with yt_dlp.YoutubeDL(self._get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_id = info.get('id', 'unknown')
            metadata_file = self._export_metadata(info, video_id)
            
            return VideoInfo(
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                uploader=info.get('uploader', 'Unknown'),
                view_count=info.get('view_count', 0),
                upload_date=info.get('upload_date', ''),
                formats=self._extract_formats(info.get('formats', [])),
                metadata_file=metadata_file
            )
    
    def _extract_formats(self, formats: List[Dict]) -> List[Dict]:
        """Extract available formats"""
        extracted = []
        for fmt in formats:
            if fmt.get('vcodec') != 'none':  # video
                extracted.append({
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'quality': fmt.get('height', 0),
                    'filesize': fmt.get('filesize', 0),
                    'type': 'video'
                })
            elif fmt.get('acodec') != 'none':  # audio
                extracted.append({
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'abr': fmt.get('abr', 0),
                    'filesize': fmt.get('filesize', 0),
                    'type': 'audio'
                })
        return extracted
    
    def download_video(self, url: str, quality: str = "best", 
                      progress_callback: Optional[Callable] = None) -> VideoInfo:
        """
        Download video
        
        Args:
            url: Video URL
            quality: Video quality (best, worst, 720p, 480p, etc.)
            progress_callback: Progress callback function
            
        Returns:
            VideoInfo: Downloaded video information
        """
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                progress = DownloadProgress(
                    downloaded_bytes=d.get('downloaded_bytes', 0),
                    total_bytes=d.get('total_bytes', 0),
                    speed=d.get('speed', 0),
                    eta=d.get('eta', 0)
                )
                progress_callback(progress)
        
        format_selector = self._build_format_selector(quality, 'video')
        opts = self._get_ydl_opts(format_selector, progress_hook)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            video_id = info.get('id', 'unknown')
            metadata_file = self._export_metadata(info, video_id)
            
            return VideoInfo(
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                uploader=info.get('uploader', 'Unknown'),
                view_count=info.get('view_count', 0),
                upload_date=info.get('upload_date', ''),
                file_path=ydl.prepare_filename(info),
                metadata_file=metadata_file
            )
    
    def download_audio(self, url: str, format: str = "mp3", 
                      progress_callback: Optional[Callable] = None) -> AudioInfo:
        """
        Download audio only
        
        Args:
            url: Video URL
            format: Audio format (mp3, m4a, wav)
            progress_callback: Progress callback function
            
        Returns:
            AudioInfo: Downloaded audio information
        """
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                progress = DownloadProgress(
                    downloaded_bytes=d.get('downloaded_bytes', 0),
                    total_bytes=d.get('total_bytes', 0),
                    speed=d.get('speed', 0),
                    eta=d.get('eta', 0)
                )
                progress_callback(progress)
        
        opts = self._get_ydl_opts('bestaudio/best', progress_hook)
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '192',
        }]
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            video_id = info.get('id', 'unknown')
            self._export_metadata(info, video_id)
            
            return AudioInfo(
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                uploader=info.get('uploader', 'Unknown'),
                format=format,
                file_path=ydl.prepare_filename(info).replace('.webm', f'.{format}').replace('.m4a', f'.{format}')
            )
    
    def _build_format_selector(self, quality: str, media_type: str) -> str:
        """Build format selector"""
        if quality == "best":
            return "best"
        elif quality == "worst":
            return "worst"
        elif quality.endswith('p'):
            height = quality[:-1]
            return f"best[height<={height}]"
        else:
            return quality
    
    async def download_async(self, url: str, quality: str = "best", 
                           is_audio: bool = False, 
                           progress_callback: Optional[Callable] = None) -> Dict:
        """
        Advanced download with async support
        
        Args:
            url: Video URL
            quality: Video quality
            is_audio: Download audio only
            progress_callback: Progress callback function
            
        Returns:
            Dict: Download information
        """
        import asyncio
        
        def sync_download():
            if is_audio:
                return self.download_audio(url, format="mp3", progress_callback=progress_callback)
            else:
                return self.download_video(url, quality=quality, progress_callback=progress_callback)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_download)
        
        return {
            "success": True,
            "file_path": result.file_path,
            "metadata_file": getattr(result, 'metadata_file', None),
            "title": result.title,
            "duration": result.duration,
            "uploader": result.uploader
        }
    
    def download_thumbnail(self, url: str, quality: str = "maxres") -> Optional[str]:
        """Download thumbnail only"""
        opts = self._get_ydl_opts()
        opts.update({
            'writethumbnail': True,
            'skip_download': True,
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
        })
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info.get('id', 'unknown')
                
                possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                for ext in possible_extensions:
                    thumbnail_path = os.path.join(self.output_dir, f"{video_id}{ext}")
                    if os.path.exists(thumbnail_path):
                        if not ext == '.jpg':
                            new_path = os.path.join(self.output_dir, f"{video_id}.jpg")
                            try:
                                os.rename(thumbnail_path, new_path)
                                return new_path
                            except:
                                pass
                        return thumbnail_path
                
                return None
        except Exception:
            return None