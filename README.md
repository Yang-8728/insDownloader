# Instagram 视频下载与合并工具

一个自动化工具，用于下载Instagram收藏视频，将它们合并为单个视频，并可选择自动上传到B站。

## 功能

- 📥 自动下载Instagram收藏的视频
- 🎬 将多个视频合并为单个视频
- 📤 自动上传合并后的视频到B站
- 📊 详细的日志记录
- 🔄 完整的自动化流程支持

## 使用方法

### 安装

```bash
git clone https://github.com/你的用户名/insDownloader.git
cd insDownloader
pip install -r requirements.txt
```

### 命令选项

```
python test_main.py [选项]
```

选项：
- `-d, --download`: 下载新视频
- `-m, --merge`: 合并已下载视频
- `-u, --upload`: 上传合并后的视频
- `-a, --all`: 执行完整流程（下载、合并、上传）
- `-l N, --last N`: 只合并最后N个视频
- `-f, --force`: 强制合并所有视频，不跳过已合并的
- `-t, --today`: 只合并今天下载的视频
- `-o NAME, --output NAME`: 指定合并输出文件名
- `-b N, --batch N`: 每批处理的最大视频数（默认15）

### 示例

```bash
# 执行完整流程：下载、合并、上传
python test_main.py -a

# 只下载新视频
python test_main.py -d

# 合并最后10个视频并指定输出名称
python test_main.py -m -l 10 -o "我的合集"

# 强制合并所有视频
python test_main.py -m -f

# 只合并今天下载的视频
python test_main.py -m -t
```

## 注意事项

- 首次使用需要登录Instagram账号
- 确保已安装所有必要的依赖
- 上传到B站需要设置相关账号信息

## 版本历史

- v1.2: 优化了错误处理和流程控制，增强了程序稳定性
- v1.1: 增加了批量处理和多种合并选项
- v1.0: 初始版本，基本下载和合并功能

## 许可

MIT
