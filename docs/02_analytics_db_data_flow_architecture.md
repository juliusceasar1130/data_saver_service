# Analytics DB 数据链路与刷新机制

修改时间：2026-08-27 Asia/Shanghai

主要修改内容：
- **对齐实际数据库（2026-08-27 通过 pg MCP 直连实时 `analytics_db` 校验）**：补充遗漏的第四条数据路径 `project_vehicle_db → FDW(src_project_vehicle) → ods.ods_fis_project_vehicle_orders`（第 1 节概览表由“3 个库”改为“4 个库”，第 2 节新增路径 4，第 5 节 Schema 树补 `src_project_vehicle` 与 `ods.ods_fis_project_vehicle_orders`）；修正 `meta.refresh_analytics_all()` 流程描述（TRUNCATE 8 张 ods、补 FIS UPSERT 与 `CALL refresh_carbody_dim()`、补首次 `mart_vehicle_quality_360` 刷新、`dim_vehicle_profile` 改为三源并集 `tracking ∪ defect ∪ carbody`、标注 `mart_vehicle_quality_360` 双刷）；将过时的“98 行固定位置”更新为实际行数（当前 2748 行）。
- **修正第 1 节部署方式与补 defect SQL Server 源（2026-08-27 补充校验）**：经 `docker ps` 与 `inet_server_addr()`（=172.24.0.2）确认，`defect_db` / `project_vehicle_db` / `analytics_db` 实际均与 `rollerbed_tracking_db` 同处一个 Docker 容器 `120JPH_postgres`（postgres:17-alpine），原“宿主机 PostgreSQL”标注有误，统一更正为 Docker 容器；补列缺陷检测 SQL Server 源 `DENTCHECK`（`defect_db` 的上游源），外部 SQL Server 源由 1 个改为 2 个。

历史修改时间：2026-07-04 Asia/Shanghai

历史修改内容：
- **修正 DIM 刷新描述**：修正了 `dim.dim_process_area` 和 `dim.dim_vehicle_profile` 刷新逻辑的文字描述，将其从误导性的“增量 UPSERT 逻辑”更正为真实的“全量重算覆盖”。


说明：本文档梳理 `analytics_db` 的四条数据来源路径、FDW 外部表机制、Python ETL 直连、存储过程刷新流程以及统一调度器编排，作为数仓架构的入口参考。

> 前置阅读：`docs/00_analytics_db_architecture.md` 是完整的 DDL 与部署操作手册，本文档聚焦链路架构与机制原理。

## 1. 四库概览

项目涉及 4 个独立的 PostgreSQL 数据库 + 2 个外部 SQL Server 源：

| 数据库 | 职责 | 部署方式 |
|--------|------|----------|
| `rollerbed_tracking_db` | 实时车辆位置追踪（位置主表，当前 2748 行，高频 UPDATE） | Docker 容器 `120JPH_postgres` (postgres:17-alpine) |
| `defect_db` | 缺陷检测汇总（`history_station_defect_summary` 宽表，源自 SQL Server `DENTCHECK`） | Docker 容器 `120JPH_postgres` (postgres:17-alpine) |
| `project_vehicle_db` | FIS 项目车生产订单明细（`project_vehicle_orders`，当前 332 行） | Docker 容器 `120JPH_postgres` (postgres:17-alpine) |
| `analytics_db` | 分析数仓，整合上述三库 + 车身历史，供 LLM 查询 | Docker 容器 `120JPH_postgres` (postgres:17-alpine) |
| SQL Server `DXQcontrol_SVWMEB_BI_DWH` | 车身过站历史源库（MES 系统，carbody 源） | 外部 Windows SQL Server |
| SQL Server `DENTCHECK` | 缺陷检测源库（`defect_db` 的上游） | 外部 Windows SQL Server |

## 2. 四条数据路径汇入 analytics_db

