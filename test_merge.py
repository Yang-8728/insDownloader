import os
import glob
import subprocess
from datetime import datetime
from datetime import date
from tqdm import tqdm

# 修改为与项目一致的目录结构
DOWNLOADS_DIR = "test_downloads"
LOG_DIR = "test_logs"
DOWNLOAD_LOG = os.path.join(LOG_DIR, "test_downloaded.log")
MERGED_DIR = "merged_videos"
TEMP_DIR = "temp"
LOG_FILE = os.path.join(LOG_DIR, "merged.log")

# 使FFmpeg路径可配置
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe"))

def is_ffmpeg_installed():
    """Check if FFmpeg is installed
    检查FFmpeg是否已安装"""
    return os.path.exists(FFMPEG_PATH)

def prepare_temp_directory():
    """Prepare temporary directory
    准备临时目录"""
    if os.path.exists(TEMP_DIR):
        for f in glob.glob(os.path.join(TEMP_DIR, "*")):
            os.remove(f)
    else:
        os.makedirs(TEMP_DIR)

def standardize_video(input_path, output_path):
    """Standardize video using FFmpeg
    使用FFmpeg标准化视频"""
    command = [
        FFMPEG_PATH, "-y",
        "-i", input_path,
        "-vf", "scale=1080:1920,fps=30,format=yuv420p,setsar=1",
        "-r", "30",
        "-ar", "48000",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def merge_all_downloaded_videos():
    """Merge all downloaded videos into one
    将所有下载的视频合并为一个"""
    if not is_ffmpeg_installed():
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        print("❌ 未找到FFmpeg。请先安装FFmpeg。")
        return None, 0

    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    prepare_temp_directory()

    # 加载已合并的视频记录
    merged_videos = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            merged_videos = set(line.strip() for line in f)

    # 获取视频文件
    video_files = []
    
    # 获取下载目录中的视频文件
    if os.path.exists(DOWNLOADS_DIR):
        for file in os.listdir(DOWNLOADS_DIR):
            if file.endswith('.mp4') and file not in merged_videos:
                video_files.append(file)
    
    # 如果没有直接找到视频文件，则检查日志文件中的shortcode
    if not video_files and os.path.exists(DOWNLOAD_LOG):
        shortcodes = set()
        with open(DOWNLOAD_LOG, "r", encoding="utf-8") as f:
            shortcodes = set(line.strip() for line in f if line.strip())
        
        # 查找下载目录中与shortcode相关的视频
        for file in os.listdir(DOWNLOADS_DIR):
            if file.endswith('.mp4') and file not in merged_videos:
                for shortcode in shortcodes:
                    if shortcode in file:
                        video_files.append(file)
                        break

    all_videos = sorted(video_files)
    merge_count = len(all_videos)
    
    if merge_count == 0:
        print("📭 No new videos to merge.")
        print("📭 没有新视频需要合并。")
        return None, 0

    # 标准化视频
    temp_video_paths = []
    for video in tqdm(all_videos, desc="正在标准化视频"):
        original_path = os.path.join(DOWNLOADS_DIR, video)
        temp_path = os.path.join(TEMP_DIR, f"temp_{video}")
        success = standardize_video(original_path, temp_path)
        if success:
            temp_video_paths.append(temp_path)
        else:
            print(f"❌ Failed to standardize video: {video}")
            print(f"❌ 标准化视频失败: {video}")
            return None, 0

    inputs = []
    filter_parts = []

    for idx, temp_path in enumerate(temp_video_paths):
        inputs += ["-i", temp_path]
        filter_parts.append(f"[{idx}:v:0][{idx}:a:0]")

    filter_complex = "".join(filter_parts) + f"concat=n={merge_count}:v=1:a=1[outv][outa]"

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    final_output_path = os.path.join(MERGED_DIR, f"{timestamp}.mp4")

    command = [
        FFMPEG_PATH, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        final_output_path
    ]

    print(f"正在合并视频: {final_output_path}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"视频已保存: {final_output_path}")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            for video in all_videos:
                f.write(video + "\n")
        print(f"成功合并: {merge_count} 个视频")
    else:
        print(f"合并失败: {result.stderr}")
        return None, 0

    return os.path.abspath(final_output_path), merge_count

if __name__ == "__main__":
    path, count = merge_all_downloaded_videos()
    print(f"✅ Merge completed, generated file: {path}, merged count: {count} videos")
    print(f"✅ 合并完成，生成文件：{path}，合并数量：{count} 个")
