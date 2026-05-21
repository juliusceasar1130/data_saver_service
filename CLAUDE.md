# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

汽车涂装车间工业数据系统，包含三大子系统：

- **实时车辆追踪** (`rollerbed_tracking_db`)：通过 WebSocket 从 PLC 采集 BodyID/CarrierID，写入 PostgreSQL
- **分析数仓 ETL 三链路** (驻留在 `analytics_db`)：
  1. **Carbody ODS 同步** (`carbody_etl/`)：从 SQL Server 源库增量抽取过站历史到 `ods.carbody_history`，聚合至 `dim.carbody_registry`
  2. **缺陷汇总 ETL** (`defect_summary_etl/`)：从 PostgreSQL/SQL Server 源库增量抽取缺陷检测结果，写入 `history_station_defect_summary` 宽表
  3. **分析库聚合** (`meta.refresh_analytics_all()`)：刷新物化视图和 FCT 层，产出最终分析数据
- **统一调度器** (`scheduler/scheduler_main.py`)：常驻 Docker 容器，按可配置间隔（默认 3 分钟）串行执行以上三链路

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

### 数据库初始化

```bash
# 全新部署：执行 DDL 建表
psql -U root -d rollerbed_tracking_db -f create_tables_postgresql.sql

# 初始化 98 个 RB 位置记录（从 deviceConfig.json 读取）
python init_rb_positions_postgresql.py

# 预填充字典表 (process_areas, carrier_types)
python init_seed_data_postgresql.py
```

### Carbody ETL — ODS 同步与维表聚合

```bash
# 首次全量同步或重置（清空数据重头开始）
python carbody_etl/refresh_carbody_ods.py --full-refresh

# 日常增量同步
python carbody_etl/refresh_carbody_ods.py
```

### 缺陷汇总 ETL（`defect_summary_etl/`）

```bash
# 初始化水位（首次使用或切库后执行一次）
python defect_summary_etl/refresh_history_station_defect_summary.py --init-state

# 执行一次增量刷新
python defect_summary_etl/refresh_history_station_defect_summary.py --refresh

# 查看当前水位和状态
python defect_summary_etl/refresh_history_station_defect_summary.py --print-status
```

### 统一调度器

```bash
# 宿主机直接运行（常驻进程，Ctrl+C 停止）
python scheduler/scheduler_main.py

# Docker 容器化部署
docker compose up -d refresh-scheduler
docker compose logs -f refresh-scheduler
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
                ↓
          ┌──────────────────────────────────────────────────────┐
          │                 scheduler/scheduler_main.py           │
          │   ┌─────────────────┐  ┌───────────────────┐  ┌─────┐ │
          │   │ Carbody ODS ETL │→│ Defect Summary ETL │→│ DB  │ │
          │   │ (carbody_etl/)  │ │ (defect_summary_etl/)││CALL │ │
          │   └─────────────────┘  └───────────────────┘  └─────┘ │
          └──────────────────────────────────────────────────────┘
                ↓
          analytics_db (PostgreSQL)
          ├── ods.carbody_history         (Carbody 原始过站数据)
          ├── dim.carbody_registry        (一车一行聚合明细)
          ├── public.history_station_defect_summary  (缺陷汇总宽表)
          ├── fct.fct_vehicle_defect_enriched        (关联车辆与缺陷的物化视图)
          └── meta.*                      (水位表、审计日志、聚合存储过程)
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

**`carbody_etl/refresh_carbody_ods.py`** — Carbody ODS 增量同步：
- 从 SQL Server `DXQcontrol_SVWMEB_BI_DWH` 流式分批抽取增量数据
- 同一事务内完成 PostgreSQL `ods.carbody_history` 写入与水位更新（Atomic Sync）
- 完成后调用存储过程 `meta.refresh_carbody_dim()` 聚合 DIM 层
- 基于 PostgreSQL Advisory Lock 并发控制

**`defect_summary_etl/refresh_history_station_defect_summary.py`** — 缺陷汇总增量刷新：
- "双连接、单次执行、增量落库" 模式：目标固定写本地 `analytics_db`，源可选 PostgreSQL/SQL Server
- 水位推进 + replay window：覆盖晚到的缺陷数据，通过 `UPSERT` 幂等写入
- PostgreSQL advisory lock 并发控制，状态表 + 日志表追踪执行历史
- 支持 retention 窗口裁剪（max_rows / max_months / both）

**`scheduler/scheduler_main.py`** — 统一常驻调度器：
- 基于 `schedule` 库，通过 `SCHEDULER_INTERVAL_MINUTES` 环境变量配置间隔（默认 3 分钟）
- 串行执行三链路：Carbody ETL → Defect Summary ETL → `CALL meta.refresh_analytics_all()`
- 全局锁 `IS_RUNNING` 防止叠跑，健康检查文件 `/tmp/scheduler_health` 供容器监控
- Docker 容器化部署（`Dockerfile.scheduler`），自动继承 `.env` 配置

### 数据库

| 数据库 | 用途 | 部署方式 |
|--------|------|----------|
| `rollerbed_tracking_db` | 车辆位置实时状态（主库） | Docker `postgres` 或 Windows PostgreSQL |
| `analytics_db` | 分析数仓，含 ODS/DIM/FCT/MART 层及 ETL 元数据表 | 本地 PostgreSQL（Docker 或 Windows） |

注：`defect_db` 已合并至 `analytics_db`，不再独立存在。`analytics_db` 通过 ETL 脚本直写（非 FDW）完成数据整合。

### 环境变量分组

`.env` 中的环境变量按职责分为以下组：

| 前缀 / 分组 | 用途 |
|-------------|------|
| `DB_*` | rollerbed_tracking_db 连接参数（Docker 内部服务默认） |
| `CARBODY_SOURCE_DB_*` | Carbody SQL Server 源库连接 |
| `CARBODY_TARGET_DB_*` | Carbody PostgreSQL 目标库连接（默认指向 analytics_db） |
| `DEFECT_SOURCE_DB_*` | 缺陷源库连接（支持 postgres / sqlserver） |
| `DEFECT_TARGET_DB_*` | 缺陷目标库连接（默认指向 analytics_db） |
| `DEFECT_SUMMARY_*` | 缺陷 ETL 批大小、replay window、retention 策略 |
| `SCHEDULER_INTERVAL_MINUTES` | 调度器执行间隔（默认 3 分钟） |
| `WS_*` | WebSocket 服务器连接参数 |

### 配置文件

- `.env` — 所有连接参数和环境变量（从 `.env_example` 复制）
- `deviceConfig.json` — 98 个 RB 位置、8 个工艺区域、35 个 PLC 设备配置
- `seed_data.json` — `process_areas` 和 `carrier_types` 字典表种子数据
- `defect_summary_etl/model_map.json` — 车型编号 → type_name / black_roof 静态映射

## 项目约定

- Conda 环境名：`websoket`（Python 3.10+）
- 修改文件时注明修改时间，重要变更记录到 `changelog.md`
- 新特性/重要优化记录到 `changelog.md`，README 记录项目特性和结构变更
- 新增依赖必须更新 `requirements.txt`
- 项目长期约定、术语、背景维护在 `memory.md`
- 协作规则补充在 `AGENTS.md`
- 优先最小改动，不随意大范围重构
