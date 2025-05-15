#!/usr/bin/env python3
"""
简单的验证脚本 - 检查关键功能是否正常工作
支持单独验证登录或下载功能
"""
from login import ensure_logged_in_user, get_session_file_path
from download import download_saved_videos, download_dir, LOG_DIR
import os
import time
import sys

def verify_login():
    """验证登录功能"""
    print("\n===== 验证登录功能 =====")
    try:
        username = ensure_logged_in_user()
        print(f"✅ 已获取用户名: {username}")
        
        # 检查会话文件
        session_path = get_session_file_path(username)
        if os.path.exists(session_path):
            print(f"✅ 会话文件存在: {session_path}")
        else:
            print(f"❌ 会话文件不存在")
        return username
    except Exception as e:
        print(f"❌ 登录验证出错: {e}")
        return None

def verify_download(username=None):
    """验证下载功能"""
    print("\n===== 验证下载功能 =====")
    
    # 如果没有提供用户名，先验证登录
    if not username:
        username = verify_login()
        if not username:
            print("❌ 无法获取用户名，下载验证终止")
            return False
    
    print(f"下载目录: {download_dir}")
    print(f"日志目录: {LOG_DIR}")
    
    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 开始计时并下载
    start_time = time.time()
    
    try:
        count = download_saved_videos(username)
        
        # 计算耗时
        duration = time.time() - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        if count > 0:
            print(f"\n✅ 下载成功！共下载 {count} 个视频")
            print(f"耗时: {minutes}分{seconds}秒")
            
            # 检查文件
            video_files = [f for f in os.listdir(download_dir) if f.endswith('.mp4')]
            print(f"下载目录中的视频文件数: {len(video_files)}")
            if video_files:
                print(f"最新下载的视频: {video_files[-1]}")
            return True
        else:
            print("⚠️ 没有新视频可下载，或下载过程中出现问题")
            return False
    except Exception as e:
        print(f"❌ 下载验证出错: {e}")
        return False

def main():
    print("\n📱 Instagram 功能验证工具")
    print("=" * 30)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == "login":
            verify_login()
        elif action == "download":
            verify_download()
        else:
            print(f"❌ 未知的验证选项: {action}")
            print("可用选项: login, download")
    else:
        # 交互式模式
        print("\n请选择要验证的功能:")
        print("1. 登录功能")
        print("2. 下载功能")
        print("3. 登录+下载功能")
        
        choice = input("输入选项 (1-3): ").strip()
        
        if choice == "1":
            verify_login()
        elif choice == "2":
            verify_download()
        elif choice == "3":
            username = verify_login()
            if username:
                verify_download(username)
        else:
            print("❌ 无效选项")
    
    print("\n✅ 验证完成")

if __name__ == "__main__":
    main()