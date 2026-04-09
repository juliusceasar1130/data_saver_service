# 使用轻量级 Python 10 镜像 (性能更好且可能利用本地缓存)
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 1. 禁用 Python 缓冲，确保日志立即输出到 Docker logs
# 2. 也是一种通用的最佳实践
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装 Python 依赖
# 技巧：先只复制依赖安装命令，利用 Docker 缓存层
# websockets: WebSocket 客户端
# psycopg2-binary: PostgreSQL 驱动
# python-dotenv: 支持加载 .env 文件
RUN pip install --no-cache-dir \
    websockets \
    psycopg2-binary \
    python-dotenv \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制程序代码
COPY data_saver_service_v3_docker.py .
COPY rb_position_manager_postgresql.py .

# 创建非特权用户运行程序
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# 启动命令
# 使用 list 格式 (exec form) 是最佳实践
CMD ["python", "data_saver_service_v3_docker.py"]
