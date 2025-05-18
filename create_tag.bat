@echo off
echo 创建Git标签 v1.1
git tag -a v1.1 -m "Version 1.1 - 视频合并与上传功能稳定版"
echo 推送标签到远程仓库
git push origin v1.1
echo 完成!
pause
