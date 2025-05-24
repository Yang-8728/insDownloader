from datetime import datetime
import os
import sys
import time
import random
import json
from contextlib import contextmanager
from instaloader import Instaloader, Profile, Post, LoginRequiredException
from test_login import get_session_file_path, ensure_logged_in_user
from tqdm import tqdm

download_dir = "test_downloads"
LOG_DIR = "test_logs"
LOG_FILE = os.path.join(LOG_DIR, "test_downloaded.log")

# 修改重试配置，减少等待时间
MAX_RETRIES = 3  # 减少最大重试次数，避免用户等待太久
RETRY_DELAY_INITIAL = 15  # 减少初始重试延迟（秒）
RETRY_DELAY_FACTOR = 1.5  # 重试延迟递增因子
RATE_LIMIT_DELAY = 30  # 遇到速率限制时的初始等待时间


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
    
    # 尝试恢复会话
    retry_count = 0
    L = None
    session_path = get_session_file_path(username)

    # Add session file existence check
    if not os.path.exists(session_path):
        print(f"❌ 会话文件不存在: {session_path}")
        print(f"❌ 请先运行登录程序创建会话")
        return 0

    print("\n🔄 正在连接Instagram...(按Ctrl+C可随时取消)")
    
    while retry_count < MAX_RETRIES:
        try:
            print(f"尝试加载Instagram会话... (尝试 {retry_count + 1}/{MAX_RETRIES})")
            L = Instaloader(
                sleep=True,                 # 启用请求间延迟
                quiet=True,                 # 不显示额外信息
                download_comments=False,    # 不下载评论
                download_geotags=False,     # 不下载地理标签
                compress_json=False,        # 不压缩JSON
                download_video_thumbnails=False,  # 不下载视频缩略图
                request_timeout=60,         # 请求超时设置为60秒
                max_connection_attempts=3   # 限制连接尝试次数
            )
            
            L.load_session_from_file(username, filename=session_path)
            
            # 添加随机延迟，避免被限制，但减少等待时间
            delay = random.uniform(1, 3)  # 减少等待时间
            print(f"准备验证登录状态，等待 {delay:.1f} 秒...")
            time.sleep(delay)
            
            # 检查登录状态
            try:
                # 添加明确的提示
                print("正在验证Instagram登录状态...")
                if L.test_login():
                    print(f"✅ 成功登录为: {username}")
                    break
                else:
                    print("❌ 登录测试失败，等待后重试...")
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户取消操作")
                return 0
            except Exception as e:
                if "401 Unauthorized" in str(e) and "Please wait a few minutes" in str(e):
                    wait_time = RETRY_DELAY_INITIAL * (RETRY_DELAY_FACTOR ** retry_count)
                    print(f"\n⚠️ Instagram要求等待! 将等待 {wait_time:.0f} 秒后重试...")
                    print("(您可以按Ctrl+C取消操作)")
                    try:
                        # 使用分段等待，让用户可以更容易取消
                        step = 5
                        for i in range(0, int(wait_time), step):
                            time.sleep(step)
                            remaining = wait_time - i - step
                            if remaining > 0:
                                print(f"⏳ 还需等待 {remaining:.0f} 秒...")
                    except KeyboardInterrupt:
                        print("\n\n⚠️ 用户取消等待")
                        return 0
                    retry_count += 1
                    continue
                else:
                    raise
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户取消操作")
            return 0
        except LoginRequiredException:
            print("❌ 会话已过期，需要重新登录")
            print("提示：请运行 test_login.py 重新登录")
            return 0
        except Exception as e:
            print(f"❌ 加载会话时出错: {str(e)}")
            wait_time = RETRY_DELAY_INITIAL * (RETRY_DELAY_FACTOR ** retry_count)
            print(f"等待 {wait_time:.0f} 秒后重试...")
            try:
                time.sleep(wait_time)
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户取消等待")
                return 0
            retry_count += 1
            
            if retry_count >= MAX_RETRIES:
                print(f"❌ 已达到最大重试次数 ({MAX_RETRIES})，放弃尝试")
                print("建议：稍后再试或运行 test_login.py 重新登录")
                return 0
    
    # 如果所有重试都失败
    if L is None or retry_count >= MAX_RETRIES:
        print("❌ 无法连接到Instagram，请稍后再试")
        print("建议：Instagram可能暂时限制了您的访问，请等待几小时后再尝试")
        return 0
        
    try:
        print("\n🔍 正在获取已保存的帖子...")
        
        # 添加获取个人资料的重试逻辑
        profile = None
        retry_count = 0
        
        while retry_count < MAX_RETRIES and profile is None:
            try:
                # 添加较短的随机延迟
                delay = random.uniform(1, 3)
                print(f"请求前等待 {delay:.1f} 秒...")
                time.sleep(delay)
                
                profile = Profile.from_username(L.context, username)
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户取消操作")
                return 0
            except Exception as e:
                if "401 Unauthorized" in str(e) and "Please wait a few minutes" in str(e):
                    wait_time = RATE_LIMIT_DELAY * (RETRY_DELAY_FACTOR ** retry_count)
                    print(f"\n⚠️ 请求被限制! 将等待 {wait_time:.0f} 秒后重试...")
                    print("(您可以按Ctrl+C取消操作)")
                    try:
                        for i in range(0, int(wait_time), 5):
                            time.sleep(5)
                            remaining = wait_time - i - 5
                            if remaining > 0:
                                print(f"⏳ 还需等待 {remaining:.0f} 秒...")
                    except KeyboardInterrupt:
                        print("\n\n⚠️ 用户取消等待")
                        return 0
                    retry_count += 1
                else:
                    print(f"❌ 获取个人资料时出错: {str(e)}")
                    raise
                    
        if profile is None:
            print("❌ 无法获取个人资料，请稍后再试")
            return 0
            
        # 以分批方式获取已保存的帖子，避免一次性请求过多
        print("正在分批获取已保存的帖子...")
        all_posts = []
        
        # 创建一个生成器
        saved_posts_generator = profile.get_saved_posts()
        batch_size = 10  # 每批获取的帖子数量
        
        # 统计总数并分批处理
        try:
            while True:
                batch = []
                for _ in range(batch_size):
                    try:
                        post = next(saved_posts_generator)
                        batch.append(post)
                    except StopIteration:
                        break
                    except KeyboardInterrupt:
                        print("\n\n⚠️ 用户取消操作")
                        return 0
                
                if not batch:
                    break
                    
                all_posts.extend(batch)
                print(f"已获取 {len(all_posts)} 个保存的帖子...")
                
                # 添加较短的随机延迟，避免被限制
                if len(all_posts) % (batch_size * 2) == 0:
                    delay = random.uniform(2, 5)  # 减少等待时间
                    print(f"休息一下，等待 {delay:.1f} 秒...")
                    try:
                        time.sleep(delay)
                    except KeyboardInterrupt:
                        print("\n\n⚠️ 用户取消操作")
                        return 0
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户取消操作")
            return len(all_posts) > 0
        except Exception as e:
            print(f"⚠️ 获取帖子时遇到错误: {str(e)}")
            print(f"将使用已获取的 {len(all_posts)} 个帖子继续处理")
            
        if not all_posts:
            print("❌ 没有找到任何已保存的帖子")
            return 0
            
        print(f"共获取 {len(all_posts)} 个已保存的帖子")
        downloaded_codes = load_downloaded_shortcodes(LOG_FILE)

        # 只保留未下载的视频
        video_posts = [p for p in all_posts if is_video_post(p) and p.shortcode not in downloaded_codes]

        count_downloaded = 0
        skipped_count = len(all_posts) - len(video_posts)
        newly_downloaded = []

        if not video_posts:
            print("没有新的视频需要下载")
            return 0
            
        print(f"\n📥 发现 {len(video_posts)} 个新视频需要下载")
            
        progress_bar = tqdm(video_posts, desc="正在下载视频", unit="个")

        for post in progress_bar:
            retry_count = 0
            while retry_count < MAX_RETRIES:
                try:
                    # 添加较短的下载前随机延迟
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                    
                    with suppress_stdout_stderr():
                        L.download_post(post, target=download_dir)

                    # 清理非视频文件
                    clean_non_video_files(download_dir)
                    newly_downloaded.append(post.shortcode)
                    count_downloaded += 1
                    break
                except KeyboardInterrupt:
                    print("\n\n⚠️ 用户取消下载")
                    # 保存已下载的内容
                    if newly_downloaded:
                        save_new_shortcodes(newly_downloaded, LOG_FILE)
                    return count_downloaded
                except Exception as e:
                    if "401 Unauthorized" in str(e) and "Please wait a few minutes" in str(e):
                        retry_count += 1
                        wait_time = min(RATE_LIMIT_DELAY * (RETRY_DELAY_FACTOR ** retry_count), 120)  # 限制最大等待时间
                        progress_bar.set_description(f"⚠️ 请求被限制! 等待 {wait_time:.0f} 秒")
                        try:
                            time.sleep(wait_time)
                        except KeyboardInterrupt:
                            print("\n\n⚠️ 用户取消等待")
                            if newly_downloaded:
                                save_new_shortcodes(newly_downloaded, LOG_FILE)
                            return count_downloaded
                        progress_bar.set_description("正在下载视频")
                    else:
                        progress_bar.set_description(f"下载出错: {str(e)[:30]}...")
                        retry_count += 1
                        time.sleep(3)  # 减少等待时间
                        
                    if retry_count >= MAX_RETRIES:
                        progress_bar.write(f"❌ 无法下载视频 {post.shortcode}: 已达到最大重试次数")
                        break

        progress_bar.close()

        if newly_downloaded:
            save_new_shortcodes(newly_downloaded, LOG_FILE)

        duration = format_duration(time.time() - start_time)

        print(f"\n✅ 下载完成: {count_downloaded} 个视频")
        if skipped_count > 0:
            print(f"已跳过: {skipped_count} 个已下载或非视频的帖子")
        print(f"总耗时: {duration}")

        return count_downloaded

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消操作")
        return 0
    except LoginRequiredException:
        print("❌ 登录已失效，请重新运行登录程序")
        return 0
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def download_new_videos():
    """下载新视频的入口函数
    Entry function for downloading new videos

    Returns:
        int: 下载的视频数量 / Number of downloaded videos
    """
    try:
        username = ensure_logged_in_user()
        if not username:
            print("未找到登录用户，请先运行登录程序")
            return 0
        
        print(f"开始为用户 {username} 下载新视频...")
        return download_saved_videos(username)
    except Exception as e:
        print(f"下载过程中出错: {e}")
        return 0


# 兼容性别名 - 用于支持老的导入语句
download_instagram_videos = download_new_videos

if __name__ == "__main__":
    username = ensure_logged_in_user()
    download_saved_videos(username)

# Import unittest modules only if needed for testing
# import unittest
# from unittest.mock import patch, MagicMock, mock_open