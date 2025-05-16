#!/usr/bin/env python3
import os
import sys
from test_login import ensure_logged_in_user, import_session, get_cookiefile
from test_download import download_saved_videos
from test_merge import merge_all_downloaded_videos

def main():
    """Instagram下载器应用的测试环境入口点"""
    try:
        print("\n📱 Instagram 视频下载工具 [测试环境]")
        print("=" * 40)
        print("⚠️ 警告：这是测试环境，不建议用于日常使用")
        
        # 检查是否有用户名
        username = ensure_logged_in_user()
        
        # 询问用户操作 - 修改菜单，添加全流程测试选项
        print("\n请选择操作:")
        print("1. 登录/更换账号")
        print("2. 下载收藏的视频")
        print("3. 合并已下载视频")
        print("4. 完整流程测试：登录+下载+合并")
        print("5. 退出")
        
        choice = input("输入选项 (1-5): ").strip()
        
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
        elif choice == "4":  # 完整流程测试
            print("\n=== 开始完整流程测试 ===")
            
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
            download_count = download_saved_videos(username)
            if download_count <= 0:
                print("没有新视频可下载，流程结束")
                return 0
            print(f"成功下载: {download_count} 个视频")
            
            # 第三步：合并视频
            print("\n【步骤3】合并视频")
            output_path, merge_count = merge_all_downloaded_videos()
            if merge_count > 0:
                print(f"成功合并: {merge_count} 个视频")
                print(f"输出文件: {output_path}")
            else:
                print("没有视频被合并，可能已经合并过")
            
            print("\n=== 完整流程测试完成 ===")
            return 0
            
        elif choice == "5":  # 更新为第5个选项
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
