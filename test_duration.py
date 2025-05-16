#!/usr/bin/env python3
import os
import sys
import glob
import time

def format_time(seconds):
    """将秒数格式化为分:秒格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}分{secs}秒" if minutes > 0 else f"{secs}秒"

def find_latest_video(folder="merged_videos"):
    """查找最新的视频文件并返回其绝对路径"""
    # 确保使用绝对路径
    abs_folder = os.path.abspath(folder)
    videos = glob.glob(os.path.join(abs_folder, "*.mp4"))
    if not videos:
        print(f"错误: 在 {abs_folder} 文件夹中没有找到视频")
        return None
    
    latest_video = max(videos, key=os.path.getmtime)
    print(f"找到最新视频: {latest_video}")
    return latest_video

def get_video_duration_moviepy(video_path):
    """使用moviepy获取视频时长"""
    start = time.time()
    try:
        # 方法1：使用try/except处理导入错误
        try:
            # 这行会产生Pylance警告，但不影响运行
            from moviepy.editor import VideoFileClip  # type: ignore
        except ImportError:
            print("MoviePy库未安装，请使用以下命令安装:")
            print("pip install moviepy")
            return None
            
        print("使用MoviePy读取视频时长...")
        
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        print(f"MoviePy方法成功，视频时长: {format_time(duration)}")
        print(f"耗时: {format_time(time.time() - start)}")
        return duration
    except Exception as e:
        print(f"MoviePy方法失败: {str(e)}")
        return None

def get_video_duration_ffprobe(video_path):
    """使用ffprobe获取视频时长"""
    start = time.time()
    try:
        import subprocess
        
        # 检查是否有ffprobe
        ffprobe_path = os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe")
        if not os.path.exists(ffprobe_path):
            print("本地ffprobe未找到，尝试使用系统路径...")
            ffprobe_path = "ffprobe"  # 尝试使用系统路径
        
        # 使用ffprobe获取视频时长
        cmd = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        
        print(f"FFprobe方法成功，视频时长: {format_time(duration)}")
        print(f"耗时: {format_time(time.time() - start)}")
        return duration
    except Exception as e:
        print(f"FFprobe方法失败: {str(e)}")
        return None

def get_serial_number(file_path="serial_number.txt"):
    """从序号文件中读取当前序号"""
    try:
        with open(file_path, "r") as file:
            serial_number = file.read().strip()
            print(f"当前序号: {serial_number}")
            return int(serial_number)
    except Exception as e:
        print(f"读取序号失败: {str(e)}")
        return None

def check_next_video_name():
    """检查下一个上传视频的名称"""
    serial_file = "serial_number.txt"
    
    if os.path.exists(serial_file):
        with open(serial_file, "r") as f:
            try:
                serial = int(f.read().strip())
                print(f"\n下一个视频标题将是: 海外离大谱#{serial}")
            except:
                print(f"\n无法读取序号文件: {serial_file}")
    else:
        print(f"\n序号文件不存在，下一个视频标题将是: 海外离大谱#1")

if __name__ == "__main__":
    print("=== 视频时长测试 ===")
    
    # 查找最新视频
    video_path = find_latest_video()
    if not video_path:
        sys.exit(1)
    
    # 仅使用FFprobe方法，不再使用MoviePy
    print("\n使用FFprobe获取视频时长")
    duration = get_video_duration_ffprobe(video_path)
    
    print("\n=== 测试结果 ===")
    if duration is not None:
        print(f"视频时长: {format_time(duration)} ({duration:.2f}秒)")
    
    print("\n=== 获取下一个视频序号 ===")
    # 检查下一个视频名称
    check_next_video_name()
    check_next_video_name()
