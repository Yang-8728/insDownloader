import os
import glob
import subprocess
import time
from datetime import datetime
from datetime import date
from tqdm import tqdm

# 项目目录结构配置 / Project directory structure configuration
DOWNLOADS_DIR = "test_downloads"  # 下载目录 / Downloads directory
LOG_DIR = "test_logs"  # 日志目录 / Log directory
DOWNLOAD_LOG = os.path.join(LOG_DIR, "test_downloaded.log")  # 下载记录日志 / Download record log
MERGED_DIR = "merged_videos"  # 合并视频输出目录 / Merged videos output directory
TEMP_DIR = "temp"  # 临时文件目录 / Temporary files directory
LOG_FILE = os.path.join(LOG_DIR, "merged.log")  # 合并记录日志 / Merge record log

# FFmpeg路径配置，优先使用环境变量，否则使用相对路径
# FFmpeg path configuration, use environment variable first, otherwise use relative path
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe"))

def is_ffmpeg_installed():
    """检查FFmpeg是否已安装
    Check if FFmpeg is installed"""
    return os.path.exists(FFMPEG_PATH)

def prepare_temp_directory():
    """准备临时目录，如果存在则清空，不存在则创建
    Prepare temporary directory, clear if exists, create if not"""
    if os.path.exists(TEMP_DIR):
        for f in glob.glob(os.path.join(TEMP_DIR, "*")):
            os.remove(f)
    else:
        os.makedirs(TEMP_DIR)

