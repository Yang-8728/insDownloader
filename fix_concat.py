#!/usr/bin/env python3
"""
修复视频合并中的Stream specifier错误
Fix Stream specifier errors in video concatenation
"""

import os
import subprocess
import glob
import json
from datetime import datetime

# 配置
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe"))
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe"))
TEMP_DIR = "temp"
MERGED_DIR = "merged_videos"

def ensure_dirs():
    """确保目录存在"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(MERGED_DIR, exist_ok=True)

def get_stream_info(video_path):
    """获取视频流信息"""
    cmd = [
        FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            info = json.loads(result.stdout)
            return info
    except Exception as e:
        print(f"获取视频信息出错: {e}")
    
    return None

def merge_with_concat_demuxer(videos, output_path):
    """使用concat demuxer合并视频"""
    # 创建文件列表
    list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for video in videos:
            # 使用绝对路径，确保转义反斜杠
            abs_path = os.path.abspath(video).replace("\\", "\\\\")
            f.write(f"file '{abs_path}'\n")
    
    # 合并视频
    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",  # 直接复制编解码器，不重新编码
        output_path
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"合并成功: {output_path}")
        return True
    else:
        print(f"合并失败: {result.stderr}")
        return False

def fix_concat_error(last_n=None):
    """修复合并错误"""
    print("=== 视频合并修复工具 ===")
    
    # 确保目录存在
    ensure_dirs()
    
    # 查找需要合并的视频
    videos = glob.glob(os.path.join(TEMP_DIR, "temp_*.mp4"))
    if not videos:
        print("未找到临时视频文件，尝试查找下载目录")
        download_dir = "test_downloads"
        if os.path.exists(download_dir):
            videos = glob.glob(os.path.join(download_dir, "*.mp4"))
    
    if not videos:
        print("未找到视频文件")
        return False
    
    # 按修改时间排序
    videos.sort(key=os.path.getmtime)
    
    # 处理last_n参数
    if last_n and isinstance(last_n, int) and last_n > 0:
        if last_n < len(videos):
            videos = videos[-last_n:]
            print(f"只处理最新的{last_n}个视频")
        else:
            print(f"处理所有{len(videos)}个视频")
    
    # 生成输出文件名
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(MERGED_DIR, f"{timestamp}.mp4")
    
    print(f"开始合并{len(videos)}个视频")
    
    # 使用concat demuxer合并
    return merge_with_concat_demuxer(videos, output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="修复视频合并错误")
    parser.add_argument("--last", "-l", type=int, help="只处理最后N个视频")
    args = parser.parse_args()
    
    if fix_concat_error(args.last):
        print("视频合并修复成功！")
    else:
        print("视频合并失败，请手动检查文件。")
