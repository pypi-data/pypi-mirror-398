# gold-dl — The simplest YouTube downloader (CLI + Python API)

[![Downloads](https://static.pepy.tech/badge/gold-dl)](https://pepy.tech/project/gold-dl)
[![Downloads month](https://static.pepy.tech/badge/gold-dl/month)](https://pepy.tech/project/gold-dl)
[![version](https://img.shields.io/pypi/v/gold-dl.svg)](https://pypi.org/project/gold-dl/)
[![Python Version](https://img.shields.io/pypi/pyversions/gold-dl)](https://pypi.org/project/gold-dl/)
[![License](https://img.shields.io/pypi/l/gold-dl.svg)](https://pypi.org/project/gold-dl/)
[![PyPI stats](https://img.shields.io/badge/pypi%20downloads-check-palegreen.svg)](https://pypistats.org/packages/gold-dl)


![gold-dl screenshot](https://i.ibb.co/Hf5sRvmS/IMG-20251120-013217-680.jpg)

Table of Contents
- Installation
- Upgrade
- Quick Start (CLI)
- Options
- Examples
- Python API
- Screenshots
- Todo
- Contributing
- License
- Badges / Usage

Channel Library : [Source Gold](https://t.me/Source_Goldd)  
Contact / Developer : @CB6BB

Installation
1. Verify you have Python 3.x:
```bash
python --version
```

2. Install gold-dl:
```bash
pip install gold-dl --break-system-packages
```
(If your environment does not require `--break-system-packages`, you may omit it.)

Upgrade
```bash
pip install --upgrade gold-dl --break-system-packages
```

Quick Start (CLI)
```bash
gold-dl "YOUTUBE_LINK" [PATH]
```
- "YOUTUBE_LINK" (required) the YouTube video or playlist URL (wrap in quotes).
- [PATH] (optional) destination folder; defaults to the current working directory.

Common options
- -v, --version
  - Show current version and exit.
- -a, --audio
  - Download audio only (skip video selection).
- -f, --footage
  - Download video only (skip audio-only flows).

Icons used in this README
- Download
- Audio
- Video
- Folder

Examples
```bash
# Download a video (interactive selection if needed)
gold-dl "https://www.youtube.com/watch?v=VIDEO_ID"

# Download audio only
gold-dl "https://www.youtube.com/watch?v=VIDEO_ID" --audio

# Download to a specific folder
gold-dl "https://www.youtube.com/watch?v=VIDEO_ID" ./downloads

# Download a playlist (you can select items or download all)
gold-dl "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Python API (async)
Use the async DownloadService to integrate gold-dl into bots and other apps.

```python
from gold_dl import DownloadService
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
        download_thumbnail=None, 
        export_metadata=None
    )
    return await service.download_async()

# Example runner:
# asyncio.run(download("botname", "https://www.youtube.com/watch?v=VIDEO_ID", video=True))
```

Screenshots
- Download video and choose save location
- Choose download type (audio / video)
- Select resolution when downloading video
- Playlist selection UI (pick single video(s) or download all)

Todo
- [x] Notification System
- [x] Auto Update package if new version available
- [x] Support Optional Numbering for Downloaded Playlist Videos
- [x] Improve code health
- [x] API (Python)
- [x] Download Playlist
- [x] Support setting for default download folder
- [x] Download thumbnails with videos and audio

Contributing
- Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
- Ensure code follows the existing style and add tests where applicable.
- Update the README and other documentation as necessary.

License
- See the LICENSE file in the project root (and the PyPI license badge above).

