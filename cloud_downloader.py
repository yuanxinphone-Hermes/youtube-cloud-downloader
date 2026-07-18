#!/usr/bin/env python3
"""
Cloud YouTube Downloader for GitHub Actions
- Reads URLs from stdin or args
- Downloads as MP4 using yt-dlp
- Outputs to ./downloads/ for artifact upload
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path


def parse_urls(urls_input: str):
    """Parse URLs from multiline string or comma-separated"""
    urls = []
    for line in urls_input.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Handle comma-separated on same line
            for url in line.split(','):
                url = url.strip()
                if url:
                    urls.append(url)
    return urls


def build_ydl_opts(quality: str, proxy: str, template: str, out_dir: Path):
    """Build yt-dlp options dict"""
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
        'no_warnings': False,
        'quiet': False,
        'retries': 3,
        'fragment_retries': 3,
        'concurrent_fragment_downloads': 4,
    }
    
    if proxy:
        opts['proxy'] = proxy
    
    return opts


def main():
    parser = argparse.ArgumentParser(description='Download YouTube videos as MP4')
    parser.add_argument('--urls', required=True, help='YouTube URLs (newline or comma separated)')
    parser.add_argument('--quality', default='best', 
                       choices=['best', '1080p', '720p', '480p', '360p', 'audio'])
    parser.add_argument('--proxy', default='', help='Proxy URL (socks5:// or http://)')
    parser.add_argument('--template', default='%(uploader)s/%(title)s.%(ext)s',
                       help='Output filename template')
    parser.add_argument('--out-dir', default='downloads', help='Output directory')
    
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
    
    # Build yt-dlp command
    opts = build_ydl_opts(args.quality, args.proxy, args.template, out_dir)
    
    cmd = ['python', '-m', 'yt_dlp']
    for key, value in opts.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f'--{key}')
        else:
            cmd.extend([f'--{key.replace("_", "-")}', str(value)])
    cmd.extend(urls)
    
    print(f"\nRunning: {' '.join(cmd[:10])}... [+{len(urls)} URLs]")
    print(f"Output dir: {out_dir.absolute()}")
    print("-" * 60)
    
    # Run download
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"\nyt-dlp exited with code {result.returncode}", file=sys.stderr)
    except Exception as e:
        print(f"Error running yt-dlp: {e}", file=sys.stderr)
    
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