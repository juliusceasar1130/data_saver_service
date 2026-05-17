# carbody_history 源库迁移方案：PostgreSQL → SQL Server

修改时间：2026-05-16 Asia/Shanghai

## 目录

- [1. 变更概述](#1-变更概述)
- [2. 现状分析](#2-现状分析)
  - [2.1 当前架构](#21-当前架构)
  - [2.2 src_carbody.carbody_history 完整引用链](#22-src_carbodycarbody_history-完整引用链)
  - [2.3 当前增量刷新机制](#23-当前增量刷新机制)
  - [2.4 受影响对象清单](#24-受影响对象清单)
- [3. 方案选型](#3-方案选型)
  - [3.1 方案 A：tds_fdw 替代 postgres_fdw](#31-方案-atds_fdw-替代-postgres_fdw)
  - [3.2 方案 B：纯 Python ETL](#32-方案-b纯-python-etl)
  - [3.3 方案 C：Python 负责 ODS 抽取 + PostgreSQL 存储过程负责 DIM 转换](#33-方案-cpython-负责-ods-抽取--postgresql-存储过程负责-dim-转换)
  - [3.4 选型结论](#34-选型结论)
- [4. 详细设计](#4-详细设计)
  - [4.1 目标架构](#41-目标架构)
  - [4.2 Python 脚本设计](#42-python-脚本设计)
  - [4.3 存储过程裁减](#43-存储过程裁减)
  - [4.4 数据类型映射](#44-数据类型映射)
  - [4.5 配置文件变更](#45-配置文件变更)
  - [4.6 调度设计](#46-调度设计)
- [5. 迁移步骤](#5-迁移步骤)
- [6. 验收标准](#6-验收标准)
- [7. 风险与回退](#7-风险与回退)
  - [7.1 风险清单](#71-风险清单)
  - [7.2 回退方案](#72-回退方案)
- [附录 A：Python 脚本伪代码](#附录-apython-脚本伪代码)
- [附录 B：裁减后存储过程完整 SQL](#附录-b裁减后存储过程完整-sql)
- [附录 C：SQL Server 侧需确认项](#附录-csql-server-侧需确认项)

---

## 1. 变更概述

| 项目 | 说明 |
|------|------|
| **变更类型** | 基础设施迁移 |
| **影响范围** | `analytics_db` 中 carbody 数据管道的上游抽取层 |
| **非影响范围** | `ods.rb_position_data`、`ods.history_station_defect_summary` 及所有非 carbody 的 dim/fct/mart 对象 |
| **动机** | 上游 `carbody_history` 数据库已从 PostgreSQL 迁移至 SQL Server `DXQcontrol_SVWMEB_BI_DWH`，原有的 `postgres_fdw` 连接不再可用 |
| **约束** | 下游 `dim.carbody_registry` → `fct.fct_vehicle_defect_enriched` 的 SQL 转换逻辑不应有任何语义变更 |

---

## 2. 现状分析

### 2.1 当前架构

```
carbody_history (PostgreSQL 独立库, dbname=carbody_history)
    │  postgres_fdw: carbody_srv
    │  IMPORT FOREIGN SCHEMA public LIMIT TO (carbody_history) INTO src_carbody
    ▼
src_carbody.carbody_history  ← FDW 外部表（只读，无下游直接引用）
    │
    │  ┌─────────────────────────────────────────────┐
    │  │  meta.refresh_carbody()                     │
    │  │  1. 读水位 max("ID")                        │
    │  │  2. INSERT INTO ods.carbody_history          │
    │  │     SELECT * FROM src_carbody.carbody_history │
    │  │     WHERE "ID" > v_last_id                   │
    │  │  3. vehicle_agg + last_mds CTE → UPSERT      │
    │  │  4. 更新水位                                 │
    │  └─────────────────────────────────────────────┘
    ▼
ods.carbody_history  ← ODS 本地缓存表（增量 INSERT，不 TRUNCATE）
    │  主键: "ID"
    │  索引: "BODY_ID", "DATE_EVT", ("BODY_ID","DATE_EVT"), "RW_STATION_ID"
    ▼
dim.carbody_registry  ← 维度表（增量 UPSERT，每车一行）
    │  主键: vehicle_id
    │  过滤: "BODY_ID" LIKE '78%'
    ▼
fct.fct_vehicle_defect_enriched  ← 物化视图（LEFT JOIN 驱动表）
    │  FROM dim.carbody_registry
    │  LEFT JOIN ods.history_station_defect_summary
    ▼
  (供 SQL Agent 查询)
```

### 2.2 src_carbody.carbody_history 完整引用链

#### 上游（数据来源）

| 层级 | 对象 | 说明 |
|------|------|------|
| 外部源库 | `carbody_history` 数据库 | PostgreSQL 独立库，存储车身过站历史 |
| FDW Server | `carbody_srv` | `postgres_fdw`，指向 `localhost:5432`，`dbname=carbody_history` |
| User Mapping | `root` → `carbody_srv` | 用 `root/root` 认证 |
| FDW 外部表 | `src_carbody.carbody_history` | `IMPORT FOREIGN SCHEMA public LIMIT TO (carbody_history)` 导入 |

#### 下游（数据消费）

| 层级 | 对象 | 消费方式 | 依赖字段 |
|------|------|----------|----------|
| **ODS** | `ods.carbody_history` | `INSERT INTO ... SELECT * FROM src_carbody.carbody_history WHERE "ID" > v_last_id` | 全部 17 个字段 |
| **DIM** | `dim.carbody_registry` | 聚合自 `ods.carbody_history`：`vehicle_agg` CTE（group by `"BODY_ID"`）+ `last_mds` CTE（`DISTINCT ON "BODY_ID"` 取末条 `MDS_DATA` substring）| `"ID"`, `"BODY_ID"`, `"DATE_EVT"`, `"RW_STATION_ID"`, `"BODY_TYPE"`, `"MDS_DATA"` |
| **FCT** | `fct.fct_vehicle_defect_enriched` | `FROM dim.carbody_registry LEFT JOIN ods.history_station_defect_summary` | `vehicle_id`, `body_type`, `platform_code`, `color_code`, `black_roof_flag`, `rework_flag`, `reserved_1`, `reserved_2`, `first_seen_at`, `last_seen_at`, `first_rw_station`, `last_rw_station`, `first_body_type`, `last_body_type`, `station_pass_count` |
| **META** | `meta.refresh_watermark` | 写入两条水位记录 | `ods.carbody_history.max_id`, `dim.carbody_registry.last_sync_at` |
| **META** | `meta.sync_job_log` | `refresh_carbody()` 执行日志 | `job_name='refresh_carbody'` |

#### 引用关系图

```
carbody_history (ext PG)
 └── src_carbody.carbody_history ──[无上游引用]──[无下游引用，仅被 refresh_carbody() 消费]
      └── ods.carbody_history ────[被 dim.carbody_registry 引用]
           └── dim.carbody_registry ────[被 fct.fct_vehicle_defect_enriched 引用]
                └── fct.fct_vehicle_defect_enriched ────[终端查询入口，无下游引用]
```

### 2.3 当前增量刷新机制

**过程**：`meta.refresh_carbody()`

| 步骤 | SQL 操作 | 说明 |
|------|----------|------|
| 1. 读水位 | `SELECT watermark_value FROM meta.refresh_watermark WHERE source_name='ods.carbody_history.max_id'` | 上次同步的最大 `"ID"` |
| 2. ODS 增量 | `INSERT INTO ods.carbody_history SELECT * FROM src_carbody.carbody_history WHERE "ID" > v_last_id` | 纯增量，不 TRUNCATE |
| 3. DIM UPSERT | `WITH new_records AS (...WHERE "ID" > v_last_id AND "BODY_ID" LIKE '78%'...), vehicle_agg AS (...GROUP BY "BODY_ID"...), last_mds AS (...DISTINCT ON "BODY_ID"...ORDER BY "DATE_EVT" DESC...) INSERT INTO dim.carbody_registry ... ON CONFLICT DO UPDATE` | 增量批次聚合 + 幂等写入 |
| 4. 水位更新 | `UPSERT meta.refresh_watermark` | 更新 `max_id` 和 `last_sync_at` |
| 5. 权限 | `GRANT SELECT ON ... TO agent_ro` | 增量对象授权 |

**UPSERT 语义**：

| 字段 | 新车 (INSERT) | 已有车 (UPDATE) |
|------|---------------|-----------------|
| `vehicle_id` | 写入 | 不变（PK） |
| `first_seen_at` / `first_rw_station` / `first_body_type` | 写入 | **不更新** |
| `last_seen_at` / `last_rw_station` / `last_body_type` | 写入 | **覆盖** |
| `station_pass_count` | 写入 | **累加** (old + new) |
| MDS 7 字段 (`body_type/platform_code/color_code/black_roof_flag/rework_flag/reserved_1/reserved_2`) | 写入（末次 MDS_DATA） | **覆盖** |

**每周兜底**：重置水位为 `'0'` + TRUNCATE ODS + TRUNCATE DIM + `CALL meta.refresh_carbody()`（等价全量重刷，清理源库已滚动删除的过期行）

### 2.4 受影响对象清单

| 对象 | 当前状态 | 迁移后 | 影响类型 |
|------|----------|--------|----------|
| `carbody_srv` FDW server | `postgres_fdw` 指向 PostgreSQL | **废弃** | 删除 |
| `src_carbody.carbody_history` | FDW 外部表 | **废弃**（可保留以便回退） | 删除 |
| `ods.carbody_history` | 本地缓存表 | 不变（表结构、PK、索引保留） | 无变更 |
| `meta.refresh_carbody()` | ODS INSERT + DIM UPSERT | 裁减为 `meta.refresh_carbody_dim()`，仅含 DIM UPSERT | 修改 |
| `meta.refresh_watermark` | `ods.carbody_history.max_id` | 不变 | 无变更 |
| `dim.carbody_registry` | 维度表 | 不变 | 无变更 |
| `fct.fct_vehicle_defect_enriched` | 物化视图 | 不变 | 无变更 |
| `meta.refresh_analytics_all()` | 主刷新过程 | 不变（不涉及 carbody） | 无变更 |
| `.env` | 环境变量 | 新增 SQL Server 源库连接参数 | 新增配置 |
| `requirements.txt` | 依赖清单 | 不变（`python-tds` 已存在） | 无变更 |

---

## 3. 方案选型

### 3.1 方案 A：tds_fdw 替代 postgres_fdw

用 PostgreSQL 的 `tds_fdw` 扩展替代 `postgres_fdw`，使 `src_carbody.carbody_history` 继续作为 FDW 外部表，下游 SQL 基本不变。

**优势**：
- `refresh_carbody()` 存储过程代码改动最小（只改 FDW server 定义）
- 保持 SQL-only 架构

**劣势**：
- `tds_fdw` 在 Windows PostgreSQL 上安装复杂，需编译 FreeTDS
- `tds_fdw` 对 quoted identifier（`"ID"`, `"BODY_ID"` 等）的支持不确定
- 社区活跃度和稳定性远低于 `postgres_fdw`
- 需同时维护 `postgres_fdw` 和 `tds_fdw` 两套 FDW 扩展
- 数据类型映射（SQL Server `datetime2`→PostgreSQL `timestamp`）在大数据量下的性能未验证

**风险等级**：高

### 3.2 方案 B：纯 Python ETL

新建 Python 脚本完全替代 `meta.refresh_carbody()` 存储过程，负责 ODS 抽取和 DIM 转换的全部逻辑。

**优势**：
- 项目已有成熟的 `python-tds` (pytds) 连接模式，经 `refresh_history_station_defect_summary.py` 验证
- Python 中可灵活处理数据类型映射、异常重试、日志
- 不依赖 FDW 扩展

**劣势**：
- `vehicle_agg` 和 `last_mds` 的 CTE 聚合逻辑需用 Python 重写（`GROUP BY` + `array_agg` + `DISTINCT ON` + `substring`），代码量较大
- UPSERT 语义（`ON CONFLICT DO UPDATE` + `first_*` 保留/`last_*` 覆盖/`station_pass_count` 累加）在 Python 中实现复杂且容易出错
- 弃用已验证的 PostgreSQL 存储过程，引入新的 bug 风险

**风险等级**：中

### 3.3 方案 C：Python 负责 ODS 抽取 + PostgreSQL 存储过程负责 DIM 转换（推荐）

Python 脚本仅负责：SQL Server → PostgreSQL 的 ODS 层增量数据搬运。PostgreSQL 存储过程保留 ODS → DIM 的聚合/UPSERT 逻辑。

**优势**：
- 关注点分离：Python 只解决跨数据库传输，PostgreSQL 原生 SQL 处理聚合转换最有效率
- `vehicle_agg` + `last_mds` CTE + UPSERT 逻辑完全保留，零语义变更风险
- Python 端逻辑最少（SELECT→INSERT→更新水位），~150 行可完成
- 可复用项目现有的 `python-tds` 连接模式和 `psycopg2` 连接模式
- carbody 与主刷新 (`refresh_analytics_all()`) 的隔离性不变

**劣势**：
- 刷新逻辑分散在两个组件中（Python 脚本 + 存储过程）
- 需新增一个 Python 脚本文件

**风险等级**：低

### 3.4 选型结论

**选择方案 C**。

关键决策因素：
1. `dim.carbody_registry` 的 UPSERT 语义复杂（`first_*` 保留、`last_*` 覆盖、`station_pass_count` 累加、MDS 覆盖），在 PostgreSQL 存储过程中已验证稳定，重写风险高
2. 下游 `fct.fct_vehicle_defect_enriched` 直接依赖 `dim.carbody_registry`，任何 DIM 数据异常都会传播到 FCT 层
3. 项目已有成熟的 `python-tds` → SQL Server 基础设施（`requirements.txt` 中 `python-tds==1.16.0` 已安装）

---

## 4. 详细设计

### 4.1 目标架构

```
DXQcontrol_SVWMEB_BI_DWH (SQL Server)
    │  python-tds (pytds)
    │  SELECT * FROM dbo.carbody_history WHERE ID > v_last_id
    ▼
┌──────────────────────────────────────────────┐
│  refresh_carbody_ods.py  (新建)              │
│                                              │
│  1. 读 PostgreSQL meta.refresh_watermark     │
│     → ods.carbody_history.max_id             │
│  2. 从 SQL Server 拉增量行                   │
│  3. INSERT INTO ods.carbody_history          │
│  4. CALL meta.refresh_carbody_dim()          │
│  5. 日志记录                                 │
└──────────────────────────────────────────────┘
    │  psycopg2
    ▼
ods.carbody_history  ← 本地缓存（不变）
    │
    │  meta.refresh_carbody_dim() (裁减后)
    │  vehicle_agg CTE + last_mds CTE → UPSERT
    ▼
dim.carbody_registry  ← 维度表（不变）
    │
    │  meta.refresh_analytics_all()
    │  REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched
    ▼
fct.fct_vehicle_defect_enriched  ← 物化视图（不变）
```

### 4.2 Python 脚本设计

**文件路径**：`defect_database/refresh_carbody_ods.py`

**输入**：环境变量（`.env`）

**执行流程**：

```
main()
 ├─ 加载环境变量
 ├─ 获取 advisory lock（防止并发执行）
 ├─ 连接 PostgreSQL 目标库（analytics_db）
 ├─ 连接 SQL Server 源库（DXQcontrol_SVWMEB_BI_DWH）
 ├─ 从 meta.refresh_watermark 读取 v_last_id
 ├─ 分批（流式）从 SQL Server 提取增量行: SELECT * FROM dbo.carbody_history WHERE ID > v_last_id ORDER BY ID
 ├─ 若增量为 0 → 记录日志，释放锁，退出
 ├─ 在同一个 PostgreSQL 事务 (with pg_conn) 中分批执行：
 │   1. 批量写入 ods.carbody_history (execute_values)
 │   2. 更新 meta.refresh_watermark (ods.carbody_history.max_id)
 ├─ 调用 CALL meta.refresh_carbody_dim()
 ├─ 记录 meta.sync_job_log（job_name='refresh_carbody_ods'）
 ├─ 释放 advisory lock
 └─ 异常处理 → 写 sync_job_log 失败记录，抛出含堆栈的错误日志
```

**关键设计决策**：

| 决策点 | 选择 | 理由 |
|--------|------|------|
| SQL Server 查询方式 | `SELECT *` 全列 | 与原有 `SELECT * FROM src_carbody` 语义一致，列变更时自动跟随 |
| ODS 拉取与写入 | `fetchmany()` + `execute_values()` | 流式分批拉取与写入，避免 `fetchall()` 一次性拉取 101 万行导致的 OOM 风险 |
| 事务一致性 | ODS 写入与水位更新在同一事务 | 使用 `with pg_conn`，防止中途崩溃导致的 ODS 数据重复写入（主键冲突） |
| DIM 触发方式 | `CALL meta.refresh_carbody_dim()` | 保持存储过程的原子性，出错时 Python 感知 |
| 并发控制 | PostgreSQL advisory lock (`pg_try_advisory_lock`) | 与 `refresh_history_station_defect_summary.py` 一致 |
| 全量首次导入 | 同脚本，`v_last_id=0` | 不需单独的全量导入脚本 |

**列名映射**：SQL Server `dbo.carbody_history` 的列名（不区分大小写）映射到 PostgreSQL `ods.carbody_history` 的 quoted 列名。Python 通过 `psycopg2.extras.execute_values()` 写入时需显式指定列名列表。

```python
# PostgreSQL ods.carbody_history 的列名（quoted，保证大小写）
ODS_COLUMNS = [
    "ID", "DATE_EVT", "SHIFT_NR", "RW_STATION_ID",
    "RW_STATION_STATUS", "SKID_ID", "SKID_TYPE", "SKID_IS_EMPTY",
    "BODY_ID", "BODY_TYPE", "MDS_DATA", "MDS_TELEGRAM_TYPE",
    "FK_ERP_HIST_ID", "CYCLE_NUM", "PRODUCTION_SEGMENT_ID",
    "ETL_MODIFY_DATE", "ETL_SOURCE_ID",
]
```

### 4.3 存储过程裁减

**当前 `meta.refresh_carbody()` 将被裁减为 `meta.refresh_carbody_dim()`**：

移除的步骤：
- ODS 水位读取（移到 Python）
- `INSERT INTO ods.carbody_history`（移到 Python）
- `ods.carbody_history.max_id` 水位更新（移到 Python）
- 对 `src_carbody` 的权限授权（`src_carbody` 废弃）

保留的步骤：
- `dim.carbody_registry.last_sync_at` 水位更新（保留在存储过程内，与 DIM UPSERT 在同一事务）
- `vehicle_agg` + `last_mds` CTE 聚合（完全不变）
- `ON CONFLICT DO UPDATE` UPSERT（完全不变，语义不移）
- 对 `ods.carbody_history` 和 `dim.carbody_registry` 的权限授权
- `sync_job_log` 写入

**关键变更**：`new_records` CTE 的数据源从 `"ID" > v_last_id` 改为读取最近一批 ODS 数据。简化方案：直接取 ODS 中所有 `"ID" > 上次同步的 DIM max_id`，或直接不筛选增量——每次都对全量 `ods.carbody_history` 跑 UPSERT（`ON CONFLICT` 保证幂等）。鉴于 `ods.carbody_history` 已经是增量插入的表，建议每次只处理最近一次增量批次。

**最终选择**：DIM 刷新时，从 `meta.refresh_watermark` 读取上次 DIM 处理的最大 `"ID"`（即 `dim.carbody_registry.last_sync_id`），仅对增量行做 UPSERT。

详细 SQL 见附录 B。

### 4.4 数据类型映射

| SQL Server 源 | PostgreSQL 目标 (`ods.carbody_history`) | 映射方式 |
|---------------|------------------------------------------|----------|
| `numeric` | `numeric` | `pytds` 返回 Python `Decimal`，`psycopg2` 自动映射 |
| `datetime` / `datetime2` | `timestamp with time zone` (`timestamptz`) | `pytds` 返回无时区的 Python `datetime`。为确保时区一致性，ODS 和 DIM 层均统一使用 `timestamptz`。在建立连接时必须通过 `options="-c timezone=Asia/Shanghai"` 指定会话时区 |
| `varchar(N)` | `varchar` | `pytds` 返回 Python `str`，直接映射 |
| `varchar(MAX)` | `varchar`（`MDS_DATA` 字段） | `pytds` 正确处理长字符串 |

**注意**：PostgreSQL 的 `ods.carbody_history` 使用带引号的大写列名（`"ID"`, `"BODY_ID"` 等）。Python 写入时必须使用双引号包裹列名，避免 PostgreSQL 自动转小写。

### 4.5 配置文件变更

在 `.env` 中新增：

```env
#---------------------------------------------------------carbody_history SQL Server 源库------------------------------
# carbody 过站历史源库（SQL Server）
CARBODY_SOURCE_DB_HOST=172.22.37.52
CARBODY_SOURCE_DB_PORT=1433
CARBODY_SOURCE_DB_NAME=DXQcontrol_SVWMEB_BI_DWH
CARBODY_SOURCE_DB_USER=sa
CARBODY_SOURCE_DB_PASSWORD=          # ← 需填写实际密码
CARBODY_SOURCE_DB_SCHEMA=dwh
CARBODY_SOURCE_TABLE_NAME=MDS_HISTORIC

# carbody PostgreSQL 目标库 (隔离配置)
CARBODY_TARGET_DB_HOST=localhost
CARBODY_TARGET_DB_PORT=5432
CARBODY_TARGET_DB_NAME=analytics_db
CARBODY_TARGET_DB_USER=root
CARBODY_TARGET_DB_PASSWORD=root

# carbody ODS 增量刷新配置
CARBODY_REFRESH_LOCK_KEY=20260515
CARBODY_REFRESH_BATCH_SIZE=5000
CARBODY_REFRESH_LOG_LEVEL=INFO
CARBODY_REFRESH_TIMEZONE=Asia/Shanghai
```

并在 `.env_example` 中增加对应的占位模板。

### 4.6 调度设计

| 任务 | 频率 | 命令 |
|------|------|------|
| **增量刷新** | 每 5 分钟 | `python defect_database/refresh_carbody_ods.py` |
| **每周兜底** | 每周日 03:00 | `python defect_database/refresh_carbody_ods.py --full-refresh` |

`--full-refresh` 参数行为：重置 `ods.carbody_history.max_id` 水位置 `'0'` + TRUNCATE `ods.carbody_history` + 重新全量拉取。
*(注：为避免 `TRUNCATE dim.carbody_registry` 带来的业务查询“真空期”，全量兜底不再清空 DIM 表。全量 ODS 数据拉取后，将通过 `ON CONFLICT DO UPDATE` 对 `dim.carbody_registry` 进行全量覆盖更新，从而保证查询不中断)*

**与主刷新的协调**：carbody 增量刷新独立于 `meta.refresh_analytics_all()`，但 `fct.fct_vehicle_defect_enriched` 的物化视图刷新仍在主刷过程中。因此如果 carbody ODS/DIM 更新后需要立即反映到 FCT，可选择：
- 在 Python 脚本末尾额外执行 `REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched`（需加 `CONCURRENTLY` 支持）
- 或保持现状，依赖下一次 `refresh_analytics_all()` 刷新

**建议**：保持现状（依赖主刷新），原因：
- `fct_vehicle_defect_enriched` 是 carbody LEFT JOIN defect，主刷新每次都会重建
- 单独刷新 FCT 需要 `CONCURRENTLY` 支持（已建 `UNIQUE INDEX`，支持）
- 避免额外的刷新时间不确定性

---

## 5. 迁移步骤

| 序号 | 步骤 | 执行方式 | 预期结果 | 回退点 |
|------|------|----------|----------|--------|
| **1** | 确认 SQL Server 端 `dbo.carbody_history` 表存在、列名/类型与 `schema.md` 一致、`ID` 为自增列、数据量 | MCP / SSMS 直连 SQL Server | 结构与当前 PostgreSQL 源一致，`ID` 有 `IDENTITY` 属性 | - |
| **2** | 在 `.env` 中新增 `CARBODY_SOURCE_*` 配置项 | 编辑 `.env` | 环境变量可被 `python-dotenv` 加载 | 删除新增行 |
| **3** | 在 `.env_example` 中增加占位模板 | 编辑 `.env_example` | 示例配置完整 | 还原文件 |
| **4** | 编写 `defect_database/refresh_carbody_ods.py` | 新建 Python 脚本 | 脚本可导入，语法正确 | 删除文件 |
| **5** | 创建 `meta.refresh_carbody_dim()` 存储过程 | 在 `analytics_db` 中执行 DDL | 存储过程创建成功，可手动调用 | `DROP PROCEDURE meta.refresh_carbody_dim()` |
| **6** | **首次全量导入**：执行 `python defect_database/refresh_carbody_ods.py`（此时水位为 0） | 宿主机命令行 | `ods.carbody_history` 有 ~101 万行数据 | TRUNCATE ODS + 重置水位 |
| **7** | 验证 `SELECT COUNT(*) FROM ods.carbody_history` 与 SQL Server 源库行数一致 | SQL 查询 | 行数一致 | - |
| **8** | 初始化水位为 `SELECT MAX("ID") FROM ods.carbody_history` | 脚本自动完成 | `meta.refresh_watermark` 记录为当前 max ID | 手动 UPDATE 水位 |
| **9** | 手动调用 `CALL meta.refresh_carbody_dim()` | psql 或 Python | `dim.carbody_registry` 有 ~1.3 万行 | TRUNCATE dim.carbody_registry 重新执行 |
| **10** | 执行 9.6 carbody 验证 SQL（首末时间、78 前缀、唯一性、MDS 非 NULL 率） | SQL 查询 | 全部通过 | - |
| **11** | 执行 `CALL meta.refresh_analytics_all()` | psql 或 Python | `fct.fct_vehicle_defect_enriched` 物化视图刷新成功 | - |
| **12** | 执行 9.2 全量数据验证 SQL | SQL 查询 | 所有计数与基准一致 | - |
| **13** | 二次调用 `python defect_database/refresh_carbody_ods.py` 验证增量幂等性 | 宿主机命令行 | `ods_new = 0`，两次 DIM UPSERT 无重复 | - |
| **14** | 配置 Windows 定时任务（每 5 分钟 + 每周兜底） | 任务计划程序 | 自动化运行 | 禁用任务 |
| **15** | 观察 1-2 天，确认无异常后，移除旧的 `carbody_srv` FDW 和 `src_carbody` schema（可选保留） | SQL DDL | 清理废弃对象 | 保留备份 SQL |

---

## 6. 验收标准

### 6.1 功能验收

- [ ] `refresh_carbody_ods.py` 首次执行完成全量 ODS 导入，行数与 SQL Server 源库一致（±0）
- [ ] `refresh_carbody_dim()` 执行后 `dim.carbody_registry` 行数与迁移前一致（~1.3 万）
- [ ] 增量执行幂等：连续两次调用后 `ods_new = 0`，`dim.carbody_registry` 行数不变
- [ ] `fct.fct_vehicle_defect_enriched` 刷新后数据完整，`has_defect_record` 分布正常
- [ ] 每周兜底 `--full-refresh` 可正常执行，执行后数据量与首次全量一致

### 6.2 数据质量验收（全部来自 9.6）

| 验证项 | SQL | 预期 |
|--------|-----|------|
| 首末时间合理性 | `SELECT count(*) FROM dim.carbody_registry WHERE first_seen_at > last_seen_at` | `0` |
| 78 前缀一致性 | `SELECT count(*) FROM dim.carbody_registry WHERE vehicle_id NOT LIKE '78%'` | `0` |
| vehicle_id 唯一性 | `SELECT vehicle_id, count(*) FROM dim.carbody_registry GROUP BY vehicle_id HAVING count(*) > 1` | 无返回行 |
| MDS 字段非 NULL 率 | `round(count(body_type)*100.0/count(*),1)` | `body_type` > 90%, `platform_code` > 90%, `color_code` > 90% |
| 水位记录存在 | `SELECT * FROM meta.refresh_watermark WHERE source_name IN ('ods.carbody_history.max_id','dim.carbody_registry.last_sync_id')` | 2 行 |

### 6.3 非功能验收

- [ ] 增量批次执行时间 < 10 秒（通常增量几十至几百行）
- [ ] 首次全量导入 < 5 分钟
- [ ] 每周兜底全量重刷 < 10 分钟
- [ ] 并发执行保护：两个实例同时运行时第二个被 advisory lock 阻止
- [ ] 异常时 `meta.sync_job_log` 记录 `status='failed'` + 错误信息
- [ ] Python 脚本进程退出码：成功=0，失败≠0

---

## 7. 风险与回退

### 7.1 风险清单

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| SQL Server `ID` 非自增或不严格递增 | 低 | 高 — 增量水位逻辑失效 | 步骤 1 中优先确认，若非自增则改用 `ETL_MODIFY_DATE` 或 `DATE_EVT` 驱动水位 |
| SQL Server 列名与 `schema.md` 不一致 | 低 | 中 — Python 写入失败 | 步骤 1 中用 `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS` 验证 |
| SQL Server 数据有 Unicode 字符，PostgreSQL `varchar` 无法存储 | 低 | 中 — `MDS_DATA` 字段可能含非 ASCII | 实测一条数据，必要时将 ODS 的 `varchar` 改为 `text`（PostgreSQL `text` 自动处理 UTF-8） |
| 首次全量 ~101 万行超过内存/超时 | 低 | 中 — 脚本 OOM 或超时 | **已改进**：在代码中改用 `fetchmany(BATCH_SIZE)` 流式分批拉取与写入，避免内存溢出 |
| 网络抖动导致 SQL Server 连接中断 | 中 | 低 — 增量批次丢失 | `pytds` 自带重连，脚本加 `try/except` + 日志记录，下一轮自动补录 |
| ODS 写入与水位更新发生事务不一致 | 极低 | 高 — 主键冲突阻塞链路 | **已改进**：在代码中将 ODS 写入和 水位更新放在同一个 `with pg_conn:` 事务块中 |
| 源库滚动删除导致 `ods` 中残留已删行 | 中 | 低 — `dim.carbody_registry` 保留已删车的最后已知状态 | 每周兜底 TRUNCATE 清理 ODS，DIM 使用 UPSERT 覆盖（为避免停机，不截断 DIM）。源库已硬删除的行将在 DIM 中作为历史留存 |
| `dim.carbody_registry` UPSERT 逻辑与迁移前不一致 | 低 | 高 — `fct_vehicle_defect_enriched` 数据异常 | 存储过程裁减时逐个 CTE 对比，零逻辑变更 |

### 7.2 回退方案

如果 SQL Server 连接持续不可用或数据异常无法短期修复：

1. **恢复 `carbody_srv` FDW 连接**（如果旧 PostgreSQL 源库仍存在于 `localhost`）
2. **恢复 `meta.refresh_carbody()` 原版存储过程**
3. **禁用 Windows 定时任务中的 `refresh_carbody_ods.py`**
4. **不影响 `refresh_analytics_all()` 主刷新**，`fct.fct_vehicle_defect_enriched` 只是暂时得不到 carbody 数据更新

回退操作清单：
```sql
-- 1. 重新创建 carbody_srv FDW（保留在文档中）
-- 2. 重新 IMPORT FOREIGN SCHEMA
-- 3. 恢复原版 refresh_carbody() 存储过程
-- 4. 恢复原版水位读取方式
```

```powershell
# 禁用新的定时任务
# 启用旧的定时任务（如有）
```

---

## 附录 A：Python 脚本伪代码

```python
#!/usr/bin/env python3
"""
carbody ODS 增量刷新脚本
从 SQL Server DXQcontrol_SVWMEB_BI_DWH 抽取 carbody_history 增量行
写入 PostgreSQL analytics_db.ods.carbody_history
"""
import os, sys, logging, argparse
from datetime import datetime, timezone
import psycopg2
from psycopg2 import extras
import pytds
from dotenv import load_dotenv

# PostgreSQL ods.carbody_history 的 quoted 列名
ODS_COLUMNS = [
    '"ID"', '"DATE_EVT"', '"SHIFT_NR"', '"RW_STATION_ID"',
    '"RW_STATION_STATUS"', '"SKID_ID"', '"SKID_TYPE"', '"SKID_IS_EMPTY"',
    '"BODY_ID"', '"BODY_TYPE"', '"MDS_DATA"', '"MDS_TELEGRAM_TYPE"',
    '"FK_ERP_HIST_ID"', '"CYCLE_NUM"', '"PRODUCTION_SEGMENT_ID"',
    '"ETL_MODIFY_DATE"', '"ETL_SOURCE_ID"',
]

LOCK_KEY = int(os.getenv("CARBODY_REFRESH_LOCK_KEY", "20260515"))
BATCH_SIZE = int(os.getenv("CARBODY_REFRESH_BATCH_SIZE", "5000"))


def connect_pg_target():
    """连接 PostgreSQL analytics_db，并设置会话时区以正确处理 timestamptz"""
    tz = os.getenv("CARBODY_REFRESH_TIMEZONE", "Asia/Shanghai")
    return psycopg2.connect(
        host=os.getenv("DEFECT_TARGET_DB_HOST", "localhost"),
        port=os.getenv("DEFECT_TARGET_DB_PORT", "5432"),
        dbname="analytics_db",
        user=os.getenv("DEFECT_TARGET_DB_USER", "root"),
        password=os.getenv("DEFECT_TARGET_DB_PASSWORD", "root"),
        options=f"-c timezone={tz}"
    )


def connect_ss_source():
    """连接 SQL Server 源库"""
    return pytds.connect(
        server=os.getenv("CARBODY_SOURCE_DB_HOST"),
        port=int(os.getenv("CARBODY_SOURCE_DB_PORT", "1433")),
        database=os.getenv("CARBODY_SOURCE_DB_NAME"),
        user=os.getenv("CARBODY_SOURCE_DB_USER"),
        password=os.getenv("CARBODY_SOURCE_DB_PASSWORD"),
        autocommit=True,
    )


def acquire_lock(pg_conn) -> bool:
    """获取 PostgreSQL advisory lock"""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_KEY,))
        return cur.fetchone()[0]


def release_lock(pg_conn):
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))


def read_watermark(pg_conn) -> int:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(watermark_value::numeric, 0) "
            "FROM meta.refresh_watermark "
            "WHERE source_name = 'ods.carbody_history.max_id'"
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def process_incremental_sync(ss_conn, pg_conn, last_id):
    """流式拉取并分批写入 ODS，同时更新水位（同一事务控制）"""
    sql = "SELECT * FROM dbo.carbody_history WHERE ID > %s ORDER BY ID"
    total_inserted = 0
    
    with ss_conn.cursor() as ss_cur:
        ss_cur.execute(sql, (last_id,))
        
        while True:
            rows = ss_cur.fetchmany(BATCH_SIZE)
            if not rows:
                break
                
            # 在同一个事务中完成 写入 ODS + 更新水位
            with pg_conn:
                with pg_conn.cursor() as cur:
                    # 1. 批量插入 ODS
                    col_placeholders = ", ".join(["%s"] * len(ODS_COLUMNS))
                    insert_sql = (
                        f'INSERT INTO ods.carbody_history ({", ".join(ODS_COLUMNS)}) '
                        f"VALUES ({col_placeholders})"
                    )
                    extras.execute_values(cur, insert_sql, rows)
                    
                    # 2. 紧接着更新本批次后的水位
                    cur.execute(
                        "INSERT INTO meta.refresh_watermark(source_name, watermark_value, updated_at) "
                        "VALUES ('ods.carbody_history.max_id', "
                        "(SELECT COALESCE(MAX(\"ID\")::text, '0') FROM ods.carbody_history), now()) "
                        "ON CONFLICT (source_name) DO UPDATE SET "
                        "watermark_value = EXCLUDED.watermark_value, "
                        "updated_at = EXCLUDED.updated_at"
                    )
            total_inserted += len(rows)
            
    return total_inserted


def call_refresh_carbody_dim(pg_conn):
    with pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("CALL meta.refresh_carbody_dim()")


def log_sync_job(pg_conn, status: str, message: str):
    with pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta.sync_job_log(job_name, status, finished_at, message) "
                "VALUES ('refresh_carbody_ods', %s, now(), %s)",
                (status, message),
            )


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    pg_conn = connect_pg_target()
    try:
        if not acquire_lock(pg_conn):
            logging.warning("上一轮刷新尚未完成，跳过")
            return

        ss_conn = connect_ss_source()
        try:
            # ---- full refresh mode ----
            if args.full_refresh:
                logging.info("执行每周兜底全量刷新...")
                with pg_conn:
                    with pg_conn.cursor() as cur:
                        cur.execute(
                            "UPDATE meta.refresh_watermark SET watermark_value='0' "
                            "WHERE source_name='ods.carbody_history.max_id'"
                        )
                        cur.execute("TRUNCATE TABLE ods.carbody_history")
                        # 注：不执行 TRUNCATE TABLE dim.carbody_registry，由后续 UPSERT 覆盖以防数据访问中断

            # ---- 增量/全量流式抽取与写入 ----
            v_last_id = 0 if args.full_refresh else read_watermark(pg_conn)
            inserted = process_incremental_sync(ss_conn, pg_conn, v_last_id)

            if inserted == 0:
                log_sync_job(pg_conn, "success", "ods_new: 0 rows")
                return

            logging.info(f"ODS 写入与水位更新: {inserted} 行")

            # ---- 触发 DIM 刷新 ----
            call_refresh_carbody_dim(pg_conn)
            logging.info("DIM UPSERT 完成")

            # ---- 日志 ----
            log_sync_job(pg_conn, "success", f"ods_new: {inserted} rows")

        finally:
            ss_conn.close()
    except Exception as e:
        logging.error("refresh_carbody_ods 执行失败", exc_info=True)
        log_sync_job(pg_conn, "failed", str(e))
        raise
    finally:
        release_lock(pg_conn)
        pg_conn.close()


if __name__ == "__main__":
    main()
```

---

## 附录 B：裁减后存储过程完整 SQL

```sql
-- ============================================================
-- meta.refresh_carbody_dim()
-- 从 ods.carbody_history 增量聚合 → dim.carbody_registry UPSERT
-- 不再包含 ODS 抽取步骤（ODS 抽取由 Python refresh_carbody_ods.py 完成）
-- ============================================================
CREATE OR REPLACE PROCEDURE meta.refresh_carbody_dim()
LANGUAGE plpgsql
AS $$
DECLARE
  v_log_id      BIGINT;
  v_last_dim_id NUMERIC;
  v_new_count   INTEGER;
BEGIN
  INSERT INTO meta.sync_job_log(job_name, status, message)
  VALUES ('refresh_carbody_dim', 'running', 'start')
  RETURNING id INTO v_log_id;

  -- 1. 读取 DIM 上次处理的最大 ID
  SELECT COALESCE(watermark_value::numeric, 0)
  INTO v_last_dim_id
  FROM meta.refresh_watermark
  WHERE source_name = 'dim.carbody_registry.last_sync_id';

  -- 2. 对增量 ODS 行做聚合 + UPSERT
  WITH new_records AS (
      SELECT * FROM ods.carbody_history
      WHERE "ID" > v_last_dim_id
        AND "BODY_ID" LIKE '78%'
  ),
  vehicle_agg AS (
      SELECT
          "BODY_ID" AS vehicle_id,
          MIN("DATE_EVT") AS first_seen_at,
          MAX("DATE_EVT") AS last_seen_at,
          (ARRAY_AGG("RW_STATION_ID" ORDER BY "DATE_EVT"))[1]      AS first_rw_station,
          (ARRAY_AGG("RW_STATION_ID" ORDER BY "DATE_EVT" DESC))[1] AS last_rw_station,
          (ARRAY_AGG("BODY_TYPE"    ORDER BY "DATE_EVT"))[1]      AS first_body_type,
          (ARRAY_AGG("BODY_TYPE"    ORDER BY "DATE_EVT" DESC))[1] AS last_body_type,
          count(*) AS station_pass_count
      FROM new_records
      GROUP BY "BODY_ID"
  ),
  last_mds AS (
      SELECT DISTINCT ON ("BODY_ID")
          "BODY_ID",
          substring("MDS_DATA", 45, 5)  AS mds_body_type,
          substring("MDS_DATA", 51, 3)  AS mds_platform_code,
          substring("MDS_DATA", 59, 4)  AS mds_color_code,
          substring("MDS_DATA", 137, 1) AS mds_black_roof_flag,
          substring("MDS_DATA", 139, 1) AS mds_rework_flag,
          substring("MDS_DATA", 138, 1) AS mds_reserved_1,
          substring("MDS_DATA", 140, 1) AS mds_reserved_2
      FROM new_records
      WHERE length("MDS_DATA") >= 140
      ORDER BY "BODY_ID", "DATE_EVT" DESC
  )
  INSERT INTO dim.carbody_registry (
      vehicle_id, first_seen_at, last_seen_at,
      first_rw_station, last_rw_station,
      first_body_type, last_body_type, station_pass_count,
      body_type, platform_code, color_code,
      black_roof_flag, rework_flag, reserved_1, reserved_2
  )
  SELECT
      va.vehicle_id,
      va.first_seen_at,
      va.last_seen_at,
      va.first_rw_station,
      va.last_rw_station,
      va.first_body_type,
      va.last_body_type,
      va.station_pass_count,
      lm.mds_body_type,
      lm.mds_platform_code,
      lm.mds_color_code,
      lm.mds_black_roof_flag,
      lm.mds_rework_flag,
      lm.mds_reserved_1,
      lm.mds_reserved_2
  FROM vehicle_agg va
  LEFT JOIN last_mds lm ON lm."BODY_ID" = va.vehicle_id
  ON CONFLICT (vehicle_id) DO UPDATE SET
      last_seen_at       = EXCLUDED.last_seen_at,
      last_rw_station    = EXCLUDED.last_rw_station,
      last_body_type     = EXCLUDED.last_body_type,
      station_pass_count = dim.carbody_registry.station_pass_count
                         + EXCLUDED.station_pass_count,
      body_type          = EXCLUDED.body_type,
      platform_code      = EXCLUDED.platform_code,
      color_code         = EXCLUDED.color_code,
      black_roof_flag    = EXCLUDED.black_roof_flag,
      rework_flag        = EXCLUDED.rework_flag,
      reserved_1         = EXCLUDED.reserved_1,
      reserved_2         = EXCLUDED.reserved_2;

  GET DIAGNOSTICS v_new_count = ROW_COUNT;

  -- 3. 更新 DIM 水位
  INSERT INTO meta.refresh_watermark(source_name, watermark_value, updated_at)
  VALUES
    ('dim.carbody_registry.last_sync_id',
     (SELECT COALESCE(MAX("ID")::text, '0') FROM ods.carbody_history), now()),
    ('dim.carbody_registry.last_sync_at', now()::text, now())
  ON CONFLICT (source_name) DO UPDATE
  SET watermark_value = EXCLUDED.watermark_value,
      updated_at      = EXCLUDED.updated_at;

  -- 4. 权限
  GRANT SELECT ON ods.carbody_history TO agent_ro;
  GRANT SELECT ON dim.carbody_registry TO agent_ro;

  -- 5. 日志
  UPDATE meta.sync_job_log
  SET finished_at = now(), status = 'success',
      message = format('dim_upsert: %s rows', v_new_count)
  WHERE id = v_log_id;

EXCEPTION WHEN OTHERS THEN
  UPDATE meta.sync_job_log
  SET finished_at = now(), status = 'failed', message = SQLERRM
  WHERE id = v_log_id;
  RAISE;
END;
$$;
```

**与旧版 `refresh_carbody()` 的差异**：

| 项目 | 旧版 | 新版 |
|------|------|------|
| ODS 水位名 | `ods.carbody_history.max_id` | 不涉及（Python 管理） |
| DIM 水位名 | 复用 `ods.carbody_history.max_id` | 新增 `dim.carbody_registry.last_sync_id` |
| `new_records` WHERE | `"ID" > v_last_id`（ODS 水位） | `"ID" > v_last_dim_id`（DIM 水位） |
| ODS INSERT / src_carbody 引用 | 有 | 无 |
| 权限 GRANT src_carbody | 有 | 无 |

---

## 附录 C：SQL Server 侧需确认项

请在迁移前逐一确认以下信息，将答案填入"实际值"列：

| # | 确认项 | 期望值 | 实际值 | 验证方法 |
|---|--------|--------|--------|----------|
| 1 | 数据库名 | `DXQcontrol_SVWMEB_BI_DWH` | | `SELECT DB_NAME()` |
| 2 | Schema | `dbo` | | `SELECT SCHEMA_NAME()` |
| 3 | 表名 | `carbody_history` | | `SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'carbody_history'` |
| 4 | 总行数 | ~101 万 | | `SELECT COUNT(*) FROM dbo.carbody_history` |
| 5 | `ID` 是否为 IDENTITY | `YES` | | `SELECT COLUMNPROPERTY(OBJECT_ID('dbo.carbody_history'), 'ID', 'IsIdentity')` |
| 6 | `ID` 当前最大值 | - | | `SELECT MAX(ID) FROM dbo.carbody_history` |
| 7 | `DATE_EVT` 类型 | `datetime` 或 `datetime2` | | `SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'carbody_history' AND COLUMN_NAME = 'DATE_EVT'` |
| 8 | `MDS_DATA` 类型和最大长度 | `varchar(MAX)` 或 `nvarchar(MAX)` | | `SELECT DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'carbody_history' AND COLUMN_NAME = 'MDS_DATA'` |
| 9 | `MDS_DATA` 非 NULL 率 | > 99% | | `SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM dbo.carbody_history) FROM dbo.carbody_history WHERE MDS_DATA IS NOT NULL AND LEN(MDS_DATA) >= 140` |
| 10 | `BODY_ID` 78 前缀占比 | ~1.3% (13000/1010000) | | `SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM dbo.carbody_history) FROM dbo.carbody_history WHERE BODY_ID LIKE '78%'` |
| 11 | `BODY_ID` 78 前缀去重数 | ~1.3 万 | | `SELECT COUNT(DISTINCT BODY_ID) FROM dbo.carbody_history WHERE BODY_ID LIKE '78%'` |
| 12 | 列名列表（17 列） | 见 `carbody_history/schema.md` | | `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'carbody_history' ORDER BY ORDINAL_POSITION` |
| 13 | 数据保留策略 | 是否有滚动删除？保留多长时间？ | | 询问 DBA |
| 14 | 网络可达性 | 从 Python 宿主机 `ping 172.22.37.52` | | `tnsping` 或 `telnet 172.22.37.52 1433` |
| 15 | 账号权限 | `sa` 或具有 `SELECT` 权限的账号 | | 用配置的账号执行 `SELECT TOP 1 * FROM dbo.carbody_history` |

---

## 附录 D：相关文件索引

| 文件 | 说明 |
|------|------|
| `defect_database/database_refactor/analytics_db_architecture.md` | Analytics DB 落地与刷新操作手册（含 carbody FDW/ODS/DIM/FCT 完整 SQL） |
| `defect_database/database_refactor/analytics_db_data_lineage.md` | 数据血缘关系文档 |
| `defect_database/database_refactor/analytics_db_migration_checklist.md` | 新环境迁移清单 |
| `defect_database/database_refactor/analytics_db_todolist.md` | 待办事项 |
| `carbody_history/schema.md` | carbody_history 表结构 |
| `carbody_history/MDS数据提取规则.md` | MDS_DATA 7 字段提取规则 |
| `defect_database/refresh_history_station_defect_summary.py` | SQL Server 连接参考实现（python-tds） |
| `requirements.txt` | 已包含 `python-tds==1.16.0` |
| `.env` | 环境变量配置 |