```
                        ┌──────────────────────────────────────────────────┐
                        │              analytics_db (分析数仓)               │
                        │                                                  │
rollerbed_tracking_db ──┤  路径1: FDW ──→ src_rb.* ──→ ods.rb_position_data  │
(PostgreSQL)            │               (6 张表)         + 5 张字典表       │
                        │                                                  │
defect_db ──────────────┤  路径2: FDW ──→ src_defect.* ──→ ods.history_     │
(PostgreSQL)            │               (1 张表)          station_defect_   │
                        │                                  summary          │
                        │                                                  │
SQL Server MES ─────────┤  路径3: Python ETL ──→ ods.carbody_history        │
(DXQcontrol_SVWMEB...)  │  (pytds 直连, 非 FDW)                            │
                        │                                                  │
project_vehicle_db ─────┤  路径4: FDW ──→ src_project_vehicle.*            │
(PostgreSQL)            │               (1 张表: project_vehicle_orders)    │
                        │               → ods.ods_fis_project_vehicle_orders│
                        │                                                  │
                        │  ──→ dim.* (聚合维表)                            │
                        │  ──→ fct.* (物化视图)                            │
                        │  ──→ mart.* (分析宽表)                           │
                        └──────────────────────────────────────────────────┘
```

### 2.1 路径 1：rollerbed_tracking_db → FDW

`analytics_db` 通过 `postgres_fdw` 扩展挂载 `rollerbed_tracking_db`，将 6 张源表映射到 `src_rb` schema：

```sql
CREATE SERVER rollerbed_srv FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', dbname 'rollerbed_tracking_db', port '5432');

CREATE USER MAPPING FOR root SERVER rollerbed_srv
OPTIONS (user 'root', password 'root');

IMPORT FOREIGN SCHEMA public
LIMIT TO (
  rb_position_data,        -- 实时位置主表（当前 2748 行）
  process_areas,           -- 工艺区域字典
  carrier_types,           -- 载体类型字典
  vehicle_body_types,      -- 车型字典（自动发现）
  vehicle_color_codes,     -- 颜色代码字典（自动发现）
  vehicle_platforms        -- 平台字典（自动发现）
)
FROM SERVER rollerbed_srv INTO src_rb;
```

FDW 外部表的本质：查询 `src_rb.*` 时，PostgreSQL 通过网络实时转发 SQL 到源库执行，**不存储本地副本**。`analytics_db` 中的本地副本来自下一步的 `ods.*` 表。

### 2.2 路径 2：defect_db → FDW

同理，`defect_db` 通过 FDW 将缺陷汇总表映射到 `src_defect` schema：

```sql
CREATE SERVER defect_srv FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', dbname 'defect_db', port '5432');

CREATE USER MAPPING FOR root SERVER defect_srv
OPTIONS (user 'root', password 'root');

IMPORT FOREIGN SCHEMA public
LIMIT TO (history_station_defect_summary)
FROM SERVER defect_srv INTO src_defect;
```

### 2.3 路径 3：Carbody → Python ETL 直连

Carbody（车身过站历史）的数据来源是 **SQL Server**（非 PostgreSQL），无法使用 `postgres_fdw`。最初也曾尝试过通过另一台 PostgreSQL 中转（`carbody_srv` FDW），但在 2026-05-16 重构中已**彻底废弃 FDW 方式**，改为 Python 脚本直连：

```
SQL Server (pytds) ──→ Python refresh_carbody_ods.py ──→ ods.carbody_history (psycopg2)
```

**为什么不用 FDW？**
- FDW 跨数据库转发对异构数据库（SQL Server）不适用（`postgres_fdw` 仅支持 PG ↔ PG）
- Python ETL 可直接控制批量大小、事务边界、水位推进，更灵活可观测
- 避免了网络跳转（PG → FDW → SQL Server）带来的延迟和不稳定性

Python ETL 脚本：`carbody_etl/refresh_carbody_ods.py`
- 源端：`pytds.connect()` 直连 SQL Server，执行 `SELECT * FROM dwh.MDS_HISTORIC WHERE ID > %s`
- 目标端：`psycopg2` 连接 `analytics_db`，`INSERT INTO ods.carbody_history`
- 每批次在同一事务内完成 ODS 写入 + 水位更新（Atomic Sync）
- 完成后自动调用 `CALL meta.refresh_carbody_dim()` 触发 DIM 聚合

