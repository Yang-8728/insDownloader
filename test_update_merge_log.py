import os
import glob

# 配置路径
downloads_dir = "test_downloads"
logs_dir = "test_logs"
merged_log = os.path.join(logs_dir, "merged.log")

# 确保logs目录存在
os.makedirs(logs_dir, exist_ok=True)

# 获取所有视频文件
video_files = glob.glob(os.path.join(downloads_dir, "*.mp4"))
video_filenames = [os.path.basename(file) for file in video_files]

# 写入merged.log
with open(merged_log, "w", encoding="utf-8") as f:
    for filename in video_filenames:
        f.write(f"{filename}\n")

print(f"完成！已将{len(video_filenames)}个视频文件名写入merged.log")
print(f"文件保存在: {os.path.abspath(merged_log)}")