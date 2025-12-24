import os
import sys

from yaspin import yaspin
from yaspin.spinners import Spinners
from pytubefix import YouTube
from pytubefix.cli import on_progress
from termcolor import colored
from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio

from gold_dl.utils import (
    console,
    error_console,
    ask_resolution,
    CANCEL_PREFIX
)








class VideoService:
    def __init__(self, url: str, quality: str, path: str) -> None:
        self.url = url
        self.quality = quality
        self.path = path

    # =========================
    # Search
    # =========================
    def search_process(self) -> YouTube:
        try:
            video = self.__video_search()
        except Exception as error:
            error_console.print(f"❗ Error: {error}")
            sys.exit(1)

        if not video:
            error_console.print("❗ No stream available for the URL.")
            sys.exit(1)

        return video

    @yaspin(
        text=colored("Searching for the video", "green"),
        color="green",
        spinner=Spinners.point,
    )
    def __video_search(self) -> YouTube:
        return YouTube(
            self.url,
            use_oauth=True,
            allow_oauth_cache=True,
            on_progress_callback=on_progress,
        )

    # =========================
    # Streams (FIXED)
    # =========================
    def get_available_resolutions(self, video: YouTube):
        streams = video.streams

        # 🎞 فيديو فقط (itag 18)
        video_stream = streams.get_by_itag(18)
        if not video_stream:
            error_console.print("❗ itag 18 video not found.")
            sys.exit(1)

        # 🔊 صوت فقط
        audio_stream = (
            streams.filter(only_audio=True, mime_type="audio/mp4")
            .order_by("abr")
            .desc()
            .first()
        )

        if not audio_stream:
            error_console.print("❗ No audio stream found.")
            sys.exit(1)

        size_mb = video_stream.filesize / (1024 * 1024)

        return (
            ["360p"],
            [f"{size_mb:.2f} MB"],
            video_stream,   # فيديو فقط
            audio_stream,   # صوت فقط
        )

    def get_video_streams(self, quality: str, stream):
        # itag 18 → stream مباشر
        return stream

    def get_selected_stream(self, video, is_audio: bool = False):
        resolutions, sizes, video_stream, audio_stream = self.get_available_resolutions(video)

        if is_audio:
            return None, audio_stream, self.quality

        return video_stream, audio_stream, "360p"

    # =========================
    # Merging (DISABLED)
    # =========================
    def merging(self, video_path: str, audio_path: str):
        # ❌ لا دمج نهائيًا
        return