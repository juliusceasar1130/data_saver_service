# 🚀 跨电脑部署说明 (Deployment Guide)

本文档指导如何将 `data_saver_service_v2` 部署到一台全新的机器上。

## 1. 准备材料 (文件清单)

请将以下文件复制到目标机器的同一个文件夹中（例如 `D:\services\data-saver`）：

| 文件名 | 说明 | 必选/可选 |
| :--- | :--- | :--- |
| `docker-compose.yml` | 容器编排定义 | **必选** |
| `Dockerfile` | 镜像构建规则 | **必选** |
| `.dockerignore` | 构建优化排除清单 | 建议带上 |
| `data_saver_service_v2_docker.py` | Python 业务主程序 | **必选** |
| `rb_position_manager_postgresql.py` | 数据库操作封装模块 | **必选** |
| `deviceConfig.json` | 设备列表配置文件 (主机修改容器同步) | **必选** |
| `create_tables_postgresql.sql` | 数据库表结构自动初始化脚本 | **必选** |
| `.env.example` | 环境变量模板 (用于生成 .env) | **必选** |

## 2. 部署步骤

### 第一步：安装 Docker 环境
确保目标机器已安装：
*   **Docker Desktop** (Windows/Mac) 或 **Docker Engine** (Linux)
*   **Docker Compose** (现代 Docker 已内置)

### 第二步：配置环境变量
1.  在项目文件夹下，将 `.env.example` 复制并重命名为 **`.env`**。
2.  使用记事本或编辑器打开 `.env`，根据目标环境修改配置：
    ```bash
    # 如果使用本项目内置的数据库，一般保持默认值即可
    POSTGRES_USER=root
    POSTGRES_PASSWORD=your_secure_password
    
    # 修改为实际的 WebSocket 地址
    WS_SERVER_HOST=172.21.12.73
    ```

### 第三步：修改设备清单
编辑 `deviceConfig.json`，确保包含目标环境需要订阅的 PLC Tag 和设备信息。

### 第四步：启动服务
打开终端（CMD/PowerShell/Terminal），进入该文件夹，运行：

```bash
docker-compose up -d --build
```
*   `--build`: 确保在本地重新根据源码构建镜像。
*   `-d`: 后台运行，关闭窗口不会停止服务。

---

## 3. 常用管理命令

*   **查看运行状态**：
    ```bash
    docker-compose ps
    ```
*   **实时查看程序日志**：
    ```bash
    docker-compose logs -f data-saver-service
    ```
*   **停止并卸载所有服务**：
    ```bash
    docker-compose down
    ```
*   **修改代码或配置后重启**：
    ```bash
    # 如果只改了 deviceConfig.json
    docker-compose restart
    
    # 如果改了 Python 代码或 .env
    docker-compose up -d --build
    ```

## 4. 注意事项
1.  **数据保存**：数据库数据存放在自动创建的 `pgdata` 卷中。即使运行 `docker-compose down`，数据也不会丢失。
2.  **网络权限**：请确保目标机器能正常访问宿主机 IP（尤其是 WebSocket 服务器）。
3.  **初次启动**：第一次运行由于需要拉取 Python 和 Postgres 镜像，速度可能较慢，请保持网络畅通。
