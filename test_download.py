from datetime import datetime
import os
import sys
import time
from contextlib import contextmanager
from instaloader import Instaloader, Profile, Post, LoginRequiredException
from test_login import get_session_file_path, ensure_logged_in_user
from tqdm import tqdm

download_dir = "test_downloads"
LOG_DIR = "test_logs"
LOG_FILE = os.path.join(LOG_DIR, "test_downloaded.log")


@contextmanager
def suppress_stdout_stderr():
    """
    A context manager that redirects stdout and stderr to devnull
    Used to suppress noisy output from instaloader
    """
    original_stdout, original_stderr = sys.stdout, sys.stderr
    stdout_null = open(os.devnull, "w")
    stderr_null = open(os.devnull, "w")

    try:
        sys.stdout, sys.stderr = stdout_null, stderr_null
        yield
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
        stdout_null.close()
        stderr_null.close()


def is_video_post(post: Post) -> bool:
    return post.typename == "GraphVideo"


def load_downloaded_shortcodes(log_file: str) -> set:
    if not os.path.exists(log_file):
        return set()
    with open(log_file, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_new_shortcodes(shortcodes: list, log_file: str):
    with open(log_file, "a", encoding="utf-8") as f:
        for code in shortcodes:
            f.write(code + "\n")


def clean_non_video_files(download_dir: str):
    for filename in os.listdir(download_dir):
        if not filename.endswith(".mp4"):
            os.remove(os.path.join(download_dir, filename))


def format_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}分{sec}秒"
    else:
        return f"{sec}秒"


def download_saved_videos(username: str) -> int:
    start_time = time.time()

    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)
    L = Instaloader()
    session_path = get_session_file_path(username)

    # Add session file existence check
    if not os.path.exists(session_path):
        print(f"❌ 会话文件不存在: {session_path}")
        print(f"❌ 请先运行登录程序创建会话")
        return 0

    try:
        L.load_session_from_file(username, filename=session_path)

        # Verify the session is still valid
        if not L.test_login():
            print("❌ 会话已过期，请重新登录")
            return 0

        profile = Profile.from_username(L.context, username)
        all_posts = list(profile.get_saved_posts())
        downloaded_codes = load_downloaded_shortcodes(LOG_FILE)

        # 只保留未下载的视频
        video_posts = [p for p in all_posts if is_video_post(p) and p.shortcode not in downloaded_codes]

        count_downloaded = 0
        skipped_count = len(all_posts) - len(video_posts)
        newly_downloaded = []

        progress_bar = tqdm(video_posts, desc="📦 正在下载", unit="视频", position=0, leave=True)

        for post in progress_bar:
            with suppress_stdout_stderr():
                L.download_post(post, target=download_dir)

            clean_non_video_files(download_dir)
            newly_downloaded.append(post.shortcode)
            count_downloaded += 1

        progress_bar.close()

        if newly_downloaded:
            save_new_shortcodes(newly_downloaded, LOG_FILE)

        duration = format_duration(time.time() - start_time)

        print(f"\n✅ 下载完成：{count_downloaded} 个")
        if skipped_count > 0:
            print(f"⏭️ 跳过了 {skipped_count} 个已下载视频")
        print(f"🕒 总耗时：{duration}")

        return count_downloaded

    except LoginRequiredException:
        print("❌ 登录已失效，请重新运行登录程序")
        return 0
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        return 0


if __name__ == "__main__":
    username = ensure_logged_in_user()
    download_saved_videos(username)

# Import unittest modules only if needed for testing
# import unittest
# from unittest.mock import patch, MagicMock, mock_open