### 2.4 路径 4：project_vehicle_db → FDW

`project_vehicle_db` 通过 FDW 将 FIS 项目车生产订单明细表映射到 `src_project_vehicle` schema（2026-07-28 新增链路）：

```sql
CREATE SERVER project_vehicle_srv FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', dbname 'project_vehicle_db', port '5432');

CREATE USER MAPPING FOR root SERVER project_vehicle_srv
OPTIONS (user 'root', password 'root');

IMPORT FOREIGN SCHEMA public
LIMIT TO (project_vehicle_orders)
FROM SERVER project_vehicle_srv INTO src_project_vehicle;
```

该路径与路径 1/2 一样采用 FDW 实时映射 + 本地 ODS 物理副本（`ods.ods_fis_project_vehicle_orders`，主键 `project_vehicle_no`，含 13 位合成 PIN `composite_pin_no` 专属 B-Tree 索引）。区别在于：FIS 数据同步发生在 `meta.refresh_carbody_dim()` 与 `meta.refresh_analytics_all()` 内部，通过 `INSERT ... ON CONFLICT (project_vehicle_no) DO UPDATE`（UPSERT）方式写入，而非 TRUNCATE + 全量 INSERT。其 `composite_pin_no` 用于与滚床 `vehicle_id` 前 13 位精确匹配，识别项目车（`entity_type = 'project_vehicle'`，优先级最高）。

## 3. refresh_analytics_all() 刷新流程

`meta.refresh_analytics_all()` 是 `analytics_db` 的核心刷新存储过程，由统一调度器每 N 分钟调用一次。其执行顺序如下：

```
┌─────────────────────────────────────────────────────┐
│          meta.refresh_analytics_all()                 │
├─────────────────────────────────────────────────────┤
│ 1. 记录 job_log (running / start)                    │
│                                                      │
│ 2. TRUNCATE ods.* (8 张表) + dim.* (2 张表)          │
│    ├─ ods.process_areas                              │
│    ├─ ods.carrier_types                              │
│    ├─ ods.vehicle_body_types                         │
│    ├─ ods.vehicle_color_codes                        │
│    ├─ ods.vehicle_platforms                          │
│    ├─ ods.rb_position_data                           │
│    ├─ ods.history_station_defect_summary             │
│    ├─ ods.ods_fis_project_vehicle_orders             │
│    ├─ dim.dim_process_area                           │
│    └─ dim.dim_vehicle_profile                        │
│                                                      │
│ 3. INSERT INTO ods.* ← SELECT FROM src_rb.* (FDW)    │
│    INSERT INTO ods.* ← SELECT FROM src_defect.* (FDW) │
│    UPSERT ods.ods_fis_project_vehicle_orders         │
│      ← SELECT FROM src_project_vehicle.* (FDW)       │
│    (全量快照，从 FDW 实时拉取源库当前数据)            │
│                                                      │
│ 4. CALL meta.refresh_carbody_dim()                    │
│    (内部: FIS UPSERT + carbody_registry UPSERT       │
│     + project_vehicle_no 13 位精确匹配)              │
│                                                      │
│ 5. REFRESH MATERIALIZED VIEW fct.* (5 个)             │
│    ├─ fct_position_current_all       (全量占位)      │
│    ├─ fct_vehicle_position_current   (正式产品车)    │
│    ├─ fct_vehicle_defect_detection   (缺陷事件)      │
│    ├─ fct_vehicle_defect_enriched    (车身+缺陷宽表) │
│    └─ fct_abnormal_vehicle_current   (异常车)        │
│                                                      │
│ 6. REFRESH mart.mart_vehicle_quality_360 (第 1 次)    │
│    (在 DIM 重建前先刷一次，供下游 dim 读取)          │
│                                                      │
│ 7. INSERT INTO dim.* (全量重算覆盖)                  │
│    ├─ dim.dim_process_area (从 ods 聚合)             │
│    └─ dim.dim_vehicle_profile                        │
│       (tracking ∪ defect ∪ carbody 三源并集)        │
│                                                      │
│ 8. REFRESH MATERIALIZED VIEW mart.* (3 个)            │
│    ├─ mart_vehicle_quality_360      (第 2 次刷新)    │
│    ├─ mart_abnormal_vehicle_current (异常车汇总)     │
│    └─ mart_position_current_overview(占位总览)      │
│                                                      │
│ 9. UPSERT meta.refresh_watermark (水位快照)          │
│                                                      │
│ 10. GRANT SELECT ON ALL TABLES TO agent_ro           │
│                                                      │
│ 11. UPDATE job_log → 'success'                       │
└─────────────────────────────────────────────────────┘
```

