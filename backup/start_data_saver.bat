@echo off
chcp 65001 >nul
echo ========================================
echo 启动数据保存服务
echo ========================================
cd /d %~dp0
python data_saver_service.py
pause

