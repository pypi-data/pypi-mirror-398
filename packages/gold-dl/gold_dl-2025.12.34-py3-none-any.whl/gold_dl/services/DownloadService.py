from gold_dl.handlers.PlaylistHandler import PlaylistHandler
import os
import sys
import json
import asyncio
from typing import Optional

from pytubefix import YouTube
from pytubefix.helpers import safe_filename

from gold_dl.utils import asking_video_or_audio, console, error_console
from gold_dl.services.AudioService import AudioService
from gold_dl.services.VideoService import VideoService
from gold_dl.services.FileService import FileService
















# =========================
DEFAULT_OUTTMPL = "downloads/%(id)s.%(ext)s"
DEFAULT_THUMBNAIL_TMPL = "downloads/%(id)s.jpg"
DEFAULT_METADATA_TMPL = "downloads/%(id)s.json"

VALID_KEYS = {"id", "ext"}



class DownloadService:
    def __init__(
        self,
        url: str,
        path: Optional[str] = None,
        quality: str = "360p",
        is_audio: bool = False,
        make_playlist_in_order: bool = False,

        # ✅ اختيارات ذكية (يمكن عدم تمريرها نهائيًا)
        download_thumbnail: Optional[bool] = None,
        thumbnail_only: Optional[bool] = None,
        export_metadata: Optional[bool] = None,

        thumbnail_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ):
        self.url = url
        self.quality = quality
        self.is_audio = is_audio
        self.make_playlist_in_order = make_playlist_in_order

        # 🧠 Smart Defaults
        self.thumbnail_only = bool(thumbnail_only)
        self.download_thumbnail_enabled = bool(download_thumbnail)
        self.export_metadata = bool(export_metadata)

        # لو thumbnail_only = True → نعطّل أي تحميل آخر
        if self.thumbnail_only:
            self.download_thumbnail_enabled = True

        self.path = path or DEFAULT_OUTTMPL
        self.thumbnail_path = thumbnail_path or DEFAULT_THUMBNAIL_TMPL
        self.metadata_path = metadata_path or DEFAULT_METADATA_TMPL

        self.video_service = VideoService(self.url, self.quality, "")
        self.audio_service = AudioService(url)
        self.file_service = FileService()

    # =========================
    # Helpers
    # =========================
    def _validate_outtmpl(self, path: str) -> bool:
        import re
        found = set(re.findall(r"%\((.*?)\)s", path))
        return found.issubset(VALID_KEYS)

    def _build_output_path(self, video_id: str, stream) -> tuple[str, str]:
        try:
            ext = "m4a" if stream.type == "audio" else (stream.subtype or "mp4")
        except Exception:
            ext = "m4a" if self.is_audio else "mp4"

        if not self._validate_outtmpl(self.path):
            self.path = DEFAULT_OUTTMPL

        output = self.path % {"id": video_id, "ext": ext}
        directory = os.path.dirname(output) or "."
        filename = os.path.basename(output)
        os.makedirs(directory, exist_ok=True)
        return directory, filename

    def _build_thumbnail_path(self, video_id: str) -> str:
        if not self._validate_outtmpl(self.thumbnail_path):
            self.thumbnail_path = DEFAULT_THUMBNAIL_TMPL

        path = self.thumbnail_path % {"id": video_id, "ext": "jpg"}
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        return path

    def _build_metadata_path(self, video_id: str) -> str:
        if not self._validate_outtmpl(self.metadata_path):
            self.metadata_path = DEFAULT_METADATA_TMPL

        path = self.metadata_path % {"id": video_id, "ext": "json"}
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        return path

    def _already_downloaded(self, directory: str, filename: str) -> bool:
        return os.path.exists(os.path.join(directory, filename))

    # =========================
    # Metadata
    # =========================
    def export_video_metadata(self, video) -> Optional[str]:
        path = self._build_metadata_path(video.video_id)

        if os.path.exists(path):
            return path

        data = {
            "id": video.video_id,
            "title": video.title,
            "author": video.author,
            "channel_id": video.channel_id,
            "length": video.length,
            "views": video.views,
            "publish_date": str(video.publish_date),
            "description": video.description,
            "url": video.watch_url,
            "thumbnail_url": video.thumbnail_url,
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return path
        except Exception:
            return None

    # =========================
    # Thumbnail
    # =========================
    def download_thumbnail(self, video) -> Optional[str]:
        if not video.thumbnail_url:
            return None

        path = self._build_thumbnail_path(video.video_id)
        if os.path.exists(path):
            return path

        try:
            import requests
            r = requests.get(video.thumbnail_url, timeout=10)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            return path
        except Exception:
            return None

    # =========================
    # Main download
    # =========================
    def download(self) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = (
            self.download_preparing()
        )

        if self.export_metadata:
            self.export_video_metadata(video)

        if self.thumbnail_only:
            return self.download_thumbnail(video)

        if self.download_thumbnail_enabled:
            self.download_thumbnail(video)

        if self.is_audio:
            return self.download_audio(audio_stream, video_id)

        return self.download_video(video_id, video_stream)

    # =========================
    # Audio
    # =========================
    def download_audio(self, audio_stream, video_id: str) -> Optional[str]:
        if not audio_stream:
            return None

        directory, filename = self._build_output_path(video_id, audio_stream)
        final_path = os.path.join(directory, filename)

        if self._already_downloaded(directory, filename):
            return final_path

        self.file_service.save_file(audio_stream, filename, directory)
        return final_path

    # =========================
    # Video
    # =========================
    def download_video(self, video_id: str, video_stream) -> Optional[str]:
        if not video_stream:
            return None

        directory, filename = self._build_output_path(video_id, video_stream)
        final_path = os.path.join(directory, filename)

        if self._already_downloaded(directory, filename):
            return final_path

        self.file_service.save_file(video_stream, filename, directory)
        return final_path

    # =========================
    # Async
    # =========================
    async def download_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.download)

    # =========================
    # Preparing
    # =========================
    def download_preparing(self):
        video = self.video_service.search_process()
        video_id = video.video_id
        video_stream, audio_stream, self.quality = (
            self.video_service.get_selected_stream(video, self.is_audio)
        )
        return video, video_id, video_stream, audio_stream, self.quality
        
        


