# vexo

**vexo** — The simplest YouTube downloader (CLI + Python API)

## Installation

Verify you have Python 3.x:

```bash
python --version
```

Install vexo:

```bash
pip install vexo
```

## Upgrade

```bash
pip install --upgrade vexo
```

## Quick Start (CLI)

```bash
vexo "YOUTUBE_LINK" [PATH]
```

### Examples

```bash
# Download a video (interactive selection if needed)
vexo "https://www.youtube.com/watch?v=VIDEO_ID"

# Download audio only
vexo "https://www.youtube.com/watch?v=VIDEO_ID" --audio

# Download to a specific folder
vexo "https://www.youtube.com/watch?v=VIDEO_ID" ./downloads

# Download with specific quality
vexo "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p
```

## Python API (async)

Use the async DownloadService to integrate vexo into bots and other apps.

```python
from vexo import DownloadService
import os
from typing import Union
import asyncio

async def download(bot_username, link, video: Union[bool, str] = None):
    is_audio = not bool(video)
    service = DownloadService(
        url=link,
        path="downloads/%(id)s.%(ext)s",
        quality="360p" if not is_audio else "audio",
        is_audio=is_audio, 
        download_thumbnail=True, 
        export_metadata=True
        # cookies_file="cookies.txt"  # Optional: auto-detects if available
    )
    return await service.download_async()

# Example runner:
# asyncio.run(download("botname", "https://www.youtube.com/watch?v=VIDEO_ID", video=True))
```

### Simple API

```python
from vexo import download
import asyncio

async def main():
    # Download video (auto-detects cookies if available)
    result = await download("botname", "https://www.youtube.com/watch?v=VIDEO_ID", video=True)
    
    # Download audio with custom cookies
    result = await download("botname", "https://www.youtube.com/watch?v=VIDEO_ID", 
                          video=False, cookies_file="my_cookies.txt")
    
    print(f"Downloaded: {result['title']}")
    print(f"File: {result['file_path']}")

asyncio.run(main())
```

## Cookies Support

Vexo automatically detects and uses cookies for accessing restricted content.

### Auto-Detection
Place any of these files in your project directory:
- `cookies.txt`
- `youtube_cookies.txt` 
- `yt_cookies.txt`

### Manual Cookies
```python
from vexo import YouTubeDownloader

# With custom cookies file
downloader = YouTubeDownloader(cookies_file="path/to/cookies.txt")
audio = downloader.download_audio("https://youtube.com/watch?v=ID")
```

### CLI with Cookies
```bash
# Auto-detect cookies
vexo "https://www.youtube.com/watch?v=VIDEO_ID" --audio

# Custom cookies file  
vexo "https://www.youtube.com/watch?v=VIDEO_ID" --cookies my_cookies.txt
```

### Getting Cookies
1. Install browser extension "Get cookies.txt LOCALLY"
2. Login to YouTube
3. Export cookies as `cookies.txt`
4. Place in your project folder

## Features

- Download YouTube videos in various qualities
- Extract audio in MP3 format
- Download thumbnails automatically
- Export video metadata as JSON
- Async/await support for integration
- Simple CLI interface
- Custom output paths with pattern support
- Cross-platform compatibility

## File Naming

Downloaded files use the pattern `{video_id}.{ext}`:
- Videos: `dQw4w9WgXcQ.mp4`
- Audio: `dQw4w9WgXcQ.mp3`
- Thumbnails: `dQw4w9WgXcQ.jpg`
- Metadata: `dQw4w9WgXcQ.json`

## Metadata Format

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "author": "Rick Astley",
  "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
  "length": 213,
  "views": 1724172072,
  "publish_date": "20091025",
  "description": "The official video...",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
}
```

## Requirements

- Python 3.8+
- yt-dlp

## License

MIT License