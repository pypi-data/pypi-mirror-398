"""
Clipr CLI - Command Line Interface

Self-contained CLI for pip installation.
"""
import argparse
import sys
import os
import re


def is_valid_youtube_url(url):
    """Validate YouTube URL."""
    patterns = [
        r'^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}',
        r'^(https?://)?(www\.)?youtu\.be/[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def is_playlist_url(url):
    """Check if URL is a playlist."""
    return 'playlist?list=' in url


def format_duration(seconds):
    """Format duration."""
    if not seconds:
        return "0:00"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def create_progress_bar():
    """Create a tqdm progress bar wrapper."""
    try:
        from tqdm import tqdm
    except ImportError:
        # Fallback if tqdm not available
        def update_progress(progress):
            print(f"  {progress.get('message', 'Working...')}")
        return update_progress
    
    pbar = None
    
    def update_progress(progress):
        nonlocal pbar
        
        status = progress.get('status', '')
        message = progress.get('message', '')
        prog = progress.get('progress', 0)
        
        if status == 'pending':
            print(f"\n🎬 {message}")
        elif status == 'downloading':
            if pbar is None:
                pbar = tqdm(total=100, desc="Downloading", unit="%", 
                           bar_format='{l_bar}{bar}| {n:.1f}/{total:.0f}%')
            pbar.n = prog
            pbar.refresh()
        elif status == 'merging':
            if pbar:
                pbar.close()
                pbar = None
            print("\n🔧 Merging video and audio...")
        elif status == 'completed':
            if pbar:
                pbar.close()
            print(f"\n✅ {message}")
        elif status == 'error':
            if pbar:
                pbar.close()
            print(f"\n❌ {message}")
    
    return update_progress


def download_video(url, output_dir=None, quality=None, audio_only=False):
    """Download a single video."""
    try:
        from pytubefix import YouTube
    except ImportError:
        print("❌ pytubefix not installed. Run: pip install pytubefix")
        sys.exit(1)
    
    output_dir = output_dir or os.path.join(os.path.expanduser("~"), "Downloads", "Clipr")
    os.makedirs(output_dir, exist_ok=True)
    
    progress_cb = create_progress_bar()
    
    try:
        print("\n📡 Fetching video information...")
        yt = YouTube(url)
        
        print(f"\n{'─' * 50}")
        print(f"📺 Title:    {yt.title}")
        print(f"👤 Author:   {yt.author}")
        print(f"⏱️  Duration: {format_duration(yt.length)}")
        print(f"{'─' * 50}")
        
        progress_cb({'status': 'pending', 'message': 'Starting download...'})
        
        if audio_only:
            # Download audio only
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not stream:
                print("❌ No audio stream found")
                sys.exit(1)
            
            progress_cb({'status': 'downloading', 'progress': 50, 'message': 'Downloading audio...'})
            output_path = stream.download(output_path=output_dir)
            
            # Convert to MP3 if ffmpeg available
            try:
                base = os.path.splitext(output_path)[0]
                mp3_path = base + '.mp3'
                os.system(f'ffmpeg -i "{output_path}" -q:a 0 "{mp3_path}" -y -loglevel quiet')
                if os.path.exists(mp3_path):
                    os.remove(output_path)
                    output_path = mp3_path
            except:
                pass
            
            progress_cb({'status': 'completed', 'message': 'Audio download complete!'})
            
        else:
            # Download video
            if quality:
                stream = yt.streams.filter(
                    adaptive=True, file_extension="mp4", only_video=True, resolution=quality
                ).first()
            else:
                stream = yt.streams.filter(
                    adaptive=True, file_extension="mp4", only_video=True
                ).order_by('resolution').desc().first()
            
            if not stream:
                # Fall back to progressive stream
                stream = yt.streams.filter(progressive=True, file_extension="mp4"
                ).order_by('resolution').desc().first()
            
            if not stream:
                print("❌ No video stream found")
                sys.exit(1)
            
            progress_cb({'status': 'downloading', 'progress': 30, 'message': 'Downloading video...'})
            video_path = stream.download(output_path=output_dir, filename_prefix="video_")
            
            # For adaptive streams, also download audio
            if stream.is_adaptive:
                progress_cb({'status': 'downloading', 'progress': 60, 'message': 'Downloading audio...'})
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                if audio_stream:
                    audio_path = audio_stream.download(output_path=output_dir, filename_prefix="audio_")
                    
                    # Merge with ffmpeg
                    progress_cb({'status': 'merging', 'progress': 90, 'message': 'Merging...'})
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', yt.title)[:100]
                    final_path = os.path.join(output_dir, f"{safe_title}.mp4")
                    
                    cmd = f'ffmpeg -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{final_path}" -y -loglevel quiet'
                    result = os.system(cmd)
                    
                    if result == 0 and os.path.exists(final_path):
                        os.remove(video_path)
                        os.remove(audio_path)
                        output_path = final_path
                    else:
                        output_path = video_path
                else:
                    output_path = video_path
            else:
                output_path = video_path
            
            progress_cb({'status': 'completed', 'message': 'Video download complete!'})
        
        print(f"\n📁 Saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='clipr',
        description='🎬 Clipr - Grab any video. Instantly.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clipr https://youtube.com/watch?v=xyz          Download video at best quality
  clipr https://youtube.com/watch?v=xyz -q 720p  Download at 720p
  clipr https://youtube.com/watch?v=xyz -a       Download audio only (MP3)
        """
    )
    
    # URL argument
    parser.add_argument('url', nargs='?', default=None,
                       help='YouTube URL to download')
    
    # Download options
    parser.add_argument('-o', '--output', default=None,
                       help='Output directory')
    parser.add_argument('-q', '--quality', default=None,
                       choices=['2160p', '1440p', '1080p', '720p', '480p', '360p'],
                       help='Video quality (default: best available)')
    parser.add_argument('-a', '--audio-only', action='store_true',
                       help='Download audio only (MP3)')
    
    # Version
    parser.add_argument('--version', action='version', version='Clipr 2.0.1')
    
    args = parser.parse_args()
    
    # Require URL
    if not args.url:
        parser.print_help()
        print("\n❌ Error: Please provide a YouTube URL")
        sys.exit(1)
    
    # Validate URL
    if not is_valid_youtube_url(args.url):
        print("❌ Invalid YouTube URL")
        print("   Supported formats:")
        print("   - https://youtube.com/watch?v=VIDEO_ID")
        print("   - https://youtube.com/shorts/VIDEO_ID")
        print("   - https://youtu.be/VIDEO_ID")
        sys.exit(1)
    
    # Download
    download_video(args.url, args.output, args.quality, args.audio_only)


if __name__ == '__main__':
    main()
