#!/usr/bin/env python3
"""
修复视频合并问题的工具
Tool to fix video merging issues

当合并大量视频时，FFmpeg的filter_complex可能会出错，特别是在处理不同来源的视频时
When merging many videos, FFmpeg's filter_complex might fail, especially when processing videos from different sources
"""

import os
import glob
import subprocess
import json
from tqdm import tqdm

# 配置 / Configuration
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe"))
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe"))
TEMP_DIR = "temp"
MERGED_DIR = "merged_videos"

def ensure_dirs():
    """确保所需目录存在
    Ensure required directories exist"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(MERGED_DIR, exist_ok=True)

def get_stream_info(video_path):
    """获取视频的流信息
    Get stream information for a video"""
    try:
        # 确保ffprobe路径存在
        if not os.path.exists(FFPROBE_PATH):
            print(f"警告: FFprobe路径不存在: {FFPROBE_PATH}")
            print("尝试使用系统路径...")
            ffprobe_cmd = "ffprobe"  # 使用系统路径
        else:
            ffprobe_cmd = FFPROBE_PATH
            
        cmd = [
            ffprobe_cmd,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            video_path
        ]
        
        if not os.path.exists(video_path):
            print(f"错误: 视频文件不存在: {video_path}")
            return None
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFprobe命令失败 (代码 {result.returncode}): {result.stderr}")
            return None
            
        if not result.stdout:
            print("FFprobe未返回任何输出")
            return None
            
        try:
            info = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"FFprobe输出: {result.stdout[:100]}...")  # 只显示前100个字符
            return None
        
        # 查找视频和音频流索引
        video_index = None
        audio_index = None
        
        streams = info.get("streams", [])
        if not streams:
            print("警告: 未在视频中找到流")
        
        for stream in streams:
            if stream.get("codec_type") == "video" and video_index is None:
                video_index = stream.get("index", 0)
            elif stream.get("codec_type") == "audio" and audio_index is None:
                audio_index = stream.get("index", 0)
        
        return {
            "video_index": video_index,
            "audio_index": audio_index,
            "has_video": video_index is not None,
            "has_audio": audio_index is not None
        }
    except Exception as e:
        print(f"分析视频流时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误堆栈
        
    # 如果无法获取信息，返回默认值
    return {
        "video_index": 0,
        "audio_index": 0,
        "has_video": True,
        "has_audio": True
    }

def merge_videos_with_concat_demuxer(video_paths, output_path):
    """使用concat demuxer合并视频（更可靠但要求视频编码一致）
    Merge videos using concat demuxer (more reliable but requires consistent encoding)"""
    try:
        # 检查ffmpeg是否存在
        if not os.path.exists(FFMPEG_PATH):
            print(f"错误: FFmpeg路径不存在: {FFMPEG_PATH}")
            return False
            
        # 检查所有视频文件是否存在
        for video in video_paths:
            if not os.path.exists(video):
                print(f"错误: 视频文件不存在: {video}")
                return False
                
        # 创建一个临时的文件列表
        list_file = os.path.join(TEMP_DIR, "files.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for video in video_paths:
                # 使用双反斜杠转义路径
                safe_path = os.path.abspath(video).replace("\\", "\\\\")
                f.write(f"file '{safe_path}'\n")
        
        # 使用concat demuxer
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",  # 直接复制流，不重新编码
            output_path
        ]
        
        print(f"执行FFmpeg命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg命令失败 (代码 {result.returncode}):")
            print(f"错误输出: {result.stderr}")
            return False
            
        # 验证输出文件是否创建成功
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            print(f"错误: 输出文件未创建或为空: {output_path}")
            return False
            
        return True
    except Exception as e:
        print(f"合并视频时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def merge_videos_in_batches(video_paths, output_path, batch_size=10):
    """分批合并视频，然后合并这些批次
    Merge videos in batches, then merge those batches"""
    if len(video_paths) <= batch_size:
        # 如果视频数量少，直接尝试demuxer方法 / If few videos, try demuxer method directly
        return merge_videos_with_concat_demuxer(video_paths, output_path)
    
    # 分批处理 / Process in batches
    batch_outputs = []
    for i in range(0, len(video_paths), batch_size):
        batch = video_paths[i:i+batch_size]
        batch_output = os.path.join(TEMP_DIR, f"batch_{i//batch_size}.mp4")
        
        print(f"处理批次 {i//batch_size + 1}/{(len(video_paths) + batch_size - 1)//batch_size}，包含 {len(batch)} 个视频")
        # Processing batch X/Y, containing Z videos
        
        if merge_videos_with_concat_demuxer(batch, batch_output):
            batch_outputs.append(batch_output)
        else:
            print(f"批次 {i//batch_size + 1} 处理失败")  # Batch X processing failed
            return False
    
    # 合并所有批次 / Merge all batches
    if len(batch_outputs) == 1:
        # 只有一个批次，直接重命名 / Only one batch, just rename
        import shutil
        shutil.move(batch_outputs[0], output_path)
        return True
    else:
        print(f"合并 {len(batch_outputs)} 个批次...")  # Merging X batches
        return merge_videos_with_concat_demuxer(batch_outputs, output_path)

def fix_merge_problem(last_n=None, output_name=None):
    """修复当前temp目录中的视频合并问题
    Fix merge problem with videos in current temp directory
    
    Args:
        last_n: 只处理最后N个视频 / Only process last N videos
        output_name: 指定输出文件名 / Specify output filename
    """
    # 确保目录存在
    ensure_dirs()
    
    # 查找所有临时视频文件
    temp_videos = glob.glob(os.path.join(TEMP_DIR, "temp_*.mp4"))
    if not temp_videos:
        print("没有找到临时视频文件")
        return False
    
    # 按文件名排序，确保顺序正确
    temp_videos.sort()
    
    # 处理last_n参数
    if last_n and isinstance(last_n, int) and last_n > 0:
        if last_n < len(temp_videos):
            print(f"根据参数只处理最新的{last_n}个视频（共有{len(temp_videos)}个）")
            temp_videos = temp_videos[-last_n:]  # 取最后N个
        else:
            print(f"要求处理最后{last_n}个视频，但只有{len(temp_videos)}个视频可用，将处理所有视频")
    
    print(f"找到 {len(temp_videos)} 个视频文件")
    
    # 生成输出文件名
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if output_name:
        filename = f"{output_name}.mp4"
    else:
        filename = f"{timestamp}.mp4"
    output_path = os.path.join(MERGED_DIR, filename)
    
    # 执行分批合并
    result = merge_videos_in_batches(temp_videos, output_path)
    
    if result:
        print(f"合并成功！输出文件: {output_path}")
        return True
    else:
        print("合并失败")
        return False

# 添加命令行支持
if __name__ == "__main__":
    print("=== 视频合并修复工具 ===")
    
    import argparse
    parser = argparse.ArgumentParser(description="修复视频合并问题 / Fix video merging issues")
    parser.add_argument("--last", "-l", type=int, help="只合并最后N个视频 / Only merge last N videos")
    parser.add_argument("--output", "-o", help="指定输出文件名 / Specify output filename")
    args = parser.parse_args()
    
    fix_merge_problem(args.last, args.output)
