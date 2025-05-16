import os
import glob
import subprocess
import time  # 添加time模块导入
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

def merge_specific_videos(source_dir=None, output_name=None, max_per_batch=15, last_n=None):
    """合并指定目录中的所有视频
    
    Args:
        source_dir: 视频源目录，默认使用DOWNLOADS_DIR
        output_name: 输出文件名，默认使用时间戳
        max_per_batch: 每批最多处理的视频数量（减小默认值以提高稳定性）
        last_n: 只处理最后N个视频（按修改时间排序）
    
    Returns:
        (output_path, count): 输出文件路径和合并的视频数量
    """
    if not is_ffmpeg_installed():
        print("❌ 未找到FFmpeg。请先安装FFmpeg。")
        return None, 0

    # 使用默认值或指定值
    source_dir = source_dir or DOWNLOADS_DIR
    
    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"❌ 源目录不存在: {source_dir}")
        print("提示: 请确保目录路径正确。如果是相对路径，它将相对于当前工作目录解析。")
        print(f"当前工作目录: {os.getcwd()}")
        return None, 0
        
    # 检查源目录是否为空
    if not os.listdir(source_dir):
        print(f"❌ 源目录为空: {source_dir}")
        print("提示: 请确保目录中包含MP4视频文件。")
        return None, 0
    
    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    prepare_temp_directory()
    
    # 获取所有视频文件（扩展搜索能力）
    video_files = []
    if os.path.exists(source_dir):
        print(f"正在扫描目录: {source_dir}")
        
        # 首先尝试直接搜索.mp4文件
        mp4_files = glob.glob(os.path.join(source_dir, "*.mp4"))
        if mp4_files:
            video_files = [os.path.basename(f) for f in mp4_files]
        else:
            # 如果没有找到.mp4文件，尝试搜索有"temp_"前缀的文件（之前处理过的临时文件）
            temp_files = glob.glob(os.path.join(source_dir, "temp_*.mp4"))
            if temp_files:
                video_files = [os.path.basename(f) for f in temp_files]
            else:
                # 如果仍未找到，尝试递归搜索子目录
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        if file.endswith('.mp4'):
                            # 使用相对路径保存，以便在原始目录中处理
                            rel_path = os.path.relpath(os.path.join(root, file), source_dir)
                            video_files.append(rel_path)
    
    all_videos = sorted(video_files)
    merge_count = len(all_videos)
    
    if merge_count == 0:
        print(f"在 {source_dir} 中没有找到视频文件。请确认路径是否正确以及文件是否为.mp4格式。")
        return None, 0
    
    print(f"找到 {merge_count} 个视频文件:")
    for i, video in enumerate(all_videos[:10]):  # 只显示前10个
        print(f"  {i+1}. {video}")
    if merge_count > 10:
        print(f"  ...以及其他 {merge_count-10} 个文件")
    
    # 始终使用批处理流程，无论视频数量
    batch_count = (merge_count + max_per_batch - 1) // max_per_batch  # 向上取整
    temp_merged_files = []
    
    print(f"将分{batch_count}批处理视频，每批最多{max_per_batch}个")
    
    for batch_idx in range(batch_count):
        start_idx = batch_idx * max_per_batch
        end_idx = min(start_idx + max_per_batch, merge_count)
        batch_videos = all_videos[start_idx:end_idx]
        
        print(f"处理批次 {batch_idx+1}/{batch_count}，包含{len(batch_videos)}个视频...")
        
        # 处理这批视频
        batch_temp_paths = []
        for video in tqdm(batch_videos, desc=f"批次{batch_idx+1}标准化视频"):
            original_path = os.path.join(source_dir, video)
            temp_path = os.path.join(TEMP_DIR, f"temp_batch{batch_idx}_{os.path.basename(video)}")
            success = standardize_video(original_path, temp_path)
            if success:
                batch_temp_paths.append(temp_path)
            else:
                print(f"标准化视频失败: {video}")
                return None, 0
        
        # 合并这批视频
        batch_output = os.path.join(TEMP_DIR, f"batch_{batch_idx}.mp4")
        success = merge_video_batch(batch_temp_paths, batch_output)
        if not success:
            print(f"批次{batch_idx+1}合并失败")
            return None, 0
            
        temp_merged_files.append(batch_output)
        print(f"批次{batch_idx+1}合并完成")
    
    # 如果只有一个批次，直接使用它
    if len(temp_merged_files) == 1:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = output_name or timestamp
        final_output_path = os.path.join(MERGED_DIR, f"{output_name}.mp4")
        
        # 直接复制文件而不是再次合并
        import shutil
        shutil.copy2(temp_merged_files[0], final_output_path)
        print(f"只有一个批次，直接复制为最终输出: {final_output_path}")
        
        success = True
    else:
        # 最后合并所有批次
        print(f"合并所有{len(temp_merged_files)}个批次...")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = output_name or timestamp
        final_output_path = os.path.join(MERGED_DIR, f"{output_name}.mp4")
        success = merge_video_batch(temp_merged_files, final_output_path)
    
    if success:
        print(f"视频已保存: {final_output_path}")
        print(f"成功合并: {merge_count} 个视频")
    else:
        print("合并失败")
        return None, 0
        
    return os.path.abspath(final_output_path), merge_count

def merge_video_batch(video_paths, output_path):
    """合并一批视频文件"""
    inputs = []
    filter_parts = []

    for idx, path in enumerate(video_paths):
        inputs += ["-i", path]
        filter_parts.append(f"[{idx}:v:0][{idx}:a:0]")

    filter_complex = "".join(filter_parts) + f"concat=n={len(video_paths)}:v=1:a=1[outv][outa]"

    command = [
        FFMPEG_PATH, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"运行FFmpeg命令合并视频...")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        return True
    else:
        print(f"合并失败: {result.stderr}")
        return False

def format_duration(seconds):
    """将秒数格式化为易读的时间格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

if __name__ == "__main__":
    # 添加命令行参数处理
    import argparse
    
    parser = argparse.ArgumentParser(description="合并视频工具")
    parser.add_argument("--dir", "-d", help="指定视频源目录", default=None)
    parser.add_argument("--output", "-o", help="指定输出文件名", default=None)
    parser.add_argument("--batch", "-b", type=int, help="每批最大视频数", default=15)
    parser.add_argument("--last", "-l", type=int, help="只合并最后N个视频", default=None)
    args = parser.parse_args()
    
    start_time = time.time()
    
    if args.dir:
        # 合并指定目录的视频
        path, count = merge_specific_videos(args.dir, args.output, args.batch, args.last)
    else:
        # 使用默认函数合并已下载视频
        path, count = merge_specific_videos(DOWNLOADS_DIR, last_n=args.last)
    
    if path:
        print(f"✅ 合并完成，生成文件：{path}，合并数量：{count} 个")
    else:
        print("❌ 合并失败")
    print(f"总用时: {format_duration(time.time() - start_time)}")
