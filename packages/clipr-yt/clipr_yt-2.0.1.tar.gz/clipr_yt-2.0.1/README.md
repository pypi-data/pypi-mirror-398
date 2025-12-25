# Clipr 🎬

> Grab any video. Instantly.

A powerful YouTube video downloader with CLI and web interface.

[![PyPI version](https://badge.fury.io/py/clipr-yt.svg)](https://pypi.org/project/clipr-yt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎬 **4K Video Downloads** - Up to 4K resolution
- 🎵 **Audio Extraction** - Download as MP3
- 📋 **Playlist Support** - Download entire playlists
- 🌐 **Web Interface** - Modern, responsive UI
- 💻 **CLI Interface** - Full command-line support
- 📊 **Progress Tracking** - Real-time progress

## Installation

```bash
pip install clipr-yt
```

### Requirements
- Python 3.8+
- FFmpeg (for merging video + audio)

```bash
# Install FFmpeg
# Windows
winget install FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

## Usage

### Command Line

```bash
# Download video
clipr https://youtube.com/watch?v=VIDEO_ID

# Specify quality
clipr https://youtube.com/watch?v=VIDEO_ID -q 1080p

# Download audio only
clipr https://youtube.com/watch?v=VIDEO_ID -a

# Download playlist
clipr https://youtube.com/playlist?list=PLAYLIST_ID

# Start web interface
clipr --server
```

### Web Interface

```bash
clipr --server
# Open http://localhost:3000
```

## CLI Options

| Option | Description |
|--------|-------------|
| `-q, --quality` | Video quality (2160p, 1080p, 720p...) |
| `-a, --audio-only` | Download audio as MP3 |
| `-o, --output` | Output directory |
| `-p, --playlist` | Force playlist mode |
| `--server` | Start web interface |
| `--port` | Server port (default: 3000) |

## License

MIT © Nikshey Yadav
