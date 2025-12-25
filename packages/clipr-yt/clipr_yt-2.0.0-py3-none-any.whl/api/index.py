"""
Clipr - Vercel Serverless Function

Self-contained Flask app for Vercel deployment.
"""
import os
import re
from flask import Flask, request, jsonify, send_file, Response

# Initialize Flask app
app = Flask(__name__)

# ============== Validators (inline) ==============

def is_valid_youtube_url(url):
    """Validate YouTube URL."""
    patterns = [
        r'^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}',
        r'^(https?://)?(www\.)?youtu\.be/[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def format_duration(seconds):
    """Format duration."""
    if not seconds:
        return "0:00"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# ============== Static Files ==============

@app.route('/')
def index():
    """Serve the main web UI."""
    static_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
    if os.path.exists(static_path):
        return send_file(static_path)
    return "<h1>Clipr</h1><p>Static files not found.</p>"


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Not found", 404


@app.route('/static/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    css_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'css')
    file_path = os.path.join(css_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='text/css')
    return "Not found", 404


@app.route('/static/js/<path:filename>')
def serve_js(filename):
    """Serve JS files."""
    js_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'js')
    file_path = os.path.join(js_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/javascript')
    return "Not found", 404


# ============== API Endpoints ==============

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video metadata from URL."""
    try:
        from pytubefix import YouTube
    except ImportError as e:
        return jsonify({'error': f'Import error: {str(e)}'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    try:
        yt = YouTube(url)
        
        # Get available qualities
        streams = yt.streams.filter(adaptive=True, file_extension="mp4", only_video=True)
        qualities = sorted(
            list(set(s.resolution for s in streams if s.resolution)),
            key=lambda x: int(x.replace('p', '')),
            reverse=True
        )
        
        return jsonify({
            'success': True,
            'video': {
                'id': yt.video_id,
                'title': yt.title,
                'author': yt.author,
                'duration': yt.length,
                'duration_formatted': format_duration(yt.length),
                'thumbnail': yt.thumbnail_url,
                'views': yt.views,
                'qualities': qualities,
                'url': url
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def get_download_url():
    """Get direct download URL for a video."""
    try:
        from pytubefix import YouTube
    except ImportError as e:
        return jsonify({'error': f'Import error: {str(e)}'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    url = data.get('url', '').strip()
    quality = data.get('quality')
    audio_only = data.get('audioOnly', False)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    try:
        yt = YouTube(url)
        
        if audio_only:
            stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        else:
            if quality:
                stream = yt.streams.filter(
                    adaptive=True, file_extension="mp4", only_video=True, resolution=quality
                ).first()
            
            if not quality or not stream:
                stream = yt.streams.filter(
                    adaptive=True, file_extension="mp4", only_video=True
                ).order_by("resolution").desc().first()
        
        if not stream:
            return jsonify({'error': 'No suitable stream found'}), 404
        
        return jsonify({
            'success': True,
            'downloadUrl': stream.url,
            'title': yt.title,
            'quality': getattr(stream, 'resolution', None) or getattr(stream, 'abr', 'Unknown'),
            'message': 'Note: On web, video and audio are separate streams.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/formats', methods=['GET'])
def get_formats():
    """Get available formats."""
    return jsonify({
        'videoQualities': ["2160p", "1440p", "1080p", "720p", "480p", "360p"],
        'audioQualities': ["320kbps", "192kbps", "128kbps"]
    })


@app.route('/api/downloads', methods=['GET'])
def get_all_downloads():
    """Download list not available on serverless."""
    return jsonify({'downloads': []})


@app.route('/api/progress/<download_id>', methods=['GET'])
def get_progress(download_id):
    """Progress not available on serverless."""
    return jsonify({
        'id': download_id,
        'status': 'not_available',
        'message': 'Progress tracking not available on serverless'
    })


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# Vercel expects 'app' to be the WSGI application
# No need for a separate handler function
