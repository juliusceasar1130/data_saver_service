@echo off
REM 修改时间：2025年9月1日14点05分
REM 修改内容：Windows批处理启动脚本 - 更新路径为service目录

echo ================================
echo  WebSocket服务器启动脚本
echo ================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python！请先安装Python 3.7+
    pause
    exit /b 1
)

REM 进入service目录
cd /d "%~dp0"

REM 检查依赖是否安装
echo 检查依赖包...
pip show websockets >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败！
        pause
        exit /b 1
    )
)

echo 启动WebSocket服务器...
echo.
python websocket_server.py

echo.
echo 服务器已停止
pause
