#!/usr/bin/env python3
import os
import sys
import time
import argparse
from datetime import datetime, date
import glob

from test_login import ensure_logged_in_user, import_session, get_cookiefile
from test_download import download_saved_videos
from test_merge import merge_all_downloaded_videos
from test_upload import upload_latest_merged_video  # 导入上传功能

def merge_todays_videos(downloads_dir="test_downloads", output_name=None):
    """合并今天下载的视频
    Merge videos downloaded today"""
    # 获取今天的日期
    today = date.today().strftime("%Y-%m-%d")
    
    # 查找今天修改的视频文件
    today_videos = []
    if os.path.exists(downloads_dir):
        for file in os.listdir(downloads_dir):
            if file.endswith('.mp4'):
                file_path = os.path.join(downloads_dir, file)
                # 获取文件修改时间
                mod_time = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
                
                # 如果是今天修改的，添加到列表
                if file_date == today:
                    today_videos.append(file_path)
    
    if not today_videos:
        print(f"今天没有下载任何视频")
        return None, 0
    
    print(f"找到今天下载的 {len(today_videos)} 个视频")
    
    # 如果没有指定输出名称，使用带日期的名称
    if not output_name:
        output_name = f"今日合集_{today}"
    
    # 调用合并函数
    from test_merge import merge_specific_videos
    return merge_specific_videos(downloads_dir, output_name=output_name, last_n=len(today_videos))

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Instagram视频下载与合并工具 / Instagram Video Download and Merge Tool")
    parser.add_argument("--download", "-d", action="store_true", help="下载新视频 / Download new videos")
    parser.add_argument("--merge", "-m", action="store_true", help="合并已下载视频 / Merge downloaded videos")
    parser.add_argument("--upload", "-u", action="store_true", help="上传合并后的视频 / Upload merged video")
    parser.add_argument("--all", "-a", action="store_true", help="执行完整流程：下载、合并、上传 / Execute complete workflow: download, merge, upload")
    
    # 新增参数
    parser.add_argument("--last", "-l", type=int, help="只合并最后N个视频 / Only merge last N videos")
    parser.add_argument("--force", "-f", action="store_true", help="强制合并所有视频，不跳过已合并的 / Force merge all videos")
    parser.add_argument("--today", "-t", action="store_true", help="只合并今天下载的视频 / Only merge videos downloaded today")
    parser.add_argument("--output", "-o", help="指定合并输出文件名 / Specify merge output filename")
    parser.add_argument("--batch", "-b", type=int, default=15, help="每批处理的最大视频数 / Maximum videos per batch")
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 执行操作
    start_time = time.time()
    
    try:
        # 添加详细的日志记录，帮助调试
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        def log_message(msg):
            print(msg)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        
        log_message("=== 开始执行操作 ===")
        
        # 检查环境
        log_message(f"Python版本: {sys.version}")
        log_message(f"当前工作目录: {os.getcwd()}")
        
        # 检查必要目录
        for dir_name in ["test_downloads", "merged_videos", "screenshots", "temp"]:
            os.makedirs(dir_name, exist_ok=True)
            log_message(f"确保目录存在: {dir_name}")
        
        # 下载视频
        if args.download or args.all:
            try:
                log_message("开始下载新视频...")
                # 使用更简单直接的方式调用已导入的函数
                try:
                    # 导入和确保用户已登录
                    username = ensure_logged_in_user()
                    if username:
                        log_message(f"已登录用户: {username}")
                        # 直接调用已导入的函数
                        download_count = download_saved_videos(username)
                        log_message(f"下载完成，共 {download_count} 个视频")
                    else:
                        log_message("未找到已登录用户，请先确保登录成功")
                except Exception as e:
                    log_message(f"调用下载函数时出错: {str(e)}")
                    import traceback
                    log_message(traceback.format_exc())
            except Exception as e:
                log_message(f"下载过程中出错: {e}")
                import traceback
                log_message(traceback.format_exc())
                log_message("继续执行后续步骤")
        
        merged_path = None  # 记录合并后的视频路径
        
        # 合并视频
        if args.merge or args.all:
            try:
                log_message("开始合并视频...")
                
                if args.today:
                    # 合并今天下载的视频
                    log_message("合并今天下载的视频...")
                    merged_path, count = merge_todays_videos(
                        "test_downloads", 
                        args.output
                    )
                else:
                    # 使用普通合并
                    try:
                        # 直接调用导入的函数，简化参数处理
                        if args.last:
                            # 如果指定了last参数
                            merged_path, count = merge_all_downloaded_videos(
                                "test_downloads",
                                output_name=args.output,
                                max_per_batch=args.batch,
                                last_n=args.last,
                                force_all=args.force
                            )
                        else:
                            # 不带last参数的调用
                            merged_path, count = merge_all_downloaded_videos(
                                "test_downloads",
                                output_name=args.output,
                                max_per_batch=args.batch,
                                force_all=args.force
                            )
                    except TypeError as e:
                        # 如果参数不匹配，尝试基本调用
                        log_message(f"合并函数参数不匹配: {e}, 尝试使用基本参数")
                        merged_path, count = merge_all_downloaded_videos()
                
                if merged_path:
                    log_message(f"视频合并完成，共 {count} 个视频，保存为：{merged_path}")
                else:
                    log_message("合并视频失败或没有视频需要合并")
            except Exception as e:
                log_message(f"合并过程中出错: {e}")
                import traceback
                log_message(traceback.format_exc())
                log_message("继续执行后续步骤")
        
        # 合并成功后，检查是否自动上传
        if merged_path and args.merge and not args.upload and not args.all:
            log_message("\n合并完成后自动执行上传操作...")
            try_upload_video(merged_path, log_message)
        
        # 显式的上传命令 (或者作为all命令的一部分)
        if args.upload or args.all:
            if not merged_path:
                # 先尝试获取视频路径
                log_message("尝试查找最新的合并视频用于上传...")
                merged_folder = "merged_videos"
                os.makedirs(merged_folder, exist_ok=True)
                videos = glob.glob(os.path.join(merged_folder, "*.mp4"))
                if videos:
                    merged_path = max(videos, key=os.path.getmtime)
                    log_message(f"找到最新合并视频: {merged_path}")
                else:
                    log_message("未找到可上传的视频")
                    videos = glob.glob(os.path.join("test_downloads", "*.mp4"))
                    if videos:
                        merged_path = max(videos, key=os.path.getmtime)
                        log_message(f"尝试使用下载目录中的最新视频: {merged_path}")
                    else:
                        log_message("下载目录中也没有找到视频")
                        raise FileNotFoundError("没有可上传的视频文件")
        
            if merged_path:
                try_upload_video(merged_path, log_message)
        
        # 显示总用时
        total_time = time.time() - start_time
        log_message(f"\n全部操作完成，总用时：{format_duration(total_time)}")
    
    except Exception as e:
        print(f"执行过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 尝试记录错误到文件
        try:
            error_log = os.path.join("logs", "error.log")
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now()} ===\n")
                f.write(f"错误: {str(e)}\n")
                f.write(traceback.format_exc())
                f.write("\n")
            print(f"详细错误已记录到: {error_log}")
        except:
            pass

