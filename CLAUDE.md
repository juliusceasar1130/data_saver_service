# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

汽车涂装车间工业数据系统，包含两大子系统：
- **实时车辆追踪** (`rollerbed_tracking_db`)：通过 WebSocket 从 PLC 采集 BodyID/CarrierID，写入 PostgreSQL
- **缺陷汇总 ETL** (`defect_db`)：从 PostgreSQL/SQL Server 源库增量抽取缺陷检测结果，写回本地汇总表

另有一个 `analytics_db`（规划中/部分落地），通过 FDW 跨库整合车辆位置与质量缺陷数据，为 SQL Agent 提供统一只读分析面。

## 环境与关键命令

```bash
# 激活 Conda 环境（所有 Python 脚本的前提）
conda activate websoket

# 安装依赖
pip install -r requirements.txt
```

### 实时采集服务

```bash
# 宿主机直接运行
python data_saver_service_v3_docker.py

# Docker 部署
docker compose up -d postgres data-saver-service
docker compose logs -f data-saver-service
docker compose down
```

### 缺陷汇总 ETL（`defect_database/refresh_history_station_defect_summary.py`）

```bash
# 初始化水位（首次使用或切库后执行一次）
python defect_database/refresh_history_station_defect_summary.py --init-state

# 执行一次增量刷新
python defect_database/refresh_history_station_defect_summary.py --refresh

# 查看当前水位和状态
python defect_database/refresh_history_station_defect_summary.py --print-status
```

### 数据库初始化

```bash
# 全新部署：执行 DDL 建表
psql -U root -d rollerbed_tracking_db -f create_tables_postgresql.sql

# 初始化 98 个 RB 位置记录（从 deviceConfig.json 读取）
python init_rb_positions_postgresql.py

# 预填充字典表 (process_areas, carrier_types)
python init_seed_data_postgresql.py
```

### Docker 缺陷刷新（备选方案，企业内网优先用宿主机）

```bash
docker compose --profile manual run --rm defect-refresh --init-state
docker compose --profile manual run --rm defect-refresh --refresh
docker compose --profile manual run --rm defect-refresh --print-status
```

### Windows 任务计划程序调度

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\defect_database\scripts\refresh_history_station_defect_summary.ps1" -PythonExe "D:\000_software_install\miniconda3\envs\websoket\python.exe"
```

## 架构概览

### 数据流

```
PLC 设备 → WebSocket Server (172.21.12.73:8088)
                ↓
   data_saver_service_v3_docker.py  ← 订阅 BodyID + CarrierID
                ↓
   rb_position_manager_postgresql.py  (psycopg2)
                ↓
   rollerbed_tracking_db (PostgreSQL) :: rb_position_data (98 行固定位置)
                ↓                                    ↓
          (FDW 只读)                          defect_db :: history_station_defect_summary
                ↓                                    ↑
          analytics_db  ←── 跨库整合 ────────────────┘
                ↓                      (refresh_history_station_defect_summary.py ETL)
          SQL Agent (只读查询)
```

### 核心模块

**`rb_position_manager_postgresql.py`** — `rollerbed_tracking_db` 的数据库操作封装：
- `RBPositionDataManager`: 提供 `update_vehicle_by_tag()`、`update_carrier_id_by_tag()`、`clear_vehicle_by_tag()`、`get_statistics()` 等方法
- `VehicleDataParser`: 解析 30 字符车身数据（14 位 vehicle_id + 5 位 body_type + 4 位 color_code + 3 位 platform_code + 黑顶/返工/预留标志位）

**`data_saver_service_v3_docker.py`** — WebSocket 长连接客户端：
- 连接 `ws://{host}/ws/emosweb`，发送 `advise` 订阅消息
- 从 `deviceConfig.json` 读取 35 个 PLC 设备、98 个 RB 位置及 8 个工艺区域配置
- 同时订阅 BodyID（30 字符车身数据）和 CarrierID（载体标识）
- 支持心跳保活（默认 2s）、自动重连，通过环境变量配置

**`defect_database/refresh_history_station_defect_summary.py`** — 缺陷汇总增量刷新：
- "双连接、单次执行、增量落库" 模式：目标固定写本地 `defect_db`，源可选 PostgreSQL/SQL Server
- 水位推进 + replay window：覆盖晚到的 `history_detail`，通过 `UPSERT` 幂等写入
- PostgreSQL advisory lock 并发控制，状态表 + 日志表追踪执行历史
- 支持 retention 窗口裁剪（max_rows / max_months / both）

### 数据库

| 数据库 | 用途 | 部署方式 |
|--------|------|----------|
| `rollerbed_tracking_db` | 车辆位置状态（主库） | Docker `postgres` 或 Windows PostgreSQL |
| `defect_db` | 缺陷汇总 + ETL 状态 | 本地 PostgreSQL |
| `analytics_db` | 跨库分析层（ODS/DIM/FCT/MART） | 通过 FDW 从以上两库导入 |

### 配置文件

- `.env` — 所有连接参数和环境变量（从 `.env_example` 复制）
- `deviceConfig.json` — 98 个 RB 位置、8 个工艺区域、35 个 PLC 设备配置
- `seed_data.json` — `process_areas` 和 `carrier_types` 字典表种子数据

## 项目约定

- Conda 环境名：`websoket`（Python 3.10+）
- 修改文件时注明修改时间，重要变更记录到 `changelog.md`
- 新特性/重要优化记录到 `changelog.md`，README 记录项目特性和结构变更
- 新增依赖必须更新 `requirements.txt`
- 项目长期约定、术语、背景维护在 `memory.md`
- 协作规则补充在 `AGENTS.md`
- 优先最小改动，不随意大范围重构