def standardize_video(input_path, output_path):
    """使用FFmpeg标准化视频：统一分辨率、帧率和编码
    Standardize video using FFmpeg: unify resolution, framerate and encoding"""
    command = [
        FFMPEG_PATH, "-y",
        "-i", input_path,
        "-vf", "scale=1080:1920,fps=30,format=yuv420p,setsar=1",  # 视频滤镜：缩放、帧率、格式 / Video filters: scale, fps, format
        "-r", "30",  # 输出帧率30fps / Output framerate 30fps
        "-ar", "48000",  # 音频采样率48kHz / Audio sample rate 48kHz
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",  # 视频编码设置 / Video codec settings
        "-c:a", "aac", "-b:a", "128k",  # 音频编码设置 / Audio codec settings
        "-movflags", "+faststart",  # 优化网络播放 / Optimize for web playback
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

def merge_specific_videos(source_dir=None, output_name=None, max_per_batch=15, last_n=None, force_all=False):
    """合并指定目录中的所有视频
    Merge all videos in the specified directory
    
    Args:
        source_dir: 视频源目录，默认使用DOWNLOADS_DIR / Source directory, default is DOWNLOADS_DIR
        output_name: 输出文件名，默认使用时间戳 / Output filename, default is timestamp
        max_per_batch: 每批最多处理的视频数量 / Maximum videos per batch
        last_n: 只处理最后N个视频（按修改时间排序）/ Only process last N videos (sorted by modification time)
        force_all: 强制处理所有视频，即使已经合并过 / Force process all videos, even if already merged
    
    Returns:
        (output_path, count): 输出文件路径和合并的视频数量 / Output file path and count of merged videos
    """
    if not is_ffmpeg_installed():
        print("❌ 未找到FFmpeg")
        return None, 0

    # 使用默认值或指定值
    source_dir = source_dir or DOWNLOADS_DIR
    
    # 检查源目录
    if not os.path.exists(source_dir):
        print(f"❌ 源目录不存在: {source_dir}")
        return None, 0
        
    if not os.listdir(source_dir):
        print(f"❌ 源目录为空: {source_dir}")
        return None, 0
    
    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    prepare_temp_directory()
    
    # 可以在这里添加日志跟踪逻辑
    # 如果force_all为True，则不检查已合并记录
    merged_videos = set()
    if not force_all and os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            merged_videos = set(line.strip() for line in f)
    
    # 获取所有视频文件
    video_files = []
    if os.path.exists(source_dir):
        # 搜索视频文件
        mp4_files = glob.glob(os.path.join(source_dir, "*.mp4"))
        if mp4_files:
            for f in mp4_files:
                file_name = os.path.basename(f)
                if force_all or file_name not in merged_videos:
                    video_files.append(file_name)
        else:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        rel_path = os.path.relpath(os.path.join(root, file), source_dir)
                        if force_all or rel_path not in merged_videos:
                            video_files.append(rel_path)
    
    # 按照修改时间排序
    all_videos_with_time = []
    for video in video_files:
        full_path = os.path.join(source_dir, video)
        mtime = os.path.getmtime(full_path)
        all_videos_with_time.append((video, mtime))
    
    all_videos_with_time.sort(key=lambda x: x[1])
    all_videos = [video for video, _ in all_videos_with_time]
    
    # 处理last_n参数
    if last_n and isinstance(last_n, int) and last_n > 0:
        if last_n < len(all_videos):
            print(f"根据参数只处理最新的{last_n}个视频（共有{len(all_videos)}个）")
            all_videos = all_videos[-last_n:]  # 取最后N个（最新的）
        else:
            print(f"要求处理最后{last_n}个视频，但只有{len(all_videos)}个视频可用，将处理所有视频")
    
    merge_count = len(all_videos)
    
    if merge_count == 0:
        print(f"没有找到符合条件的视频文件")
        return None, 0

    # 标准化视频
    temp_video_paths = []
    for video in tqdm(all_videos, desc="正在标准化视频"):
        original_path = os.path.join(source_dir, video)
        temp_path = os.path.join(TEMP_DIR, f"temp_{video}")
        success = standardize_video(original_path, temp_path)
        if success:
            temp_video_paths.append(temp_path)
        else:
            print(f"❌ 标准化视频失败: {video}")
            return None, 0
    
    # 使用concat demuxer方法替代filter_complex方法
    # 创建合并列表文件
    list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for video_path in temp_video_paths:
            # 使用绝对路径并正确转义
            abs_path = os.path.abspath(video_path).replace('\\', '\\\\')
            f.write(f"file '{abs_path}'\n")
    
    # 设置输出文件名
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_name = output_name or timestamp
    final_output_path = os.path.join(MERGED_DIR, f"{output_name}.mp4")
    
    # 使用concat demuxer执行合并
    command = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file, 
        "-c", "copy",  # 直接复制流，不重新编码
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
        print("尝试使用备用方法合并...")
        
        # 如果concat demuxer方法失败，则尝试使用中间文件方法
        final_success = merge_in_smaller_batches(temp_video_paths, final_output_path, 5)
        if not final_success:
            print("所有合并方法都失败了")
            return None, 0
    
    return os.path.abspath(final_output_path), merge_count

def merge_in_smaller_batches(video_paths, output_path, batch_size=5):
    """分批合并视频，适用于大量视频
    Merge videos in smaller batches, suitable for large number of videos"""
    if len(video_paths) <= batch_size:
        # 使用concat demuxer直接合并
        return merge_with_concat_demuxer(video_paths, output_path)
    
    # 分批处理
    batch_outputs = []
    for i in range(0, len(video_paths), batch_size):
        batch = video_paths[i:i+batch_size]
        batch_output = os.path.join(TEMP_DIR, f"batch_{i//batch_size}.mp4")
        print(f"合并批次 {i//batch_size + 1}/{(len(video_paths) + batch_size - 1)//batch_size}...")
        
        if merge_with_concat_demuxer(batch, batch_output):
            batch_outputs.append(batch_output)
        else:
            print(f"批次 {i//batch_size + 1} 合并失败")
            return False
    
    # 合并所有批次
    return merge_with_concat_demuxer(batch_outputs, output_path)

def merge_with_concat_demuxer(video_paths, output_path):
    """使用concat demuxer合并视频
    Merge videos using concat demuxer"""
    # 创建合并列表文件
    list_file = os.path.join(TEMP_DIR, f"list_{os.path.basename(output_path)}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for video_path in video_paths:
            # 使用绝对路径并正确转义
            abs_path = os.path.abspath(video_path).replace('\\', '\\\\')
            f.write(f"file '{abs_path}'\n")
    
    # 使用concat demuxer执行合并
    command = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",  # 直接复制流，不重新编码
        output_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def format_duration(seconds):
    """将秒数格式化为易读的时间格式
    Format seconds into a readable time format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}分{secs}秒"  # X minutes Y seconds
    else:
        return f"{secs}秒"  # X seconds

# 添加命令行参数处理
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="合并视频工具 / Video Merge Tool")
    parser.add_argument("--dir", "-d", help="指定视频源目录 / Specify source directory", default=None)
    parser.add_argument("--output", "-o", help="指定输出文件名 / Specify output filename", default=None)
    parser.add_argument("--batch", "-b", type=int, help="每批最大视频数 / Maximum videos per batch", default=15)
    parser.add_argument("--last", "-l", type=int, help="只合并最后N个视频 / Only merge last N videos", default=None)
    parser.add_argument("--force", "-f", action="store_true", help="强制处理所有视频，不跳过已合并的 / Force process all videos, don't skip merged ones")
    args = parser.parse_args()
    
    start_time = time.time()
    
    if args.dir:
        # 合并指定目录的视频
        path, count = merge_specific_videos(args.dir, args.output, args.batch, args.last, args.force)
    else:
        # 使用默认函数合并已下载视频，并传递last_n参数
        path, count = merge_specific_videos(DOWNLOADS_DIR, output_name=args.output, max_per_batch=args.batch, last_n=args.last, force_all=args.force)
    
    if path:
        print(f"✅ 合并完成，生成文件：{path}，合并数量：{count} 个")
    else:
        print("❌ 合并失败")
    print(f"总用时: {format_duration(time.time() - start_time)}")