# 修改上传视频的函数，增加日志记录参数
def try_upload_video(video_path, log_func=print):
    """尝试上传指定的视频文件到B站"""
    log_func(f"准备上传视频到B站: {video_path}")
    
    # 确保视频文件存在
    if not os.path.exists(video_path):
        log_func(f"错误: 视频文件不存在: {video_path}")
        return False
        
    # 导入上传模块并调用函数
    try:
        log_func("开始上传流程...")
        
        try:
            # 直接调用，新版本支持指定路径
            success, duration = upload_latest_merged_video(video_path=video_path)
        except TypeError:
            # 如果函数不接受视频路径参数，确保视频在正确位置后使用无参数调用
            log_func("上传函数不支持路径参数，使用自动查找方式上传")
            merged_folder = "merged_videos"
            if not video_path.startswith(os.path.abspath(merged_folder)):
                target_path = os.path.join(merged_folder, os.path.basename(video_path))
                if not os.path.exists(target_path) or os.path.getsize(target_path) != os.path.getsize(video_path):
                    log_func(f"复制视频到上传目录: {target_path}")
                    import shutil
                    shutil.copy2(video_path, target_path)
            
            success, duration = upload_latest_merged_video()
        
        if success:
            log_func(f"🎉 上传成功！用时：{format_duration(duration)}")
        else:
            log_func(f"❌ 上传失败，用时：{format_duration(duration)}")
            
        return success
    except Exception as e:
        log_func(f"上传过程中出错: {e}")
        import traceback
        log_func(traceback.format_exc())
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
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户已取消操作，程序退出")
        sys.exit(0)
