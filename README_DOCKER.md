# Docker 部署说明

更新时间：2026-04-13 18:05 Asia/Shanghai

主要修改内容：

- 补充 Docker Desktop 下缺陷汇总定时刷新的独立容器方案
- 新增 `defect-refresh` 服务与 Windows 任务计划程序调用方式说明

本文档说明如何使用 Docker 部署 `data_saver_service_v3_docker.py` 服务。

## 1. 目录结构

确保目录下包含以下文件：
- `data_saver_service_v3_docker.py`: 主程序（支持环境变量）
- `rb_position_manager_postgresql.py`: 数据库管理模块
- `deviceConfig.json`: 设备配置文件
- `Dockerfile`: 构建镜像说明
- `docker-compose.yml`: 容器编排文件
- `.env`: 环境变量配置文件（从 `.env_example` 复制）

## 2. 快速开始

### 步骤 1: 准备配置文件

如果需要修改数据库连接或 WebSocket 地址，请复制模板并编辑：

```bash
Copy-Item .env_example .env
# 编辑 .env 文件填入实际参数
```

### 步骤 2: 启动服务

在当前目录下运行：

```bash
docker compose up -d
```

这将会：
1. 构建名为 `data-saver-service:v3` 的镜像
2. 启动容器
3. 挂载当前的 `deviceConfig.json` 到容器中

### 步骤 3: 查看日志

```bash
docker compose logs -f
```

### 步骤 4: 停止服务

```bash
docker compose down
```

## 3. 修改配置

### 修改数据库配置 (DB_CONFIG)

有两种方式：
1. **推荐**: 修改 `.env` 文件中的 `DB_HOST`, `DB_USER` 等变量，然后重启容器 (`docker compose up -d`)。
2. 直接修改 `docker-compose.yml` 中的 `environment` 部分。

### 修改设备列表 (deviceConfig.json)

由于使用了 Volume 挂载，您可以直接修改主机上的 `deviceConfig.json` 文件。

**注意**: 修改文件后，需要重启容器才能生效（因为程序是在启动时加载配置的）：

```bash
docker compose restart
```

## 4. 故障排查

- **连接不上数据库**: 检查 `.env` 中的 IP 地址。如果是宿主机上的数据库，无法使用 `127.0.0.1`，请使用宿主机的局域网 IP（如 `192.168.x.x`）。
- **找不到配置文件**: 确保 `docker-compose.yml` 中 `volumes` 路径正确。

## 5. defect-refresh 定时刷新（Docker Desktop 推荐）

如果你需要稳定运行：

- `defect_database/refresh_history_station_defect_summary.py`

推荐方式不是在容器里再跑一个常驻 `cron`，而是：

- `postgres`、`data-saver-service` 继续常驻
- `defect-refresh` 容器只在被触发时执行一次
- Windows 任务计划程序定时触发该容器

### 5.1 首次准备

1. 启动基础服务：

```bash
docker compose up -d postgres data-saver-service
```

2. 确认目标数据库已存在：

- 默认 `.env` 中缺陷汇总目标库是 `DEFECT_TARGET_DB_NAME=defect_db`
- 如果 compose 中的 PostgreSQL 还没有这个数据库，请先手工创建
- 或者把 `.env` 中 `DEFECT_TARGET_DB_NAME` 改成已存在的数据库名

3. 初始化刷新状态：

```bash
docker compose --profile manual run --rm defect-refresh --init-state
```

4. 手工试跑一次：

```bash
docker compose --profile manual run --rm defect-refresh --refresh
```

5. 查看状态：

```bash
docker compose --profile manual run --rm defect-refresh --print-status
```

### 5.2 Windows 任务计划程序推荐命令

推荐直接调用仓库中的 PowerShell 包装脚本：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\scripts\refresh_history_station_defect_summary_docker.ps1"
```

说明：

- 脚本默认执行 `--refresh`
- 日志会写到宿主机 `logs/history_station_defect_summary_docker.log`
- 如需手工执行初始化或状态检查，可传参：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\scripts\refresh_history_station_defect_summary_docker.ps1" -Mode --print-status
```
