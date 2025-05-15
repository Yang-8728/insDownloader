#!/usr/bin/env python3
import os
import sys
from test_login import ensure_logged_in_user, import_session, get_cookiefile
from test_download import download_saved_videos

def main():
    """Instagram下载器应用的测试环境入口点"""
    try:
        print("\n📱 Instagram 视频下载工具 [测试环境]")
        print("=" * 40)
        print("⚠️ 警告：这是测试环境，不建议用于日常使用")
        
        # 检查是否有用户名
        username = ensure_logged_in_user()
        
        # 询问用户操作
        print("\n请选择操作:")
        print("1. 登录/更换账号")
        print("2. 下载收藏的视频")
        print("3. 退出")
        
        choice = input("输入选项 (1-3): ").strip()
        
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
        elif choice == "3":
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