**关键设计决策：**

- **ODS 采用全量 TRUNCATE + INSERT**（非增量）。因为 `rollerbed_tracking_db` 的 `rb_position_data` 当前 2748 行 + 少量字典表，全量拉取成本极低。`defect_db` 的缺陷汇总表行数较大（~5 万行），但每次全量刷新可接受。`project_vehicle_db` 的 `project_vehicle_orders`（332 行）采用 UPSERT 而非 TRUNCATE，以保留 `project_vehicle_no` 主键稳定。
- **`ods.carbody_history` 不参与 TRUNCATE**。它是 Python ETL 增量追加写入的，`refresh_analytics_all()` 不触碰它。
- **DIM 层在 FCT 之后重建**。因为 `dim.dim_vehicle_profile` 依赖 `fct.fct_vehicle_position_current` 的物化结果（当前车辆位置快照），所以必须等 FCT 刷新完再填充 DIM。需要注意的是，这里的 dim 表在刷新过程中是被 `TRUNCATE` 后全量写入（INSERT），并非增量更新。
- **`mart.mart_vehicle_quality_360` 被刷新两次**。第一次在 DIM 重建前（基于上一轮 carbody/defect 数据），第二次在 DIM 重建后（基于最新三源合并画像），确保最终结果反映 `tracking ∪ defect ∪ carbody` 合并后的画像。
- **MART 在 DIM 之后刷新**。`mart.mart_vehicle_quality_360` 等汇总视图依赖 DIM 层的聚合结果。

## 4. 统一调度器编排

`scheduler/scheduler_main.py` 是 Docker 常驻进程，按 `SCHEDULER_INTERVAL_MINUTES`（默认 3 分钟）串行执行三条链路：

```
┌──────────────────────────────────────────────────────┐
│            scheduler_main.py (每 3 分钟)               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Step 1: Carbody ETL                                 │
│  ┌──────────────────────────────────────────────┐   │
│  │ subprocess: refresh_carbody_ods.py            │   │
│  │ SQL Server → pytds → ods.carbody_history      │   │
│  │ → CALL meta.refresh_carbody_dim()             │   │
│  │ → REFRESH fct.fct_vehicle_defect_enriched     │   │
│  │ Lock Key: 20260515                            │   │
│  └──────────────────────────────────────────────┘   │
│           ↓                                          │
│  Step 2: Defect Summary ETL                          │
│  ┌──────────────────────────────────────────────┐   │
│  │ subprocess: refresh_history_station_defect_   │   │
│  │             summary.py --refresh              │   │
│  │ SQL Server → pytds → defect_db (UPSERT)       │   │
│  │ Lock Key: 20260413                            │   │
│  └──────────────────────────────────────────────┘   │
│           ↓                                          │
│  Step 3: Analytics All Refresh                       │
│  ┌──────────────────────────────────────────────┐   │
│  │ psycopg2 直连: CALL meta.refresh_analytics_   │   │
│  │                all()                          │   │
│  │ FDW 全量拉取 + REFRESH MV + DIM 重建          │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  全局锁 IS_RUNNING 防止叠跑                          │
│  健康检查文件 /tmp/scheduler_health                   │
└──────────────────────────────────────────────────────┘
```

**执行顺序的必要性：**

