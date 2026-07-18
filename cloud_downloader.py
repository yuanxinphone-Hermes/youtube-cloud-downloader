#!/usr/bin/env python3
"""
Cloud YouTube Downloader for GitHub Actions
Uses yt-dlp Python API with robust format selection and cookie support
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp not installed. Run: pip install yt-dlp", file=sys.stderr)
    sys.exit(1)


def parse_urls(urls_input: str):
    """Parse URLs from multiline string or comma-separated"""
    urls = []
    for line in urls_input.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            for url in line.split(','):
                url = url.strip()
                if url:
                    urls.append(url)
    return urls


def build_ydl_opts(quality: str, proxy: str, template: str, out_dir: Path, cookies: str = None):
    """Build yt-dlp options dict for Python API - robust format selection"""
    
    # Most permissive format selectors
    quality_formats = {
        "best": "bv*+ba/b",                    # Best video + best audio / best single
        "1080p": "bv*[height<=1080]+ba/b[height<=1080]",
        "720p": "bv*[height<=720]+ba/b[height<=720]",
        "480p": "bv*[height<=480]+ba/b[height<=480]",
        "360p": "bv*[height<=360]+ba/b[height<=360]",
        "audio": "ba",                          # Best audio only
    }
    
    format_selector = quality_formats.get(quality, quality_formats["best"])
    
    opts = {
        'format': format_selector,
        'merge_output_format': 'mp4',
        'outtmpl': str(out_dir / template),
        'nocheckcertificate': True,
        'retries': 3,
        'fragment_retries': 3,
        'concurrent_fragment_downloads': 4,
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': False,
        # Extractor args: use web client (supports cookies), android as fallback
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android'],
                'skip': ['dash', 'hls'],
            }
        },
        # Additional options to help with bot detection
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    if proxy:
        opts['proxy'] = proxy
    
    if cookies:
        cookies_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        cookies_file.write(cookies)
        cookies_file.close()
        opts['cookiefile'] = cookies_file.name
        opts['_cookies_temp_file'] = cookies_file.name
        print(f"Cookie file created: {cookies_file.name}")
    else:
        print("WARNING: No cookies provided - YouTube will likely block the request")
    
    return opts


class ProgressLogger:
    """Logger to capture yt-dlp output"""
    def debug(self, msg):
        if msg.strip() and not msg.startswith('[debug]'):
            print(msg)
    
    def info(self, msg):
        if msg.strip():
            print(msg)
    
    def warning(self, msg):
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        print(f"ERROR: {msg}")


def main():
    parser = argparse.ArgumentParser(description='Download YouTube videos as MP4')
    parser.add_argument('--urls', required=True, help='YouTube URLs (newline or comma separated)')
    parser.add_argument('--quality', default='best', 
                       choices=['best', '1080p', '720p', '480p', '360p', 'audio'])
    parser.add_argument('--proxy', default='', help='Proxy URL (socks5:// or http://)')
    parser.add_argument('--template', default='%(uploader)s/%(title)s.%(ext)s',
                       help='Output filename template')
    parser.add_argument('--out-dir', default='downloads', help='Output directory')
    parser.add_argument('--cookies', default='', help='YouTube cookies (Netscape format)')
    
    args = parser.parse_args()
    
    # Parse URLs
    urls = parse_urls(args.urls)
    if not urls:
        print("ERROR: No valid URLs provided", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(urls)} URL(s) to download")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    # Prepare output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {out_dir.absolute()}")
    print("-" * 60)
    
    # Get cookies from arg or env var
    cookies = args.cookies or os.environ.get('YOUTUBE_COOKIES', '')
    if cookies:
        print("Using YouTube cookies for authentication")
    else:
        print("WARNING: No cookies provided - YouTube may block the request")
    
    # Build options
    ydl_opts = build_ydl_opts(args.quality, args.proxy, args.template, out_dir, cookies)
    ydl_opts['logger'] = ProgressLogger()
    
    # Track temp cookie file for cleanup
    cookies_temp_file = ydl_opts.pop('_cookies_temp_file', None)
    
    # Download using Python API
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
    except Exception as e:
        print(f"\nDownload failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup temp cookie file
        if cookies_temp_file and os.path.exists(cookies_temp_file):
            try:
                os.unlink(cookies_temp_file)
            except:
                pass
    
    # List downloaded files (any video format)
    video_files = []
    for ext in ['*.mp4', '*.mkv', '*.webm', '*.mov', '*.flv', '*.m4v']:
        video_files.extend(out_dir.rglob(ext))
    
    print(f"\n{'='*60}")
    print(f"Downloaded {len(video_files)} video file(s):")
    for f in video_files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.relative_to(out_dir)} ({size_mb:.1f} MB)")
    
    if not video_files:
        print("  (No video files found - check logs above)")
        sys.exit(1)


def parse_urls(urls_input: str):
    """Parse URLs from multiline string or comma-separated"""
    urls = []
    for line in urls_input.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            for url in line.split(','):
                url = url.strip()
                if url:
                    urls.append(url)
    return urls


if __name__ == '__main__':
    main()