class DownloadServicee:
    def __init__(
        self,
        url: str,
        path: str,
        quality: str,
        is_audio: bool = False,
        make_playlist_in_order: bool = False,
    ):
        self.url = url
        self.path = path
        self.quality = quality
        self.is_audio = is_audio
        self.make_playlist_in_order = make_playlist_in_order

        self.video_service = VideoService(self.url, self.quality, self.path)
        self.audio_service = AudioService(url)
        self.file_service = FileService()

    # =========================
    # Helpers
    # =========================
    def _filename_from_stream(self, stream, video_id: str) -> str:
        try:
            ext = "m4a" if stream.type == "audio" else (stream.subtype or "mp4")
        except Exception:
            ext = "m4a" if self.is_audio else "mp4"

        return f"{video_id}.{ext}"

    def _already_downloaded(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.path, filename))

    # =========================
    # Main download (sync)
    # =========================
    def download(self, title_number: int = 0) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        if self.is_audio:
            return self.download_audio(video, audio_stream, video_id)

        return self.download_video(video, video_id, video_stream)

    # =========================
    # Audio
    # =========================
    def download_audio(
        self,
        video: YouTube,
        audio_stream,
        video_id: str,
        title_number: int = 0,
    ) -> Optional[str]:

        if not audio_stream:
            return None

        audio_filename = self._filename_from_stream(audio_stream, video_id)
        final_path = os.path.join(self.path, audio_filename)

        if self._already_downloaded(audio_filename):
            console.print("⏭ Audio already exists, skipping", style="warning")
            return final_path

        try:
            console.print("⏳ Downloading audio...", style="info")
            self.file_service.save_file(audio_stream, audio_filename, self.path)
            return final_path

        except Exception as error:
            error_console.print(
                f"❗ Audio download failed:\n{error}"
            )
            raise RuntimeError(f"Audio download failed: {error}")

    # =========================
    # Video (بدون صوت)
    # =========================
    def download_video(
        self,
        video: YouTube,
        video_id: str,
        video_stream,
        title_number: int = 0,
    ) -> Optional[str]:

        if not video_stream:
            return None

        video_filename = self._filename_from_stream(video_stream, video_id)
        final_path = os.path.join(self.path, video_filename)

        if self._already_downloaded(video_filename):
            console.print("⏭ Video already exists, skipping", style="warning")
            return final_path

        try:
            console.print("⏳ Downloading video...", style="info")
            self.file_service.save_file(video_stream, video_filename, self.path)
            console.print("✅ Video download completed", style="success")
            return final_path

        except Exception as error:
            error_console.print(f"❗ Video download failed:\n{error}")
            raise RuntimeError(f"Video download failed: {error}")

    # =========================
    # Direct Stream URL
    # =========================
    def get_stream_url(self) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        stream = audio_stream if self.is_audio else video_stream
        if not stream:
            return None

        return stream.url

    async def get_stream_url_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_stream_url)

    # =========================
    # Async Support (Download)
    # =========================
    def _download_sync_return_path(self) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        if self.is_audio:
            return self.download_audio(video, audio_stream, video_id)

        return self.download_video(video, video_id, video_stream)

    async def download_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._download_sync_return_path)

    # =========================
    # Playlist
    # =========================
    def get_playlist_links(self):
        handler = PlaylistHandler(self.url, self.path)
        new_path, is_audio, videos_selected, make_in_order, playlist_videos = (
            handler.process_playlist()
        )

        self.make_playlist_in_order = make_in_order

        last_quality = None
        for index, video_id in enumerate(videos_selected):
            self.url = f"https://www.youtube.com/watch?v={video_id}"
            self.path = new_path
            self.is_audio = is_audio
            self.video_service = VideoService(self.url, self.quality, self.path)

            if index == 0:
                last_quality = self.download()
            else:
                self.quality = last_quality
                self.download()

    # =========================
    # Preparing
    # =========================
    def download_preparing(self):
        video = self.video_service.search_process()
        console.print(f"Title: {video.title}\n", style="info")

        video_id = video.video_id
        video_stream, audio_stream, self.quality = (
            self.video_service.get_selected_stream(video, self.is_audio)
        )

        return video, video_id, video_stream, audio_stream, self.quality        