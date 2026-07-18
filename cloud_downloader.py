#!/usr/bin/env python3
"""
Cloud YouTube Downloader for GitHub Actions
Uses yt-dlp Python API directly with cookie support
"""
import argparse
import os
import sys
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
    """Build yt-dlp options dict for Python API"""
    quality_formats = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
        "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
        "audio": "bestaudio[ext=m4a]/bestaudio",
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
        # Additional options to help with YouTube bot detection
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls'],
            }
        },
    }
    
    if proxy:
        opts['proxy'] = proxy
    
    if cookies:
        # Write cookies to temp file and pass to yt-dlp
        import tempfile
        cookies_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        cookies_file.write(cookies)
        cookies_file.close()
        opts['cookiefile'] = cookies_file.name
        # Store temp file path for cleanup
        opts['_cookies_temp_file'] = cookies_file.name
    
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
    
    # List downloaded files
    mp4_files = list(out_dir.rglob('*.mp4'))
    print(f"\n{'='*60}")
    print(f"Downloaded {len(mp4_files)} MP4 file(s):")
    for f in mp4_files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.relative_to(out_dir)} ({size_mb:.1f} MB)")
    
    if not mp4_files:
        print("  (No MP4 files found - check logs above)")
        sys.exit(1)


if __name__ == '__main__':
    main()