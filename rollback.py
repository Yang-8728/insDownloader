#!/usr/bin/env python3
import os
import shutil
import sys

def rollback_production():
    """从备份恢复生产代码"""
    # 定义路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 需要恢复的文件
    files_to_restore = ["download.py", "login.py", "main.py"]
    
    restored_count = 0
    for file in files_to_restore:
        file_path = os.path.join(base_dir, file)
        backup_path = file_path + ".bak"
        
        if os.path.exists(backup_path):
            # 恢复备份
            shutil.copy2(backup_path, file_path)
            print(f"已恢复 {file} 从备份")
            restored_count += 1
        else:
            print(f"没有找到 {file} 的备份文件")
    
    if restored_count > 0:
        print(f"\n✅ 已成功回退 {restored_count} 个文件")
    else:
        print("\n⚠️ 没有找到任何备份文件可以回退")

if __name__ == "__main__":
    rollback_production()
