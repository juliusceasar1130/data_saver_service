#!/bin/bash
echo "========================================"
echo "启动数据保存服务"
echo "========================================"
cd "$(dirname "$0")"
python3 data_saver_service.py