1. **Carbody ETL 先执行** — 写入 `ods.carbody_history` 并更新 `dim.carbody_registry`，调用 `REFRESH fct.fct_vehicle_defect_enriched`（该视图依赖 carbody 数据）。
2. **Defect ETL 次之** — 将最新的缺陷检测数据写入 `defect_db.history_station_defect_summary`，为下一步 FDW 拉取做准备。
3. **Analytics All Refresh 最后** — 通过 FDW 从 `rollerbed_tracking_db` 和 `defect_db` 全量拉取最新快照，刷新所有物化视图和 DIM/MART 层。

**并发控制：**

每个 ETL 脚本各自使用 PostgreSQL Advisory Lock 防止重复执行：
- Carbody ETL: lock key `20260515`
- Defect ETL: lock key `20260413`
- Scheduler 本身: 全局 `IS_RUNNING` 标志位防止叠跑

## 5. Schema 分层架构

```
analytics_db
├── src_rb               ← FDW 外部表 (rollerbed_tracking_db 的实时映射)
├── src_defect           ← FDW 外部表 (defect_db 的实时映射)
├── src_project_vehicle  ← FDW 外部表 (project_vehicle_db 的实时映射)
├── ods                  ← 本地操作数据存储 (TRUNCATE + 全量 INSERT)
│   ├── rb_position_data, process_areas, carrier_types,
│   │   vehicle_body_types, vehicle_color_codes, vehicle_platforms
│   ├── history_station_defect_summary
│   ├── ods_fis_project_vehicle_orders (FIS 项目车订单, UPSERT 同步)
│   └── carbody_history (Python ETL 增量追加, 不参与 TRUNCATE)
├── dim                  ← 维表 (在 FCT 之后重建)
│   ├── dim_process_area
│   ├── dim_vehicle_profile (tracking ∪ defect ∪ carbody 三源并集)
│   └── carbody_registry (Python ETL 触发 refresh_carbody_dim 维护)
├── fct                  ← 事实层物化视图
│   ├── fct_position_current_all (全量占位)
│   ├── fct_vehicle_position_current (正式产品车)
│   ├── fct_abnormal_vehicle_current (异常车)
│   ├── fct_vehicle_defect_detection (缺陷事件)
│   └── fct_vehicle_defect_enriched (车身+缺陷富集宽表)
├── mart                 ← 分析汇总层物化视图
│   ├── mart_vehicle_quality_360
│   ├── mart_abnormal_vehicle_current
│   └── mart_position_current_overview
└── meta                 ← ETL 元数据
    ├── sync_job_log (作业执行日志)
    └── refresh_watermark (水位快照)
```

## 6. 两种刷新模式对比

| 维度 | FDW 路径 (rb / defect / project_vehicle) | Python ETL 路径 (carbody) |
|------|------------------------------------------|---------------------------|
| **源库类型** | PostgreSQL | SQL Server |
| **连接方式** | `postgres_fdw` 外部表 | `pytds` Python 驱动直连 |
| **写入方式** | TRUNCATE + 全量 INSERT | 增量追加 (WHERE ID > watermark) |
| **触发时机** | `refresh_analytics_all()` 内部 | `scheduler` subprocess 独立执行 |
| **频率** | 每 3 分钟全量快照 | 每 3 分钟增量同步 |
| **数据量** | 2748 行 (rb) + ~5 万行 (defect) + 332 行 (project_vehicle) | 依赖源库增量 |
| **事务策略** | 存储过程内多语句事务 | Python 批量事务 (Atomic Sync) |
| **并发控制** | 依赖调度器 IS_RUNNING | Advisory Lock + 调度器 IS_RUNNING |

## 7. 关键环境变量

| 变量组 | 用途 |
|--------|------|
| `DB_*` | `rollerbed_tracking_db` 连接参数 |
| `CARBODY_SOURCE_DB_*` | Carbody SQL Server 源库连接 |
| `CARBODY_TARGET_DB_*` | Carbody 目标库连接（指向 `analytics_db`） |
| `DEFECT_SOURCE_DB_*` | 缺陷源库连接（支持 `postgres` / `sqlserver`） |
| `DEFECT_TARGET_DB_*` | 缺陷目标库连接（指向 `defect_db`） |
| `SCHEDULER_INTERVAL_MINUTES` | 调度器执行间隔（默认 3） |
