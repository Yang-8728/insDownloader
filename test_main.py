#!/usr/bin/env python3
import os
import sys
import time
from test_login import ensure_logged_in_user, import_session, get_cookiefile
from test_download import download_saved_videos
from test_merge import merge_all_downloaded_videos
from test_upload import upload_latest_merged_video  # 导入上传功能

def main():
    """Instagram下载器应用的测试环境入口点"""
    try:
        print("\n📱 Instagram 视频下载工具 [测试环境]")
        print("=" * 40)
        print("⚠️ 警告：这是测试环境，不建议用于日常使用")
        
        # 检查是否有用户名
        username = ensure_logged_in_user()
        
        # 询问用户操作 - 添加上传功能和新的完整流程
        print("\n请选择操作:")
        print("1. 登录/更换账号")
        print("2. 下载收藏的视频")
        print("3. 合并已下载视频")
        print("4. 上传到B站")
        print("5. 完整流程测试：登录+下载+合并+上传")
        print("6. 退出")
        
        choice = input("输入选项 (1-6): ").strip()
        
        if choice == "1":
            try:
                cookiefile = get_cookiefile()
                import_session(cookiefile, username)
                print("✅ 登录成功，现在可以下载视频了")
                return 0
            except Exception as e:
                print(f"❌ 登录失败: {str(e)}")
                return 1
        elif choice == "2":
            count = download_saved_videos(username)
            if count > 0:
                print(f"✅ 成功下载 {count} 个视频")
            return 0 if count > 0 else 1
        elif choice == "3":  # 合并功能
            print("\n合并已下载视频中...")
            output_path, count = merge_all_downloaded_videos()
            if count > 0:
                print(f"✅ 成功合并了 {count} 个视频。")
                print(f"✅ 输出文件: {output_path}")
                return 0
            else:
                print("❌ 没有视频被合并或发生了错误。")
                return 1
        elif choice == "4":  # 上传功能
            print("\n=== 开始上传到B站 ===")
            try:
                success = upload_latest_merged_video()
                if success:
                    print("上传成功完成")
                    return 0
                else:
                    print("上传过程未完成，请查看错误信息")
                    return 1
            except Exception as e:
                print(f"上传过程出现异常: {str(e)}")
                return 1
        elif choice == "5":  # 完整流程测试（包含上传）
            print("\n=== 开始完整流程测试 ===")
            total_start_time = time.time()  # 记录总开始时间
            video_duration = 0  # 合并视频的时长
            
            # 第一步：登录验证
            try:
                print("\n【步骤1】登录验证")
                cookiefile = get_cookiefile()
                print(f"使用 Firefox cookies: {cookiefile}")
                import_session(cookiefile, username)
                print("登录成功：会话文件已保存")
            except Exception as e:
                print(f"登录失败: {str(e)}")
                return 1
            
            # 第二步：下载视频
            print("\n【步骤2】下载视频")
            download_start = time.time()
            download_count = download_saved_videos(username)
            download_time = time.time() - download_start
            if download_count <= 0:
                print("没有新视频可下载，流程结束")
                return 0
            print(f"成功下载: {download_count} 个视频")
            
            # 第三步：合并视频
            print("\n【步骤3】合并视频")
            merge_start = time.time()
            output_path, merge_count = merge_all_downloaded_videos()
            merge_time = time.time() - merge_start
            if merge_count <= 0:
                print("没有视频被合并，流程结束")
                return 0
            print(f"成功合并: {merge_count} 个视频")
            print(f"输出文件: {output_path}")
            
            # 获取视频时长（仅使用FFprobe）
            video_duration = 0
            try:
                import subprocess
                
                # 检查是否有ffprobe
                ffprobe_path = os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe")
                if os.path.exists(ffprobe_path):
                    # 使用ffprobe获取视频时长
                    cmd = [
                        ffprobe_path,
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        os.path.abspath(output_path)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    video_duration = float(result.stdout.strip())
                else:
                    print("警告: FFprobe未找到，无法获取准确视频时长")
            except Exception as e:
                print(f"获取视频时长失败: {e}")
            
            # 第四步：上传视频
            print("\n【步骤4】上传视频")
            try:
                success, upload_time = upload_latest_merged_video()
            except Exception as e:
                print(f"上传失败: {str(e)}")
                return 1
            
            # 计算总时间并打印总结信息
            total_time = time.time() - total_start_time
            
            # 格式化时间
            def format_time(seconds):
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes}分{secs}秒" if minutes > 0 else f"{secs}秒"
            
            # 打印总结信息
            video_duration_str = format_time(video_duration)
            total_time_str = format_time(total_time)
            
            print(f"\n=== 新下载了{download_count}个视频，合并后视频时长{video_duration_str}，总用时{total_time_str} ===")
            
            return 0
        elif choice == "6":  # 更新为第6个选项
            print("再见!")
            return 0
        else:
            print("❌ 无效选项")
            return 1
    except KeyboardInterrupt:
        print("\n\n用户已取消操作，程序退出")
        return 0
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户已取消操作，程序退出")
        sys.exit(0)
