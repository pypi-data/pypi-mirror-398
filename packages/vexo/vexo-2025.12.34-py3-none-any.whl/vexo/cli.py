#!/usr/bin/env python3
"""
Vexo CLI - Simple YouTube downloader command line interface
"""

import sys
import os
import asyncio
import argparse
from .service import DownloadService


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Vexo - The simplest YouTube downloader",
        prog="vexo"
    )
    
    parser.add_argument(
        "url",
        help="YouTube video URL"
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default="./downloads",
        help="Download path (default: ./downloads)"
    )
    
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Download audio only"
    )
    
    parser.add_argument(
        "--quality",
        default="360p",
        help="Video quality (default: 360p)"
    )
    
    parser.add_argument(
        "--no-thumbnail",
        action="store_true",
        help="Don't download thumbnail"
    )
    
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't export metadata"
    )
    
    parser.add_argument(
        "--cookies",
        default=None,
        help="Path to cookies file (auto-detects if not specified)"
    )
    
    args = parser.parse_args()
    
    # Create download path
    os.makedirs(args.path, exist_ok=True)
    
    # Create service
    service = DownloadService(
        url=args.url,
        path=os.path.join(args.path, "%(id)s.%(ext)s"),
        quality="audio" if args.audio else args.quality,
        is_audio=args.audio,
        download_thumbnail=not args.no_thumbnail,
        export_metadata=not args.no_metadata,
        cookies_file=args.cookies  # Will auto-detect if None
    )
    
    print(f"Downloading from: {args.url}")
    print(f"Output path: {args.path}")
    print(f"Type: {'Audio' if args.audio else 'Video'}")
    print(f"Quality: {args.quality if not args.audio else 'Audio'}")
    print()
    
    try:
        # Run download
        result = asyncio.run(service.download_async())
        
        if result["success"]:
            print(f"Download completed successfully!")
            print(f"Title: {result['title']}")
            print(f"File: {result['file_path']}")
            
            if result.get('metadata_file'):
                print(f"Metadata: {result['metadata_file']}")
        else:
            print(f"Download failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()