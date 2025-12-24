import os
import re
import sys
import threading

from pytubefix.helpers import safe_filename
from pytubefix import Playlist

from gold_dl.utils import (
    console,
    asking_video_or_audio,
    ask_playlist_video_names,
    ask_for_make_playlist_in_order,
)


class PlaylistHandler:
    playlist_videos = []

    def __init__(self, url: str, path: str):
        self.url: str = url
        self.path: str = path

    def process_playlist(self):
        console.print("Processing playlist...")

        try:
            is_audio = asking_video_or_audio()
        except TypeError:
            console.print("Cancelled")
            return

        console.print("Downloading playlist...")
        playlist = Playlist(self.url)

        p_title = playlist.title
        p_total = playlist.length
        p_videos = playlist.videos

        make_in_order = ask_for_make_playlist_in_order()
        console.print(
            f"{'✅' if make_in_order else '❌'} Make playlist in order",
            style="info",
        )
        console.print()
        console.print("Fetching playlist videos...", style="info")

        self.get_all_playlist_videos_title(p_videos)

        for index, video_and_id in enumerate(self.playlist_videos):
            if make_in_order:
                new_video_title = f"{index + 1}__{video_and_id[0]}"
            else:
                new_video_title = video_and_id[0]
            self.playlist_videos[index] = (new_video_title, video_and_id[1])

        console.print("Checking if the videos are already downloaded...")
        new_path = self.check_for_downloaded_videos(p_title, p_total)

        console.print("Chose what video you want to download", style="info")
        videos_selected = ask_playlist_video_names(self.playlist_videos)

        return new_path, is_audio, videos_selected, make_in_order, self.playlist_videos

    # =========================
    # FIXED THREAD
    # =========================
    def fetch_title_thread(self, video, index, results):
        """
        Fetch playlist video title safely.
        """
        try:
            try:
                title = video.title
                if not title:
                    raise ValueError
                title = safe_filename(title)
            except Exception:
                # 🔥 fallback: استخدم video_id
                title = video.video_id

            video_id = video.video_id
            results[index] = (title, video_id)

        except Exception:
            # 🔥 أي فشل غير متوقع
            results[index] = (video.video_id, video.video_id)

    def get_all_playlist_videos_title(self, videos):
        total_videos = len(videos)
        results = [None] * total_videos
        title_threads = []

        for index, video in enumerate(videos):
            thread = threading.Thread(
                target=self.fetch_title_thread,
                args=(video, index, results),
            )
            thread.start()
            title_threads.append(thread)

        for thread in title_threads:
            thread.join()

        # حذف أي عناصر فاشلة (احتياط)
        self.playlist_videos = [v for v in results if v is not None]

    # =========================
    # UTILS
    # =========================
    @staticmethod
    def show_playlist_info(title, total):
        console.print(f"\nPlaylist title: {title}\n", style="info")
        console.print(f"Total videos: {total}\n", style="info")

    def create_playlist_folder(self, title):
        os.makedirs(title, exist_ok=True)
        return os.path.join(self.path, title)

    def check_for_downloaded_videos(self, title, total):
        new_path = self.create_playlist_folder(safe_filename(title))

        for file in os.listdir(new_path):
            file_name = os.path.splitext(file)[0]
            cleaned_file_name = re.compile(
                r'(_\d{3,4}p|_\d+k|_(hd|uhd|sd))$'
            ).sub('', file_name)

            for video in self.playlist_videos[:]:
                video_name = video[0]
                if video_name.startswith(cleaned_file_name):
                    self.playlist_videos.remove(video)
                    break

        if not self.playlist_videos:
            console.print(
                f"All playlist videos are already downloaded, see '{title}' folder",
                style="info",
            )
            sys.exit()

        self.show_playlist_info(title, total)
        return new_path
