#!/usr/bin/env python3
import os
import shutil

def rename_files():
    """重命名验证文件以使命名更清晰"""
    print("开始重命名文件...")
    
    # 定义需要重命名的文件
    files_to_rename = {
        "verify_login.py": "verify_test_login.py",
        "verify_download.py": "verify_test_download.py"
    }
    
    # 获取当前目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 重命名文件
    for old_name, new_name in files_to_rename.items():
        old_path = os.path.join(base_dir, old_name)
        new_path = os.path.join(base_dir, new_name)
        
        if os.path.exists(old_path):
            # 如果新文件已存在，先备份
            if os.path.exists(new_path):
                backup_path = new_path + ".bak"
                shutil.copy2(new_path, backup_path)
                print(f"已备份现有文件 {new_name} 到 {backup_path}")
            
            # 复制文件并更新内容
            with open(old_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 写入新文件
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"已创建 {new_name}")
            
            # 询问是否删除旧文件
            delete_old = input(f"是否删除旧文件 {old_name}? (y/n): ").strip().lower()
            if delete_old == 'y':
                os.remove(old_path)
                print(f"已删除 {old_name}")
            else:
                print(f"已保留 {old_name}")
        else:
            print(f"文件 {old_name} 不存在，跳过")
    
    print("文件重命名完成!")

if __name__ == "__main__":
    rename_files()
