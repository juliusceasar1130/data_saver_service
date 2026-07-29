# Analytics DB 落地与刷新操作手册（最新已验证版）

修改时间：2026-07-28 Asia/Shanghai

主要修改内容：
- **新增 FIS 项目车业务源库 FDW 映射与 ODS 贴源对齐**：新增 `project_vehicle_db` 源库的 FDW 外部连接挂载（`project_vehicle_srv`）、模式 `src_project_vehicle` 及外部表映射 `src_project_vehicle.project_vehicle_orders`；初始化本地物理 ODS 贴源表 `ods.ods_fis_project_vehicle_orders` 及其主键与 `composite_pin_no` 专属 B-Tree 索引。

历史修改时间：2026-07-23 Asia/Shanghai

历史修改内容：
- **画像表与质量集市升级**：为 `dim.dim_vehicle_profile` 画像表扩展了 9 个车身历史及状态字段；将 `mart.mart_vehicle_quality_360` 物化视图的驱动表更改为 `fct.fct_vehicle_defect_enriched`，从而全面支持展示在产未检车辆与漏检车辆；同步升级一键刷新存储过程 `meta.refresh_analytics_all()` 支持“滚床在产 + 缺陷系统 + 车身历史”三源合并。
- **删除过时 ALTER 语句**：删除了第 6.4 节中已过时的旧版 `dim_vehicle_profile` 位置快照字段补全 `ALTER TABLE` 语句，保持文档整洁及部署的准确性。
- **校验基线对齐更新**：更正了第 2 节中因升级导致的过时数据量基线，更新了 `dim_vehicle_profile` 中已整合的全部实时、车身过站以及缺陷新字段列表。
- **注释术语统一**：更新车身注册表相关的注释，将 `rw_station` 对应的中文注释由“过站位置/工位”修正并统一为“过站读写站”，以契合现场读写站（Read-Write Station）设备的实际业务术语。

历史修改时间：2026-05-21 Asia/Shanghai




历史修改内容：
- **初始化依赖关系优化**：调整底层表与维表的初始化顺序，将 `ods.carbody_history`、`dim.carbody_registry` 以及存储过程 `meta.refresh_carbody_dim` 移动到物化视图 `fct.fct_vehicle_defect_enriched` 之前，彻底解决物化视图 DDL 初始化时的表依赖报错问题。
- **日常验证 SQL 遗留清理**：修正日常验证中遗留的废弃存储过程名称 `refresh_carbody`，统一为新存储过程名 `refresh_carbody_dim`，并同步更新其幂等性验证 SQL 注释。


历史修改时间：2026-05-16 Asia/Shanghai

历史修改内容：
- **Carbody 数据链路重构**：彻底移除 `postgres_fdw` 连接，改为通过 Python 脚本直连 SQL Server 抽取数据。
- **配置隔离**：在 `.env` 中引入 `CARBODY_TARGET_*` 独立变量，实现任务解耦。
- **存储过程升级**：更新 `meta.refresh_carbody_dim`，支持增量聚合、日志监控及 FCT 自动刷新。
- **字段类型对齐**：修正 `ods.carbody_history` 中 SKID 和 CYCLE 字段为 VARCHAR，适配源库真实数据。
- 新增 `fct.fct_vehicle_defect_enriched` 物化视图：以 carbody 为中心，整合缺陷检测记录的全量分析宽表
- 优化 `refresh_analytics_all()` 过程：在 MART 刷新后增加 `fct_vehicle_defect_enriched` 的刷新步骤

## 目录

- [1. 适用范围](#1-适用范围)
- [2. 当前已验证的最新状态](#2-当前已验证的最新状态)
- [3. 旧版流程中已修正的错误](#3-旧版流程中已修正的错误)
- [4. 前置确认](#4-前置确认)
- [5. 一次性初始化流程](#5-一次性初始化流程)
- [5.1 检查 `analytics_db` 是否已存在](#51-检查-analytics_db-是否已存在)
- [5.2 创建 `analytics_db`](#52-创建-analytics_db)
- [5.3 创建 schema](#53-创建-schema)
- [5.4 创建只读角色](#54-创建只读角色)
- [5.5 创建 FDW 连接](#55-创建-fdw-连接)
- [5.6 导入外部表](#56-导入外部表)
- [6. 本地 ODS / DIM / FCT / MART 对象初始化](#6-本地-ods--dim--fct--mart-对象初始化)
- [6.1 创建 ODS 表](#61-创建-ods-表)
- [6.2 ODS 主键与索引](#62-ods-主键与索引)
- [6.3 创建 `meta` 表](#63-创建-meta-表)
- [6.4 创建 `dim` 表](#64-创建-dim-表)
- [6.5 创建 ods.carbody_history](#65-创建-odscarbody_history)
- [6.6 创建 dim.carbody_registry](#66-创建-dimcarbody_registry)
- [6.7 聚合存储过程 meta.refresh_carbody_dim](#67-聚合存储过程-metarefresh_carbody_dim)
- [6.8 创建事实层与分析层物化视图](#68-创建事实层与分析层物化视图)
- [6.9 授权](#69-授权)
- [7. 最新正式版一键刷新过程](#7-最新正式版一键刷新过程)
- [8. 首次刷新](#8-首次刷新)
- [9. 日常验证 SQL](#9-日常验证-sql)
- [9.4 验证异常车分类结果](#94-验证异常车分类结果)
- [9.5 验证 `agent_ro` 权限](#95-验证-agent_ro-权限)
- [10. 后续怎么执行](#10-后续怎么执行)
- [10.1 手工刷新](#101-手工刷新)
- [10.2 Windows 定时任务](#102-windows-定时任务)
- [10.3 建议频率](#103-建议频率)
- [11. 项目接入](#11-项目接入)
- [12. 两个重要提醒](#12-两个重要提醒)

## 1. 适用范围

本手册面向当前项目的 `analytics_db` 分析库建设与后续刷新维护。

当前项目涉及的三个业务源库：

- `rollerbed_tracking_db`
- `defect_db`
- `project_vehicle_db`

当前分析库策略：

- 在 PostgreSQL 中独立建设 `analytics_db`
- 通过 `postgres_fdw` 挂载三个源库（`src_rb`, `src_defect`, `src_project_vehicle`）
- 将源表数据同步落盘到本地 `ods` 物理表（含索引）
- 在 `fct` / `mart` 中生成给 Agent 使用的分析对象

本手册与 `current_vehicle_fact_refactor.md` 的关系：

- 本手册是当前项目后续执行、刷新、校验、接入时应采用的唯一落地基线
- `current_vehicle_fact_refactor.md` 保留为第一阶段分层重构的历史设计记录
- 若两份文档出现口径差异，以本手册和实时数据库对象定义为准

## 2. 当前已验证的最新状态

2026-04-14 通过 MCP 直连实时 `analytics_db` 校验，数据库中当前存在以下对象：

- 数据库：
  - `analytics_db`
- schema：
  - `src_rb`
  - `src_defect`
  - `src_carbody (旧版 FDW 遗留，新版已由 Python ETL 直连取代)`
  - `ods`
  - `dim`
  - `fct`
  - `mart`
  - `meta`
- `ods` 表：
  - `rb_position_data`
  - `process_areas`
  - `carrier_types`
  - `vehicle_body_types`
  - `vehicle_color_codes`
  - `vehicle_platforms`
  - `history_station_defect_summary`
  - `carbody_history`
- `dim` 表：
  - `dim_process_area`
  - `dim_vehicle_profile`
  - `carbody_registry`
- `fct` 物化视图：
  - `fct_position_current_all`
  - `fct_abnormal_vehicle_current`
  - `fct_vehicle_position_current`
  - `fct_vehicle_defect_detection` (仅缺陷事件)
  - `fct_vehicle_defect_enriched` (车身中心全量视图)
- `mart` 物化视图：
  - `mart_abnormal_vehicle_current`
  - `mart_position_current_overview`
  - `mart_vehicle_quality_360`
- `meta` 表：
  - `sync_job_log`
  - `refresh_watermark`
- 刷新过程：
  - `meta.refresh_analytics_all()`
  - `meta.refresh_carbody_dim() (原 refresh_carbody 已废弃)`
- 只读角色：
  - `agent_ro`

本手册以下内容，以这套已验证状态为准。

当次实时校验结果（2026-04-14，当前数据水位仍停留在 2026-04-11 刷新批次）：

- `ods.rb_position_data`：`520`
- `ods.history_station_defect_summary`：`60370`
- `dim.dim_process_area`：`15`
- `dim.dim_vehicle_profile`：`54430`
- `fct.fct_position_current_all`：`114`
- `fct.fct_vehicle_position_current`：`102`
- `fct.fct_abnormal_vehicle_current`：`12`
- `fct.fct_vehicle_defect_detection`：`60370`
- `fct.fct_vehicle_defect_enriched`：`>= 54430` (取决于 carbody 记录数)
- `mart.mart_vehicle_quality_360`：`>= 54430` (由于改用车身富集表驱动已包含未检测车辆，行数与 fct_vehicle_defect_enriched 保持一致)
- `mart.mart_abnormal_vehicle_current`：`12`
- `mart.mart_position_current_overview`：`114`

当次实时校验还确认：

- `dim.dim_vehicle_profile` 已整合以下三大来源的核心特征属性：
  - **实时位置快照**：`current_position_id`, `current_carrier_id`, `current_carrier_type`, `current_process_area`, `current_full_rb_code`, `current_position_updated_at`
  - **物理车身过站历史**：`carbody_first_seen_at`, `carbody_last_seen_at`, `carbody_first_rw_station`, `carbody_last_rw_station`, `carbody_station_pass_count`, `is_rework`
  - **最新缺陷状态指标**：`has_defect_record`, `defect_last_seen_at`
- `fct.fct_position_current_all` 的真实定义已按当前占位进行分类：
  - `product_vehicle`
  - `abnormal_vehicle`
- `fct.fct_abnormal_vehicle_current` 当前实时分类结果为：
  - `empty_vehicle_id_with_carrier`：`8`
  - `non_product_prefix`：`4`
- `meta.refresh_watermark` 当前记录为：
  - `ods.rb_position_data.max_vehicle_updated_at = 2026-04-03 06:11:32.191541+00`
  - `ods.history_station_defect_summary.max_date_time = 2026-04-08 11:54:19`
  - `ods.history_station_defect_summary.max_history_id = 1301806`

## 3. 旧版流程中已修正的错误

旧版流程有几处容易误导后续执行，现统一修正如下：

1. `meta.refresh_analytics_all()` 旧版只刷新 `ods` 与物化视图，没有刷新 `dim` 表。
2. 当前正式版本的刷新过程会同时重建：
   - `dim.dim_process_area`
   - `dim.dim_vehicle_profile`
   - `meta.refresh_watermark`
3. 当前刷新机制是“全量刷新”，不是增量刷新。
4. `mart.mart_vehicle_quality_360` 当前关联的是：
   - 缺陷检测记录
   - 车辆当前最新位置
   不是“检测当时位置”。
5. 当前 `fct.fct_vehicle_position_current` 已明确收敛为“正式产品车当前事实”。
6. 当前异常车与全量当前占位已分别由：
   - `fct.fct_position_current_all`
   - `fct.fct_abnormal_vehicle_current`
   - `mart.mart_abnormal_vehicle_current`
   承接。
7. 当前 `dim.dim_vehicle_profile` 已补充 `current_*` 字段，用于保留正式产品车的当前绑定快照。

## 3.1 当前已知限制

当前数据库结构已经完成第一阶段分层优化，但仍有两个需要明确的边界：

1. `fct.fct_vehicle_position_current` 现在只面向正式产品车。  
   它已经按 `vehicle_id LIKE '782026%'`、`body_type <> '-----'`、`carrier_id <> '0'` 收窄，不应再拿它回答“全部当前占位”问题。
2. `mart.mart_vehicle_quality_360` 仍然关联的是：
   - 一次缺陷检测
   - 该车当前最新位置  
   它不是“检测当时位置”的严格还原口径。

当前已经通过新增对象修正了异常车与重复调试 `vehicle_id` 的主要问题：

- `fct.fct_position_current_all`
- `fct.fct_abnormal_vehicle_current`
- `mart.mart_abnormal_vehicle_current`

下一阶段如果还要继续增强，重点会转向：

- `mart_position_current_overview`
- 位置历史快照层
- 检测时位置或停留时长关联分析

以上边界与后续方向，原本分散记录在 `current_vehicle_fact_refactor.md` 中，现已并入本手册。

## 3.2 为什么必须拆分“全部占位 / 正式产品车 / 异常车”

本次分层优化的根本原因，不是命名调整，而是业务实体唯一性不同。

### 3.2.1 重复调试 `vehicle_id` 会被错误压缩

旧版 `fct.fct_vehicle_position_current` 的核心逻辑是：

- 从 `ods.rb_position_data` 中取数
- 按 `vehicle_id` 使用 `DISTINCT ON (vehicle_id)` 保留最新一条

这套逻辑对正式产品车基本成立，但对异常车或调试车不成立。  
如果现场有多台调试车共用同一个临时 `vehicle_id`，例如 `88888888888888`，那么按 `vehicle_id` 去重后只能保留一条，无法代表“当前全部占位”。

### 3.2.2 产品车与异常车的建模依据不同

正式产品车当前采用的识别口径是：

- `vehicle_id LIKE '782026%'`
- `body_type <> '-----'`
- `carrier_id <> '0'`

异常车则可能出现以下情况：

- `vehicle_id` 前缀不是 `782026`
- `vehicle_id = '--------------'`
- `vehicle_id` 为空
- `vehicle_id` 虽是产品前缀，但 `body_type = '-----'`

因此异常车不能继续与正式产品车共用同一个“按 `vehicle_id` 唯一化”的事实表。

### 3.2.3 为什么不能再把 `fct_vehicle_position_current` 当成总入口

如果继续把 `fct.fct_vehicle_position_current` 当成“全部车辆当前事实”，会导致：

1. 多台调试车共用 `vehicle_id` 时被错误合并
2. 异常车统计被系统性低估
3. `carrier_id -> vehicle_id` 的当前绑定关系不完整
4. Agent 容易把“正式产品车事实”误认为“全部现场事实”

因此当前正式落地口径已经拆为：

- `fct.fct_position_current_all`：当前全部有效占位
- `fct.fct_vehicle_position_current`：当前正式产品车
- `fct.fct_abnormal_vehicle_current`：当前异常车

## 3.3 建议查询入口

为避免 Agent 或后续开发继续混用口径，当前建议的查询入口固定如下：

- 正式产品车当前分布：
  - `fct.fct_vehicle_position_current`
- 当前异常车监控：
  - `fct.fct_abnormal_vehicle_current`
  - `mart.mart_abnormal_vehicle_current`
- 当前现场总览：
  - `fct.fct_position_current_all`
  - `mart.mart_position_current_overview`
- 质量与当前位置关联：
  - `mart.mart_vehicle_quality_360`

一句话原则：

- 不再试图让一张表同时承担“全部占位、正式产品车、异常车”三种不同口径

## 4. 前置确认

首次搭建前，请先确认源表已存在：

- `rollerbed_tracking_db` 中的基础表来自：
  - [create_tables_postgresql.sql](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/create_tables_postgresql.sql)
- `defect_db` 中需要先存在：
  - `history_station_defect_summary`
- 缺陷汇总表说明文档：
  - [history_station_defect_summary_schema.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/defect_database_from_agent/history_station_defect_summary_schema.md)

默认 PostgreSQL 环境：

- 主机：`localhost`
- 端口：`5432`
- 管理员：`root`
- 密码：`root`

## 5. 一次性初始化流程

这一部分只在首次搭建或重建 `analytics_db` 时执行。

### 5.1 检查 `analytics_db` 是否已存在

先连接到 `postgres` 库或任意管理工具，执行：

```sql
SELECT datname
FROM pg_database
WHERE datname = 'analytics_db';
```

如果已经返回 `analytics_db`，说明库已存在，跳过“创建数据库”步骤。

### 5.2 创建 `analytics_db`

如果数据库不存在，再执行：

```sql
CREATE DATABASE analytics_db
WITH OWNER = root
     ENCODING = 'UTF8'
     TEMPLATE = template0;
```

然后切换到新库：

```sql
\c analytics_db
```

### 5.3 创建 schema

```sql
CREATE SCHEMA IF NOT EXISTS src_rb;              -- 滚床追踪业务源库 FDW 外部表模式
CREATE SCHEMA IF NOT EXISTS src_defect;          -- 缺陷检测业务源库 FDW 外部表模式
CREATE SCHEMA IF NOT EXISTS src_project_vehicle; -- FIS 项目车业务源库 FDW 外部表模式
CREATE SCHEMA IF NOT EXISTS ods;                 -- 本地物理贴源层 Schema
CREATE SCHEMA IF NOT EXISTS dim;                 -- 维表层 Schema
CREATE SCHEMA IF NOT EXISTS fct;                 -- 事实表/宽表层 Schema
CREATE SCHEMA IF NOT EXISTS mart;                -- 数据集市层 Schema
CREATE SCHEMA IF NOT EXISTS meta;                -- 元数据管理与日志 Schema
```

### 5.4 创建只读角色

如果 `agent_ro` 不存在，再执行：

```sql
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'agent_ro'
  ) THEN
    CREATE ROLE agent_ro LOGIN PASSWORD '请改成强密码';
  END IF;
END;
$$;
```

授权：

```sql
GRANT CONNECT ON DATABASE analytics_db TO agent_ro;
GRANT USAGE ON SCHEMA ods, dim, fct, mart, meta TO agent_ro;
```

### 5.5 创建 FDW 连接

```sql
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
```

如果外部 server 不存在，再执行：

```sql
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_foreign_server WHERE srvname = 'rollerbed_srv'
  ) THEN
    CREATE SERVER rollerbed_srv
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'localhost', dbname 'rollerbed_tracking_db', port '5432');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_foreign_server WHERE srvname = 'defect_srv'
  ) THEN
    CREATE SERVER defect_srv
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'localhost', dbname 'defect_db', port '5432');
  END IF;
END;
$$;

-- 挂载 FIS 项目车业务源库 (project_vehicle_db)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_foreign_server WHERE srvname = 'project_vehicle_srv'
  ) THEN
    CREATE SERVER project_vehicle_srv
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'localhost', dbname 'project_vehicle_db', port '5432');
  END IF;
END;
$$;
```

为 `root` 创建 user mapping：

```sql
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_user_mappings m
    JOIN pg_foreign_server s ON m.srvid = s.oid
    JOIN pg_roles r ON m.umuser = r.oid
    WHERE s.srvname = 'rollerbed_srv' AND r.rolname = 'root'
  ) THEN
    CREATE USER MAPPING FOR root
    SERVER rollerbed_srv
    OPTIONS (user 'root', password 'root');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_user_mappings m
    JOIN pg_foreign_server s ON m.srvid = s.oid
    JOIN pg_roles r ON m.umuser = r.oid
    WHERE s.srvname = 'defect_srv' AND r.rolname = 'root'
  ) THEN
    CREATE USER MAPPING FOR root
    SERVER defect_srv
    OPTIONS (user 'root', password 'root');
  END IF;
END;
$$;

-- 为 project_vehicle_srv 创建 root 用户映射
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_user_mappings m
    JOIN pg_foreign_server s ON m.srvid = s.oid
    JOIN pg_roles r ON m.umuser = r.oid
    WHERE s.srvname = 'project_vehicle_srv' AND r.rolname = 'root'
  ) THEN
    CREATE USER MAPPING FOR root
    SERVER project_vehicle_srv
    OPTIONS (user 'root', password 'root');
  END IF;
END;
$$;
```

### 5.6 导入外部表

注意：`IMPORT FOREIGN SCHEMA` 只应在外部表尚未导入时执行一次。

```sql
IMPORT FOREIGN SCHEMA public
LIMIT TO (
  rb_position_data,
  process_areas,
  carrier_types,
  vehicle_body_types,
  vehicle_color_codes,
  vehicle_platforms
)
FROM SERVER rollerbed_srv INTO src_rb;

IMPORT FOREIGN SCHEMA public
LIMIT TO (
  history_station_defect_summary
)
FROM SERVER defect_srv INTO src_defect;

-- 导入 FIS 项目车订单明细外部表 (project_vehicle_orders)
IMPORT FOREIGN SCHEMA public
LIMIT TO (
  project_vehicle_orders
)
FROM SERVER project_vehicle_srv INTO src_project_vehicle;
```

如果这些外部表已经存在，就不要重复执行上面的导入语句。

---
-- 注意：原 5.7 节 carbody FDW 已弃用，改由 Python ETL 直连 SQL Server。
---

## 6. 本地 ODS / DIM / FCT / MART 对象初始化

如果是首次搭建，依次执行以下对象初始化 SQL。

### 6.1 创建 ODS 表

```sql
CREATE TABLE IF NOT EXISTS ods.rb_position_data AS
SELECT * FROM src_rb.rb_position_data WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.process_areas AS
SELECT * FROM src_rb.process_areas WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.carrier_types AS
SELECT * FROM src_rb.carrier_types WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.vehicle_body_types AS
SELECT * FROM src_rb.vehicle_body_types WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.vehicle_color_codes AS
SELECT * FROM src_rb.vehicle_color_codes WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.vehicle_platforms AS
SELECT * FROM src_rb.vehicle_platforms WITH NO DATA;

CREATE TABLE IF NOT EXISTS ods.history_station_defect_summary AS
SELECT * FROM src_defect.history_station_defect_summary WITH NO DATA;

-- 创建 FIS 项目车订单明细物理贴源表 (初始结构同步自 src_project_vehicle.project_vehicle_orders 外表)
CREATE TABLE IF NOT EXISTS ods.ods_fis_project_vehicle_orders AS
SELECT * FROM src_project_vehicle.project_vehicle_orders WITH NO DATA;
```

### 6.2 ODS 主键与索引

首次创建后执行一次：

```sql
ALTER TABLE ods.rb_position_data ADD PRIMARY KEY (id);
ALTER TABLE ods.process_areas ADD PRIMARY KEY (id);
ALTER TABLE ods.carrier_types ADD PRIMARY KEY (id);
ALTER TABLE ods.vehicle_body_types ADD PRIMARY KEY (id);
ALTER TABLE ods.vehicle_color_codes ADD PRIMARY KEY (id);
ALTER TABLE ods.vehicle_platforms ADD PRIMARY KEY (id);
ALTER TABLE ods.history_station_defect_summary ADD PRIMARY KEY (history_id);
ALTER TABLE ods.ods_fis_project_vehicle_orders ADD PRIMARY KEY (project_vehicle_no);
```

索引：

```sql
CREATE INDEX IF NOT EXISTS idx_ods_rb_vehicle_id
ON ods.rb_position_data(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_ods_rb_process_area
ON ods.rb_position_data(process_area);

CREATE INDEX IF NOT EXISTS idx_ods_rb_vehicle_updated_at
ON ods.rb_position_data(vehicle_updated_at);

CREATE INDEX IF NOT EXISTS idx_ods_defect_vehicle_id
ON ods.history_station_defect_summary(serial_number);

CREATE INDEX IF NOT EXISTS idx_ods_defect_detect_time
ON ods.history_station_defect_summary(date_time);

-- FIS 项目车订单明细检索与匹配索引 (含 13 位合成 PIN 精确匹配专属索引)
CREATE INDEX IF NOT EXISTS idx_ods_pvo_composite_pin
ON ods.ods_fis_project_vehicle_orders(composite_pin_no);

CREATE INDEX IF NOT EXISTS idx_ods_pvo_pin
ON ods.ods_fis_project_vehicle_orders(pin_no);

CREATE INDEX IF NOT EXISTS idx_ods_pvo_knr
ON ods.ods_fis_project_vehicle_orders(knr_no);
```

### 6.3 创建 `meta` 表

```sql
CREATE TABLE IF NOT EXISTS meta.sync_job_log (
  id BIGSERIAL PRIMARY KEY,
  job_name TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  message TEXT
);

CREATE TABLE IF NOT EXISTS meta.refresh_watermark (
  source_name TEXT PRIMARY KEY,
  watermark_value TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.4 创建 `dim` 表

```sql
CREATE TABLE IF NOT EXISTS dim.dim_process_area (
  process_area_name VARCHAR(50) PRIMARY KEY,
  source_area_id INTEGER,
  description VARCHAR(200),
  sort_order INTEGER,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dim.dim_vehicle_profile (
  vehicle_id VARCHAR(255) PRIMARY KEY,              -- 车辆唯一识别码
  body_type VARCHAR(5),                              -- 车型代码（优先滚床，其次车身）
  tracking_type_name VARCHAR(100),                   -- 车型中文名（由 body_type 关联字典翻译）
  defect_model INTEGER,                              -- 最新缺陷检测型号
  defect_type_name VARCHAR(100),                     -- 最新缺陷检测类型名
  platform_code VARCHAR(10),                         -- 平台代码
  platform_name VARCHAR(50),                         -- 平台中文名
  color_code VARCHAR(255),                           -- 颜色代码（优先滚床，其次缺陷，再次车身）
  color_name VARCHAR(50),                            -- 颜色中文名
  is_black_roof BOOLEAN,                             -- 是否双色车顶（滚床黑顶或缺陷包含“黑”或车身黑顶）
  is_rework BOOLEAN,                                 -- 是否重工车（根据车身重工标记 rework_flag 计算）
  has_defect_record BOOLEAN,                         -- 是否存在缺陷检测记录
  black_roof_raw_tracking VARCHAR(32),               -- 滚床原始黑车顶标记
  black_roof_raw_defect VARCHAR(100),                -- 缺陷系统原始黑车顶标记
  tracking_last_seen_at TIMESTAMPTZ,                 -- 滚床系统最后看到时间
  defect_last_seen_at TIMESTAMPTZ,                   -- 缺陷系统最后检测时间
  
  -- ===== 🆕 新增：物理车身过站汇总属性 (源自 dim.carbody_registry) =====
  carbody_first_seen_at TIMESTAMPTZ,                 -- 首次过站读写站时间
  carbody_last_seen_at TIMESTAMPTZ,                  -- 末次过站读写站时间
  carbody_first_rw_station VARCHAR(64),              -- 首次过站读写站编码
  carbody_last_rw_station VARCHAR(64),               -- 末次过站读写站编码
  carbody_station_pass_count INTEGER,                -- 累计过站读写站总频次（频次过高反映内循环返修）
  carbody_reserved_1 VARCHAR(1),                     -- 车身 MDS 备用字段 1
  carbody_reserved_2 VARCHAR(1),                     -- 车身 MDS 备用字段 2
  retention_checkpoint_station VARCHAR(64),          -- 滞留监控关键读写站编码 (取自指定列表中的最新节点)
  retention_checkpoint_pass_at TIMESTAMPTZ,          -- 滞留监控关键读写站过站时间
  project_vehicle_no VARCHAR(64),                    -- 项目车编号 (关联项目车生产订单明细)
  
  current_position_id BIGINT,                        -- 当前最新占位位置 ID
  current_carrier_id VARCHAR(50),                    -- 当前最新载体卡号
  current_carrier_type VARCHAR(20),                  -- 当前最新载体类型
  current_process_area VARCHAR(50),                  -- 当前最新工艺区域
  current_full_rb_code VARCHAR(255),                 -- 当前最新位置全编码
  current_position_updated_at TIMESTAMPTZ,           -- 当前位置最后更新时间
  etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()   -- 画像数据装载时间
);
```

索引：

```sql
CREATE INDEX IF NOT EXISTS idx_dim_process_area_sort_order
ON dim.dim_process_area(sort_order);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_type_name
ON dim.dim_vehicle_profile(defect_type_name, tracking_type_name);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_color_code
ON dim.dim_vehicle_profile(color_code);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_platform_code
ON dim.dim_vehicle_profile(platform_code);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_current_carrier_id
ON dim.dim_vehicle_profile(current_carrier_id);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_current_process_area
ON dim.dim_vehicle_profile(current_process_area);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_retention_pass
ON dim.dim_vehicle_profile(retention_checkpoint_pass_at);

CREATE INDEX IF NOT EXISTS idx_dim_vp_pvn
ON dim.dim_vehicle_profile(project_vehicle_no);
```

### 6.5 创建 ods.carbody_history

```sql
-- 显式创建以确保时间字段为 TIMESTAMPTZ
CREATE TABLE IF NOT EXISTS ods.carbody_history (
    "ID"               NUMERIC PRIMARY KEY,
    "DATE_EVT"         TIMESTAMPTZ,
    "SHIFT_NR"         NUMERIC,
    "RW_STATION_ID"    VARCHAR(64),
    "RW_STATION_STATUS" NUMERIC,
    "SKID_ID"          VARCHAR(64),
    "SKID_TYPE"        VARCHAR(64),
    "SKID_IS_EMPTY"    NUMERIC,
    "BODY_ID"          VARCHAR(14),
    "BODY_TYPE"        VARCHAR(12),
    "MDS_DATA"         VARCHAR,
    "MDS_TELEGRAM_TYPE" VARCHAR(10),
    "FK_ERP_HIST_ID"   NUMERIC,
    "CYCLE_NUM"        VARCHAR(64),
    "PRODUCTION_SEGMENT_ID" NUMERIC,
    "ETL_MODIFY_DATE"  TIMESTAMPTZ,
    "ETL_SOURCE_ID"    NUMERIC
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ods_carbody_body_id         ON ods.carbody_history("BODY_ID");
CREATE INDEX IF NOT EXISTS idx_ods_carbody_date_evt        ON ods.carbody_history("DATE_EVT");
CREATE INDEX IF NOT EXISTS idx_ods_carbody_body_id_date    ON ods.carbody_history("BODY_ID", "DATE_EVT");
CREATE INDEX IF NOT EXISTS idx_ods_carbody_rw_station      ON ods.carbody_history("RW_STATION_ID");
```

### 6.6 创建 dim.carbody_registry

```sql
-- 首/末过站聚合表，78 前缀过滤，每车一行
-- MDS_DATA 提取规则见 carbody_history/MDS数据提取规则.md
CREATE TABLE IF NOT EXISTS dim.carbody_registry (
    vehicle_id         VARCHAR(14) PRIMARY KEY,
    first_seen_at      TIMESTAMPTZ NOT NULL,    -- 首次过站时间
    last_seen_at       TIMESTAMPTZ NOT NULL,    -- 末次过站时间
    first_rw_station   VARCHAR(64),             -- 首次过站读写站
    last_rw_station    VARCHAR(64),             -- 末次过站读写站
    first_body_type    VARCHAR(12),             -- 入口车身类型
    last_body_type     VARCHAR(12),             -- 出口车身类型
    station_pass_count INTEGER,                 -- 总过站次数
    body_type          VARCHAR(5),              -- MDS_DATA 45-49
    platform_code      VARCHAR(3),              -- MDS_DATA 51-53
    color_code         VARCHAR(4),              -- MDS_DATA 59-62
    black_roof_flag    VARCHAR(1),              -- MDS_DATA 137
    rework_flag        VARCHAR(1),              -- MDS_DATA 139
    reserved_1         VARCHAR(1),              -- MDS_DATA 138
    reserved_2         VARCHAR(1),              -- MDS_DATA 140
    retention_checkpoint_station VARCHAR(64),   -- 滞留监控关键读写站编码
    retention_checkpoint_pass_at TIMESTAMPTZ,   -- 滞留监控关键读写站过站时间
    project_vehicle_no VARCHAR(64),             -- 项目车编号 (基于 13位 composite_pin_no 匹配关联)
    etl_loaded_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_dim_carbody_vp_first_seen   ON dim.carbody_registry(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_dim_carbody_vp_last_seen    ON dim.carbody_registry(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_dim_carbody_vp_first_station ON dim.carbody_registry(first_rw_station);
CREATE INDEX IF NOT EXISTS idx_dim_carbody_vp_last_station  ON dim.carbody_registry(last_rw_station);
CREATE INDEX IF NOT EXISTS idx_dim_carbody_retention_pass   ON dim.carbody_registry(retention_checkpoint_pass_at);
CREATE INDEX IF NOT EXISTS idx_dim_carbody_pvn              ON dim.carbody_registry(project_vehicle_no);
```

如果表已存在（老版本升级），通过 ALTER TABLE 补齐 MDS 字段与滞留监控关键节点字段：

```sql
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS body_type       VARCHAR(5);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS platform_code   VARCHAR(3);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS color_code      VARCHAR(4);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS black_roof_flag VARCHAR(1);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS rework_flag     VARCHAR(1);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS reserved_1      VARCHAR(1);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS reserved_2      VARCHAR(1);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS retention_checkpoint_station VARCHAR(64);
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS retention_checkpoint_pass_at TIMESTAMPTZ;
ALTER TABLE dim.carbody_registry ADD COLUMN IF NOT EXISTS project_vehicle_no VARCHAR(64);

ALTER TABLE dim.dim_vehicle_profile ADD COLUMN IF NOT EXISTS retention_checkpoint_station VARCHAR(64);
ALTER TABLE dim.dim_vehicle_profile ADD COLUMN IF NOT EXISTS retention_checkpoint_pass_at TIMESTAMPTZ;
ALTER TABLE dim.dim_vehicle_profile ADD COLUMN IF NOT EXISTS project_vehicle_no VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_dim_carbody_pvn ON dim.carbody_registry(project_vehicle_no);
CREATE INDEX IF NOT EXISTS idx_dim_vp_pvn      ON dim.dim_vehicle_profile(project_vehicle_no);
```

### 6.7 聚合存储过程 meta.refresh_carbody_dim

负责从 `ods.carbody_history` 增量拉取数据并执行复杂聚合计算（包含查找首次与末次过站时间、首次与末次过站读写站名称、车身类型、MDS 7 个关键字段翻译及汇总统计过站次数），然后以 UPSERT 幂等方式写入维度表 `dim.carbody_registry`。同时记录详细审计日志。

```sql
-- DROP PROCEDURE meta.refresh_carbody_dim();

CREATE OR REPLACE PROCEDURE meta.refresh_carbody_dim()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
  v_log_id      BIGINT;
  v_last_dim_id NUMERIC;
  v_new_count   INTEGER;
BEGIN
  INSERT INTO meta.sync_job_log(job_name, status, message)
  VALUES ('refresh_carbody_dim', 'running', 'start')
  RETURNING id INTO v_log_id;

  -- 0. 贴源同步 FIS 项目车订单 FDW 数据至本地 ODS 物理表
  INSERT INTO ods.ods_fis_project_vehicle_orders (
      project_vehicle_no, file_name, project_stage, block_no, code_6bit, 
      color_interior, kom_no, knr_no, pin_no, pin_prefix, composite_pin_no, 
      created_at, updated_at
  )
  SELECT 
      project_vehicle_no, file_name, project_stage, block_no, code_6bit, 
      color_interior, kom_no, knr_no, pin_no, pin_prefix, composite_pin_no, 
      created_at, updated_at
  FROM src_project_vehicle.project_vehicle_orders
  ON CONFLICT (project_vehicle_no) DO UPDATE SET
      file_name        = EXCLUDED.file_name,
      project_stage    = EXCLUDED.project_stage,
      block_no         = EXCLUDED.block_no,
      code_6bit        = EXCLUDED.code_6bit,
      color_interior   = EXCLUDED.color_interior,
      kom_no           = EXCLUDED.kom_no,
      knr_no           = EXCLUDED.knr_no,
      pin_no           = EXCLUDED.pin_no,
      pin_prefix       = EXCLUDED.pin_prefix,
      composite_pin_no = EXCLUDED.composite_pin_no,
      updated_at       = EXCLUDED.updated_at;

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
  ),
  last_checkpoint AS (
      SELECT DISTINCT ON ("BODY_ID")
          "BODY_ID",
          "RW_STATION_ID" AS retention_checkpoint_station,
          "DATE_EVT"       AS retention_checkpoint_pass_at
      FROM new_records
      WHERE "RW_STATION_ID" IN ('1J440RB', 'K3IS140', 'K2IS075', 'K1IS135')
      ORDER BY "BODY_ID", "DATE_EVT" DESC
  )
  INSERT INTO dim.carbody_registry (
      vehicle_id, first_seen_at, last_seen_at,
      first_rw_station, last_rw_station,
      first_body_type, last_body_type, station_pass_count,
      body_type, platform_code, color_code,
      black_roof_flag, rework_flag, reserved_1, reserved_2,
      retention_checkpoint_station, retention_checkpoint_pass_at
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
      lm.mds_reserved_2,
      lc.retention_checkpoint_station,
      lc.retention_checkpoint_pass_at
  FROM vehicle_agg va
  LEFT JOIN last_mds lm ON lm."BODY_ID" = va.vehicle_id
  LEFT JOIN last_checkpoint lc ON lc."BODY_ID" = va.vehicle_id
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
      reserved_2         = EXCLUDED.reserved_2,
      retention_checkpoint_station = COALESCE(EXCLUDED.retention_checkpoint_station, dim.carbody_registry.retention_checkpoint_station),
      retention_checkpoint_pass_at = COALESCE(EXCLUDED.retention_checkpoint_pass_at, dim.carbody_registry.retention_checkpoint_pass_at);

  GET DIAGNOSTICS v_new_count = ROW_COUNT;

  -- 2.1 纯粹基于 13 位 composite_pin_no 精确匹配更新 dim.carbody_registry.project_vehicle_no
  UPDATE dim.carbody_registry cr
  SET project_vehicle_no = pvo.project_vehicle_no
  FROM ods.ods_fis_project_vehicle_orders pvo
  WHERE pvo.composite_pin_no IS NOT NULL 
    AND pvo.composite_pin_no <> '' 
    AND LEFT(cr.vehicle_id, 13) = pvo.composite_pin_no
    AND (cr.project_vehicle_no IS NULL OR cr.project_vehicle_no <> pvo.project_vehicle_no);

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
  -- GRANT SELECT ON ods.carbody_history TO agent_ro;
  -- GRANT SELECT ON dim.carbody_registry TO agent_ro;

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
$procedure$
;
```

### 6.8 创建事实层与分析层物化视图

如果数据库中已经存在旧版同名物化视图，而你需要升级到本手册对应的最新定义，请先按依赖顺序删除旧对象，再执行下面 SQL：

```sql
DROP MATERIALIZED VIEW IF EXISTS mart.mart_abnormal_vehicle_current;
DROP MATERIALIZED VIEW IF EXISTS mart.mart_position_current_overview;
DROP MATERIALIZED VIEW IF EXISTS mart.mart_vehicle_quality_360;
DROP MATERIALIZED VIEW IF EXISTS fct.fct_vehicle_defect_enriched;
DROP MATERIALIZED VIEW IF EXISTS fct.fct_vehicle_defect_detection;
DROP MATERIALIZED VIEW IF EXISTS fct.fct_abnormal_vehicle_current;
DROP MATERIALIZED VIEW IF EXISTS fct.fct_vehicle_position_current;
DROP MATERIALIZED VIEW IF EXISTS fct.fct_position_current_all;
```

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_position_current_all AS
SELECT
  id AS position_id,
  plc,
  tag,
  rb_index,
  COALESCE(plc, '') || COALESCE(rb_index, '') AS full_rb_code,
  remark,
  process_area,
  carrier_id,
  carrier_type,
  NULLIF(trim(vehicle_id), '') AS vehicle_id,
  body_type,
  color_code,
  platform_code,
  black_roof_flag,
  rework_flag,
  raw_data,
  position_created_at,
  vehicle_updated_at,
  CASE
    WHEN NULLIF(trim(vehicle_id), '') LIKE '782026%'
         AND COALESCE(body_type, '') <> '-----' THEN 'product_vehicle'
    ELSE 'abnormal_vehicle'
  END AS entity_type,
  CASE
    WHEN NULLIF(trim(vehicle_id), '') = '--------------' THEN 'empty_vehicle_id_with_carrier'
    WHEN COALESCE(body_type, '') = '-----'
         AND NULLIF(trim(vehicle_id), '') LIKE '782026%' THEN 'undefined_body_type_with_carrier'
    WHEN NULLIF(trim(vehicle_id), '') IS NULL THEN 'blank_vehicle_id_with_carrier'
    WHEN NULLIF(trim(vehicle_id), '') NOT LIKE '782026%' THEN 'non_product_prefix'
    ELSE NULL
  END AS abnormal_type
FROM ods.rb_position_data
WHERE COALESCE(NULLIF(trim(carrier_id), ''), '0') <> '0'
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_position_current_all_position_id
ON fct.fct_position_current_all(position_id);

CREATE INDEX IF NOT EXISTS idx_fct_position_current_all_vehicle_id
ON fct.fct_position_current_all(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_fct_position_current_all_carrier_id
ON fct.fct_position_current_all(carrier_id);

CREATE INDEX IF NOT EXISTS idx_fct_position_current_all_process_area
ON fct.fct_position_current_all(process_area);

CREATE INDEX IF NOT EXISTS idx_fct_position_current_all_entity_type
ON fct.fct_position_current_all(entity_type, abnormal_type);

CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_vehicle_position_current AS
SELECT DISTINCT ON (vehicle_id)
  vehicle_id,
  position_id,
  plc,
  tag,
  rb_index,
  full_rb_code,
  remark,
  process_area,
  carrier_id,
  carrier_type,
  body_type,
  color_code,
  platform_code,
  black_roof_flag,
  rework_flag,
  raw_data,
  position_created_at,
  vehicle_updated_at
FROM fct.fct_position_current_all
WHERE entity_type = 'product_vehicle'
  AND vehicle_id LIKE '782026%'
ORDER BY vehicle_id, vehicle_updated_at DESC NULLS LAST, position_created_at DESC, position_id DESC
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_vehicle_position_current_vehicle_id
ON fct.fct_vehicle_position_current(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_position_current_carrier_id
ON fct.fct_vehicle_position_current(carrier_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_position_current_process_area
ON fct.fct_vehicle_position_current(process_area);

CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_vehicle_defect_detection AS
SELECT
  history_id,
  trim(serial_number) AS vehicle_id,
  model,
  type_name,
  black_roof,
  date_time AS detect_time,
  color_code,
  tunnel,
  cycle,
  station_1_defect_count,
  station_2_defect_count,
  station_3_defect_count,
  station_4_defect_count,
  station_5_defect_count,
  total_defect_count
FROM ods.history_station_defect_summary
WHERE serial_number IS NOT NULL
  AND trim(serial_number) <> ''
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_vehicle_defect_detection_history_id
ON fct.fct_vehicle_defect_detection(history_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_detection_vehicle_id
ON fct.fct_vehicle_defect_detection(vehicle_id);

-- ---------------------------------------------------------
-- fct.fct_vehicle_defect_enriched
-- 以 carbody 为中心，LEFT JOIN 缺陷事件，保留双源属性
-- ---------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_vehicle_defect_enriched AS
SELECT
  -- ===== carbody 权威车身维度（驱动表）=====
  cvp.vehicle_id,
  cvp.body_type,
  cvp.platform_code,
  cvp.color_code,
  cvp.black_roof_flag,
  cvp.rework_flag,
  cvp.reserved_1,
  cvp.reserved_2,
  cvp.first_seen_at,
  cvp.last_seen_at,
  cvp.first_rw_station,
  cvp.last_rw_station,
  cvp.first_body_type,
  cvp.last_body_type,
  cvp.station_pass_count,
  cvp.retention_checkpoint_station,
  cvp.retention_checkpoint_pass_at,
  cvp.project_vehicle_no,                            -- 项目车编号 (关联项目车生产订单明细)

  -- ===== 缺陷检测事件（可为 NULL）=====
  d.history_id,
  d.model                     AS defect_model,
  d.type_name                 AS defect_type_name,
  d.black_roof                AS defect_black_roof,
  d.color_code                AS defect_color_code,
  d.date_time                 AS detect_time,
  d.tunnel,
  d.cycle,
  d.station_1_defect_count,
  d.station_2_defect_count,
  d.station_3_defect_count,
  d.station_4_defect_count,
  d.station_5_defect_count,
  d.total_defect_count,

  -- ===== 检测覆盖标记 =====
  CASE WHEN d.history_id IS NOT NULL THEN TRUE ELSE FALSE END AS has_defect_record

FROM dim.carbody_registry cvp
LEFT JOIN ods.history_station_defect_summary d
  -- 性能优化：此处不使用 trim() 以利用 ods 层的索引。要求 ODS 加载时已完成数据清洗。
  ON cvp.vehicle_id = d.serial_number
  AND d.serial_number <> ''
WITH NO DATA;

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_vehicle_id
ON fct.fct_vehicle_defect_enriched(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_detect_time
ON fct.fct_vehicle_defect_enriched(detect_time);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_body_type
ON fct.fct_vehicle_defect_enriched(body_type);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_has_defect
ON fct.fct_vehicle_defect_enriched(has_defect_record);

-- UNIQUE INDEX：支持 REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_unique
ON fct.fct_vehicle_defect_enriched(vehicle_id, COALESCE(history_id, -1));


CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_abnormal_vehicle_current AS
SELECT
  position_id,
  plc,
  tag,
  rb_index,
  full_rb_code,
  remark,
  process_area,
  carrier_id,
  carrier_type,
  vehicle_id,
  body_type,
  color_code,
  platform_code,
  black_roof_flag,
  rework_flag,
  raw_data,
  position_created_at,
  vehicle_updated_at,
  entity_type,
  abnormal_type,
  CASE abnormal_type
    WHEN 'non_product_prefix' THEN 'carrier_id 非 0，但 vehicle_id 前缀不是 782026。'
    WHEN 'empty_vehicle_id_with_carrier' THEN 'carrier_id 非 0，但 vehicle_id 为 --------------。'
    WHEN 'blank_vehicle_id_with_carrier' THEN 'carrier_id 非 0，但 vehicle_id 为空。'
    WHEN 'undefined_body_type_with_carrier' THEN 'carrier_id 非 0，vehicle_id 为产品前缀，但 body_type 为 -----。'
    ELSE 'carrier_id 非 0，但当前占位不满足正式产品车规则。'
  END AS abnormal_reason
FROM fct.fct_position_current_all
WHERE entity_type = 'abnormal_vehicle'
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_abnormal_vehicle_current_position_id
ON fct.fct_abnormal_vehicle_current(position_id);

CREATE INDEX IF NOT EXISTS idx_fct_abnormal_vehicle_current_abnormal_type
ON fct.fct_abnormal_vehicle_current(abnormal_type);

CREATE INDEX IF NOT EXISTS idx_fct_abnormal_vehicle_current_carrier_id
ON fct.fct_abnormal_vehicle_current(carrier_id);

CREATE INDEX IF NOT EXISTS idx_fct_abnormal_vehicle_current_vehicle_id
ON fct.fct_abnormal_vehicle_current(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_fct_abnormal_vehicle_current_process_area
ON fct.fct_abnormal_vehicle_current(process_area);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mart_vehicle_quality_360 AS
SELECT
  -- ===== 缺陷检测明细（源自富集表，未检车辆对应值为 NULL） =====
  e.history_id,
  e.vehicle_id,
  e.detect_time,
  e.defect_model,
  e.defect_type_name,
  e.defect_black_roof,
  e.defect_color_code,
  e.tunnel,
  e.cycle,
  e.station_1_defect_count,
  e.station_2_defect_count,
  e.station_3_defect_count,
  e.station_4_defect_count,
  e.station_5_defect_count,
  e.total_defect_count,
  e.has_defect_record,                               -- 是否存在缺陷检测记录 (TRUE/FALSE)

  -- ===== 车身维度背景属性 =====
  e.body_type,
  bt.type_name AS tracking_type_name,                -- 车型中文名称
  e.color_code AS tracking_color_code,
  cc.color_name AS tracking_color_name,              -- 颜色中文名称
  e.platform_code,
  vp.platform_name,                                  -- 平台中文名称
  e.black_roof_flag,
  e.rework_flag,
  e.project_vehicle_no,                              -- 项目车编号 (透传自 carbody/enriched)
  e.first_seen_at AS carbody_first_seen_at,          -- 首次过站读写站时间
  e.last_seen_at AS carbody_last_seen_at,            -- 末次过站读写站时间
  e.first_rw_station AS carbody_first_rw_station,    -- 首次过站读写站
  e.last_rw_station AS carbody_last_rw_station,      -- 末次过站读写站
  e.station_pass_count AS carbody_station_pass_count,-- 累计过站读写站总频次
  e.retention_checkpoint_station AS carbody_retention_checkpoint_station,  -- 滞留监控关键读写站编码
  e.retention_checkpoint_pass_at AS carbody_retention_checkpoint_pass_at,  -- 滞留监控关键读写站过站时间

  -- ===== 实时位置追踪（源自滚床事实，已下线则为 NULL） =====
  p.process_area,
  p.plc,
  p.rb_index,
  p.full_rb_code,
  p.carrier_id,
  p.carrier_type,
  ct.type_name_cn AS carrier_type_name_cn,           -- 载体中文译名
  p.position_created_at,
  p.vehicle_updated_at
FROM fct.fct_vehicle_defect_enriched e
LEFT JOIN fct.fct_vehicle_position_current p
  ON p.vehicle_id = e.vehicle_id
LEFT JOIN ods.carrier_types ct
  ON ct.type_code = p.carrier_type
LEFT JOIN ods.vehicle_body_types bt
  ON bt.body_type = e.body_type
LEFT JOIN ods.vehicle_color_codes cc
  ON cc.color_code = e.color_code
LEFT JOIN ods.vehicle_platforms vp
  ON vp.platform_code = e.platform_code
WITH NO DATA;

-- 重新创建必需的索引以支持高频并发刷新（CONCURRENTLY）
CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_unique ON mart.mart_vehicle_quality_360(vehicle_id, COALESCE(history_id, -1));
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_vehicle_id ON mart.mart_vehicle_quality_360(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_detect_time ON mart.mart_vehicle_quality_360(detect_time);
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_process_area ON mart.mart_vehicle_quality_360(process_area);

CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_vehicle_id
ON mart.mart_vehicle_quality_360(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_detect_time
ON mart.mart_vehicle_quality_360(detect_time);

CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_process_area
ON mart.mart_vehicle_quality_360(process_area);

CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_carrier_id
ON mart.mart_vehicle_quality_360(carrier_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mart_abnormal_vehicle_current AS
SELECT
  a.position_id,
  a.vehicle_id,
  a.abnormal_type,
  a.abnormal_reason,
  a.process_area,
  dpa.description AS process_area_description,
  dpa.sort_order AS process_area_sort_order,
  a.carrier_id,
  a.carrier_type,
  ct.type_name_cn AS carrier_type_name_cn,
  a.plc,
  a.rb_index,
  a.full_rb_code,
  a.remark,
  a.body_type,
  bt.type_name AS tracking_type_name,
  a.color_code,
  cc.color_name AS tracking_color_name,
  a.platform_code,
  vp.platform_name,
  a.black_roof_flag,
  a.rework_flag,
  a.position_created_at,
  a.vehicle_updated_at
FROM fct.fct_abnormal_vehicle_current a
LEFT JOIN dim.dim_process_area dpa
  ON dpa.process_area_name = a.process_area
LEFT JOIN ods.carrier_types ct
  ON ct.type_code = a.carrier_type
LEFT JOIN ods.vehicle_body_types bt
  ON bt.body_type = a.body_type
LEFT JOIN ods.vehicle_color_codes cc
  ON cc.color_code = a.color_code
LEFT JOIN ods.vehicle_platforms vp
  ON vp.platform_code = a.platform_code
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_abnormal_vehicle_current_position_id
ON mart.mart_abnormal_vehicle_current(position_id);

CREATE INDEX IF NOT EXISTS idx_mart_abnormal_vehicle_current_abnormal_type
ON mart.mart_abnormal_vehicle_current(abnormal_type);

CREATE INDEX IF NOT EXISTS idx_mart_abnormal_vehicle_current_carrier_id
ON mart.mart_abnormal_vehicle_current(carrier_id);

CREATE INDEX IF NOT EXISTS idx_mart_abnormal_vehicle_current_process_area
ON mart.mart_abnormal_vehicle_current(process_area);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mart_position_current_overview AS
SELECT
  p.position_id,
  p.entity_type,
  CASE
    WHEN p.entity_type = 'product_vehicle' THEN '正式产品车'
    ELSE '异常车'
  END AS entity_type_name,
  CASE
    WHEN p.entity_type = 'product_vehicle' THEN 'product_vehicle'
    ELSE COALESCE(a.abnormal_type, p.abnormal_type, 'unknown_abnormal')
  END AS vehicle_status_code,
  CASE
    WHEN p.entity_type = 'product_vehicle' THEN '正式产品车'
    ELSE COALESCE(a.abnormal_reason, 'carrier_id 非 0，但当前占位不满足正式产品车规则。')
  END AS vehicle_status_name,
  COALESCE(a.abnormal_type, p.abnormal_type) AS abnormal_type,
  a.abnormal_reason,
  p.process_area,
  dpa.description AS process_area_description,
  dpa.sort_order AS process_area_sort_order,
  p.carrier_id,
  p.carrier_type,
  ct.type_name_cn AS carrier_type_name_cn,
  p.plc,
  p.tag,
  p.rb_index,
  p.full_rb_code,
  p.remark,
  p.vehicle_id,
  p.body_type,
  bt.type_name AS tracking_type_name,
  p.color_code,
  cc.color_name AS tracking_color_name,
  p.platform_code,
  vp.platform_name,
  p.black_roof_flag,
  p.rework_flag,
  CASE
    WHEN COALESCE(p.black_roof_flag, '') IN ('1', 'Y', 'y', 'T', 't') THEN TRUE
    ELSE FALSE
  END AS is_black_roof,
  CASE
    WHEN COALESCE(p.rework_flag, '') IN ('1', 'Y', 'y', 'T', 't') THEN TRUE
    ELSE FALSE
  END AS is_rework,
  p.position_created_at,
  p.vehicle_updated_at
FROM fct.fct_position_current_all p
LEFT JOIN fct.fct_abnormal_vehicle_current a
  ON a.position_id = p.position_id
LEFT JOIN dim.dim_process_area dpa
  ON dpa.process_area_name = p.process_area
LEFT JOIN ods.carrier_types ct
  ON ct.type_code = p.carrier_type
LEFT JOIN ods.vehicle_body_types bt
  ON bt.body_type = p.body_type
LEFT JOIN ods.vehicle_color_codes cc
  ON cc.color_code = p.color_code
LEFT JOIN ods.vehicle_platforms vp
  ON vp.platform_code = p.platform_code
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_position_current_overview_position_id
ON mart.mart_position_current_overview(position_id);

CREATE INDEX IF NOT EXISTS idx_mart_position_current_overview_entity_type
ON mart.mart_position_current_overview(entity_type, abnormal_type);

CREATE INDEX IF NOT EXISTS idx_mart_position_current_overview_process_area
ON mart.mart_position_current_overview(process_area);

CREATE INDEX IF NOT EXISTS idx_mart_position_current_overview_carrier_id
ON mart.mart_position_current_overview(carrier_id);

CREATE INDEX IF NOT EXISTS idx_mart_position_current_overview_vehicle_id
ON mart.mart_position_current_overview(vehicle_id);
```

### 6.9 授权

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA ods, dim, fct, mart, meta TO agent_ro;
GRANT SELECT ON fct.fct_vehicle_defect_enriched TO agent_ro; -- 明确授予新视图权限
ALTER DEFAULT PRIVILEGES IN SCHEMA ods, dim, fct, mart, meta
GRANT SELECT ON TABLES TO agent_ro;
```


## 7. 最新正式版一键刷新过程

以下过程是当前数据库已经验证通过的正式刷新版本。

```sql
CREATE OR REPLACE PROCEDURE meta.refresh_analytics_all()
LANGUAGE plpgsql
AS $$
DECLARE
  v_log_id BIGINT;
BEGIN
  INSERT INTO meta.sync_job_log(job_name, status, message)
  VALUES ('refresh_analytics_all', 'running', 'start')
  RETURNING id INTO v_log_id;

  TRUNCATE TABLE
    ods.process_areas,
    ods.carrier_types,
    ods.vehicle_body_types,
    ods.vehicle_color_codes,
    ods.vehicle_platforms,
    ods.rb_position_data,
    ods.history_station_defect_summary,
    ods.ods_fis_project_vehicle_orders,
    dim.dim_process_area,
    dim.dim_vehicle_profile;

  INSERT INTO ods.process_areas SELECT * FROM src_rb.process_areas;
  INSERT INTO ods.carrier_types SELECT * FROM src_rb.carrier_types;
  INSERT INTO ods.vehicle_body_types SELECT * FROM src_rb.vehicle_body_types;
  INSERT INTO ods.vehicle_color_codes SELECT * FROM src_rb.vehicle_color_codes;
  INSERT INTO ods.vehicle_platforms SELECT * FROM src_rb.vehicle_platforms;
  INSERT INTO ods.rb_position_data SELECT * FROM src_rb.rb_position_data;
  INSERT INTO ods.history_station_defect_summary SELECT * FROM src_defect.history_station_defect_summary;

  -- 贴源同步 FIS 项目车订单数据
  INSERT INTO ods.ods_fis_project_vehicle_orders SELECT * FROM src_project_vehicle.project_vehicle_orders
  ON CONFLICT (project_vehicle_no) DO UPDATE SET
    file_name = EXCLUDED.file_name,
    project_stage = EXCLUDED.project_stage,
    block_no = EXCLUDED.block_no,
    code_6bit = EXCLUDED.code_6bit,
    color_interior = EXCLUDED.color_interior,
    kom_no = EXCLUDED.kom_no,
    knr_no = EXCLUDED.knr_no,
    pin_no = EXCLUDED.pin_no,
    pin_prefix = EXCLUDED.pin_prefix,
    composite_pin_no = EXCLUDED.composite_pin_no,
    updated_at = EXCLUDED.updated_at;

  -- 触发 carbody 维表匹配刷新
  CALL meta.refresh_carbody_dim();

  -- 刷新事实层与集市物化视图
  REFRESH MATERIALIZED VIEW fct.fct_position_current_all;
  REFRESH MATERIALIZED VIEW fct.fct_vehicle_position_current;
  REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_detection;
  REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched;
  REFRESH MATERIALIZED VIEW fct.fct_abnormal_vehicle_current;
  REFRESH MATERIALIZED VIEW mart.mart_vehicle_quality_360;

  -- 更新区域维度表
  INSERT INTO dim.dim_process_area (
    process_area_name, source_area_id, description, sort_order, created_at, updated_at, etl_loaded_at
  )
  SELECT area_name, id, description, sort_order, created_at, updated_at, now()
  FROM ods.process_areas;

  -- 升级：多源合并写入车辆主画像维度表（支持滚床位置追踪 + 缺陷系统 + MES车身过站历史 + FIS项目车）
  INSERT INTO dim.dim_vehicle_profile (
    vehicle_id, body_type, tracking_type_name, defect_model, defect_type_name,
    platform_code, platform_name, color_code, color_name, is_black_roof,
    is_rework, has_defect_record, black_roof_raw_tracking, black_roof_raw_defect,
    tracking_last_seen_at, defect_last_seen_at, carbody_first_seen_at, carbody_last_seen_at,
    carbody_first_rw_station, carbody_last_rw_station, carbody_station_pass_count,
    carbody_reserved_1, carbody_reserved_2, retention_checkpoint_station, retention_checkpoint_pass_at,
    project_vehicle_no,
    current_position_id, current_carrier_id, current_carrier_type, current_process_area,
    current_full_rb_code, current_position_updated_at, etl_loaded_at
  )
  WITH latest_tracking AS (
    -- 获取滚床上的在产车辆当前最新位置信息
    SELECT
      vehicle_id, position_id, carrier_id, carrier_type, process_area, full_rb_code,
      body_type, color_code, platform_code, black_roof_flag, vehicle_updated_at
    FROM fct.fct_vehicle_position_current
  ),
  latest_defect AS (
    -- 获取每个车辆最新的一条缺陷检测结果
    SELECT DISTINCT ON (trim(serial_number))
      trim(serial_number) AS vehicle_id,
      model AS defect_model,
      type_name AS defect_type_name,
      black_roof AS black_roof_raw_defect,
      color_code AS defect_color_code,
      date_time AS defect_last_seen_at,
      history_id
    FROM ods.history_station_defect_summary
    WHERE serial_number IS NOT NULL AND trim(serial_number) <> ''
    ORDER BY trim(serial_number), date_time DESC NULLS LAST, history_id DESC
  ),
  latest_carbody AS (
    -- 获取每个车身在 MES 系统中的累计过站状态
    SELECT
      vehicle_id, body_type, platform_code, color_code, black_roof_flag, rework_flag,
      first_seen_at, last_seen_at, first_rw_station, last_rw_station, station_pass_count,
      reserved_1, reserved_2, retention_checkpoint_station, retention_checkpoint_pass_at,
      project_vehicle_no
    FROM dim.carbody_registry
  ),
  vehicle_union AS (
    -- 核心升级：三源并集，确保已下线且漏检的车不丢失
    SELECT vehicle_id FROM latest_tracking
    UNION
    SELECT vehicle_id FROM latest_defect
    UNION
    SELECT vehicle_id FROM latest_carbody
  )
  SELECT
    u.vehicle_id,
    -- 车型字段级联合并（优先滚床跟踪，其次车身历史）
    COALESCE(t.body_type, c.body_type) AS body_type,
    bt.type_name AS tracking_type_name,
    
    -- 缺陷数据
    d.defect_model,
    d.defect_type_name,
    
    -- 平台字段级联合并
    COALESCE(t.platform_code, c.platform_code) AS platform_code,
    vp.platform_name,
    
    -- 颜色代码级联合并（优先滚床跟踪，其次缺陷，再次车身历史）
    COALESCE(t.color_code, d.defect_color_code, c.color_code) AS color_code,
    cc.color_name,
    
    -- 是否黑车顶（任意一源标记为真即为真）
    CASE
      WHEN COALESCE(t.black_roof_flag, '') IN ('1', 'Y', 'y', 'T', 't') THEN TRUE
      WHEN COALESCE(d.black_roof_raw_defect, '') ILIKE '%黑%' THEN TRUE
      WHEN COALESCE(c.black_roof_flag, '') IN ('1', 'Y', 'y', 'T', 't') THEN TRUE
      ELSE FALSE
    END AS is_black_roof,
    
    -- 新增布尔属性
    CASE WHEN c.rework_flag = '1' THEN TRUE ELSE FALSE END AS is_rework,
    CASE WHEN d.history_id IS NOT NULL THEN TRUE ELSE FALSE END AS has_defect_record,
    
    -- 跟踪和缺陷原始保留字段
    t.black_roof_flag AS black_roof_raw_tracking,
    d.black_roof_raw_defect,
    t.vehicle_updated_at AS tracking_last_seen_at,
    d.defect_last_seen_at,
    
    -- 新增车身物理过站时间与读写站信息
    c.first_seen_at AS carbody_first_seen_at,
    c.last_seen_at AS carbody_last_seen_at,
    c.first_rw_station AS carbody_first_rw_station,
    c.last_rw_station AS carbody_last_rw_station,
    c.station_pass_count AS carbody_station_pass_count,
    c.reserved_1 AS carbody_reserved_1,
    c.reserved_2 AS carbody_reserved_2,
    c.retention_checkpoint_station,
    c.retention_checkpoint_pass_at,
    c.project_vehicle_no,
    
    -- 当前最新滚床位置追踪字段（若下线则为 NULL）
    t.position_id AS current_position_id,
    t.carrier_id AS current_carrier_id,
    t.carrier_type AS current_carrier_type,
    t.process_area AS current_process_area,
    t.full_rb_code AS current_full_rb_code,
    t.vehicle_updated_at AS current_position_updated_at,
    now() AS etl_loaded_at
  FROM vehicle_union u
  LEFT JOIN latest_tracking t ON t.vehicle_id = u.vehicle_id
  LEFT JOIN latest_defect d ON d.vehicle_id = u.vehicle_id
  LEFT JOIN latest_carbody c ON c.vehicle_id = u.vehicle_id
  LEFT JOIN ods.vehicle_body_types bt ON bt.body_type = COALESCE(t.body_type, c.body_type)
  LEFT JOIN ods.vehicle_color_codes cc ON cc.color_code = COALESCE(t.color_code, d.defect_color_code, c.color_code)
  LEFT JOIN ods.vehicle_platforms vp ON vp.platform_code = COALESCE(t.platform_code, c.platform_code);

  -- 刷新汇总层物化视图
  REFRESH MATERIALIZED VIEW mart.mart_vehicle_quality_360;
  REFRESH MATERIALIZED VIEW mart.mart_abnormal_vehicle_current;
  REFRESH MATERIALIZED VIEW mart.mart_position_current_overview;

  INSERT INTO meta.refresh_watermark(source_name, watermark_value, updated_at)
  VALUES
    ('ods.rb_position_data.max_vehicle_updated_at', (SELECT COALESCE(MAX(vehicle_updated_at)::text, '') FROM ods.rb_position_data), now()),
    ('ods.history_station_defect_summary.max_date_time', (SELECT COALESCE(MAX(date_time)::text, '') FROM ods.history_station_defect_summary), now()),
    ('ods.history_station_defect_summary.max_history_id', (SELECT COALESCE(MAX(history_id)::text, '') FROM ods.history_station_defect_summary), now())
  ON CONFLICT (source_name) DO UPDATE
  SET watermark_value = EXCLUDED.watermark_value,
      updated_at = EXCLUDED.updated_at;

  GRANT SELECT ON ALL TABLES IN SCHEMA ods, dim, fct, mart, meta TO agent_ro;

  UPDATE meta.sync_job_log
  SET finished_at = now(), status = 'success', message = 'done'
  WHERE id = v_log_id;
EXCEPTION WHEN OTHERS THEN
  UPDATE meta.sync_job_log
  SET finished_at = now(), status = 'failed', message = SQLERRM
  WHERE id = v_log_id;
  RAISE;
END;
$$;
```

### 7.2 Carbody 刷新过程的重构与废弃说明

> [!WARNING]
> **⚠️ 架构更新说明（2026-05-17）**：
> 随着 Carbody 链路重构（彻底移除 `postgres_fdw` 外部表连接，改用 Python [refresh_carbody_ods.py](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/carbody_etl/refresh_carbody_ods.py) 直连 SQL Server 抽取），原先设计的 **`meta.refresh_carbody()` 存储过程已完全废弃，请勿在数据库中继续创建或运行该过程！**

#### 为什么废弃？
原存储过程 `meta.refresh_carbody()` 在设计上强耦合了 **从 FDW 外部表向 `ods.carbody_history` 抽取数据** 和 **聚合到 `dim.carbody_registry`** 这两个阶段。

在取消 FDW 链路后，数据库内部已无法直接跨网读取外部 SQL Server，因此该逻辑必须进行彻底的“库内/外解耦”：
1. **第一步（抽取与加载 - ODS Layer）**：移交至外部 Python 调度脚本 [refresh_carbody_ods.py](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/carbody_etl/refresh_carbody_ods.py) 独立执行，直连源库安全抽取。
2. **第二步（维表聚合 - DIM Layer）**：移交至轻量级的库内存储过程 **`meta.refresh_carbody_dim()`** 执行（参见 [第 6.7 节](#67-聚合存储过程-metarefresh_carbody_dim)）。在 Python 写入 ODS 完成后，由脚本自动调用触发。

#### 最新数据链路流转图
```mermaid
graph TD
  SQLServer["SQL Server (源数据库)"] -- "1. Python 直连抽取 (refresh_carbody_ods.py)" --> ODS["ods.carbody_history (本地 ODS 贴源层)"]
  ODS -- "2. 自动调用 CALL meta.refresh_carbody_dim()" --> DIM["dim.carbody_registry (本地车身过站注册维度表)"]
  DIM -- "3. 自动刷新 REFRESH VIEW" --> FCT["fct.fct_vehicle_defect_enriched (缺陷与车身事实富集宽表)"]
```

**UPSERT 语义**：
由 `meta.refresh_carbody_dim()` 保证幂等性：

| 字段 | INSERT（新车） | UPDATE（已有车） |
|------|---------------|------------------|
| `vehicle_id` | 写入 | 不变（PK） |
| `first_seen_at` / `first_rw_station` / `first_body_type` | 写入 | **不更新** |
| `last_seen_at` / `last_rw_station` / `last_body_type` | 写入 | **覆盖** |
| `station_pass_count` | 写入 | **累加**（旧值 + 批次计数） |
| MDS 7 字段 | 写入（末次 MDS_DATA） | **覆盖** |

**全量重刷与手动水位重置**：
若由于网络波动、源数据库回滚或结构变更需要全量重刷数据：

```sql
-- 1. 重置 DIM 水位为 0 且清空本地表
UPDATE meta.refresh_watermark SET watermark_value = '0'
WHERE source_name = 'dim.carbody_registry.last_sync_id';
TRUNCATE TABLE ods.carbody_history;
TRUNCATE TABLE dim.carbody_registry;

-- 2. 重新运行 Python 抽取脚本，或者在手动导入 ODS 后执行：
CALL meta.refresh_carbody_dim();
```

## 8. 首次刷新

首次执行前，先初始化增量水位。根据环境选择：

```sql
-- 新环境（空库）：水位从 0 开始，首次调用即全量
INSERT INTO meta.refresh_watermark(source_name, watermark_value)
VALUES ('ods.carbody_history.max_id', '0')
ON CONFLICT (source_name) DO NOTHING;

-- 老环境（已有全量数据）：跳过全量重刷，从当前最大 ID 开始增量
-- INSERT INTO meta.refresh_watermark(source_name, watermark_value)
-- VALUES ('ods.carbody_history.max_id',
--         (SELECT COALESCE(MAX("ID")::text, '0') FROM ods.carbody_history))
-- ON CONFLICT (source_name) DO NOTHING;
```

```sql
-- analytics 主刷新（包含滚床、基础维表以及除 carbody 之外的所有物化视图重算）
CALL meta.refresh_analytics_all();
```

对于 **Carbody 过站数据链路** 的首次刷新，由于已切为 Python 直连机制，**切勿直接在数据库内调用已废弃的 `CALL meta.refresh_carbody();`**。

请按照以下方式进行首次刷新：

1. **确认增量同步水位已初始化**（新环境从 `0` 开始即为全量抽取）：
```sql
INSERT INTO meta.refresh_watermark(source_name, watermark_value)
VALUES ('ods.carbody_history.max_id', '0')
ON CONFLICT (source_name) DO NOTHING;
```

2. **在外部命令行执行同步脚本**（脚本会自动完成 ODS 增量拉取，并自动调用库内 `CALL meta.refresh_carbody_dim()` 完成维表聚合及下游宽表刷新）：
```powershell
python carbody_etl/refresh_carbody_ods.py
```

## 9. 日常验证 SQL

### 9.1 验证 schema / 表 / 物化视图

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('src_rb','src_defect','ods','dim','fct','mart','meta')
ORDER BY schema_name;

SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema IN ('src_rb','src_defect','ods','dim','fct','mart','meta')
ORDER BY table_schema, table_name;

SELECT schemaname, matviewname
FROM pg_matviews
WHERE schemaname IN ('fct','mart')
ORDER BY schemaname, matviewname;
```

### 9.2 验证数据量

```sql
SELECT count(*) FROM ods.rb_position_data;
SELECT count(*) FROM ods.history_station_defect_summary;
SELECT count(*) FROM dim.dim_process_area;
SELECT count(*) FROM dim.dim_vehicle_profile;
SELECT count(*) FROM fct.fct_position_current_all;
SELECT count(*) FROM fct.fct_vehicle_position_current;
SELECT count(*) FROM fct.fct_abnormal_vehicle_current;
SELECT count(*) FROM fct.fct_vehicle_defect_detection;
SELECT count(*) FROM fct.fct_vehicle_defect_enriched;
SELECT count(*) FROM mart.mart_vehicle_quality_360;
SELECT count(*) FROM mart.mart_abnormal_vehicle_current;
SELECT count(*) FROM mart.mart_position_current_overview;

-- 验证：fct_vehicle_defect_enriched 漏检与重复检测验证
SELECT has_defect_record, count(*) 
FROM fct.fct_vehicle_defect_enriched 
GROUP BY has_defect_record;

-- 验证：属性一致性（同一车身的 carbody 属性不应冲突）
SELECT vehicle_id, count(DISTINCT body_type), count(DISTINCT color_code)
FROM fct.fct_vehicle_defect_enriched
WHERE has_defect_record
GROUP BY vehicle_id
HAVING count(DISTINCT body_type) > 1 OR count(DISTINCT color_code) > 1;
```

### 9.3 验证刷新日志与水位

```sql
SELECT *
FROM meta.sync_job_log
ORDER BY id DESC
LIMIT 5;

SELECT *
FROM meta.refresh_watermark
ORDER BY source_name;
```

### 9.4 验证异常车分类结果

```sql
SELECT abnormal_type, count(*)
FROM fct.fct_abnormal_vehicle_current
GROUP BY abnormal_type
ORDER BY abnormal_type;

SELECT
  position_id,
  vehicle_id,
  carrier_id,
  abnormal_type,
  process_area
FROM fct.fct_abnormal_vehicle_current
ORDER BY vehicle_updated_at DESC NULLS LAST, position_created_at DESC, position_id DESC
LIMIT 20;

SELECT
  entity_type,
  vehicle_status_code,
  count(*)
FROM mart.mart_position_current_overview
GROUP BY entity_type, vehicle_status_code
ORDER BY entity_type, vehicle_status_code;
```

### 9.5 验证 `agent_ro` 权限

```sql
SELECT
  has_schema_privilege('agent_ro', 'mart', 'USAGE') AS mart_usage,
  has_table_privilege('agent_ro', 'mart.mart_vehicle_quality_360', 'SELECT') AS mart_select,
  has_table_privilege('agent_ro', 'mart.mart_abnormal_vehicle_current', 'SELECT') AS abnormal_mart_select,
  has_table_privilege('agent_ro', 'mart.mart_position_current_overview', 'SELECT') AS overview_mart_select,
  has_schema_privilege('agent_ro', 'dim', 'USAGE') AS dim_usage,
  has_table_privilege('agent_ro', 'dim.dim_vehicle_profile', 'SELECT') AS dim_select,
  has_table_privilege('agent_ro', 'fct.fct_position_current_all', 'SELECT') AS position_all_select,
  has_table_privilege('agent_ro', 'fct.fct_vehicle_defect_enriched', 'SELECT') AS defect_enriched_select;
```

### 9.6 验证 carbody 对象

```sql
-- 水位是否存在
SELECT * FROM meta.refresh_watermark
WHERE source_name IN ('ods.carbody_history.max_id', 'dim.carbody_registry.last_sync_at');

-- 对象存在性
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('src_carbody','ods') AND table_name LIKE '%carbody%'
UNION ALL
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'dim' AND table_name = 'carbody_registry';

-- 数据量（期待 ods ~101 万，dim ~1.3 万）
SELECT 'ods.carbody_history' AS tbl, count(*) AS rows FROM ods.carbody_history
UNION ALL
SELECT 'dim.carbody_registry' AS tbl, count(*) AS rows FROM dim.carbody_registry;

-- 首末时间合理性（应为 0）
SELECT count(*) AS invalid_count
FROM dim.carbody_registry
WHERE first_seen_at > last_seen_at;

-- 78 前缀一致性（应为 0）
SELECT count(*) AS non_78_prefix
FROM dim.carbody_registry
WHERE vehicle_id NOT LIKE '78%';

-- vehicle_id 唯一性（应为 0）
SELECT vehicle_id, count(*) AS dup
FROM dim.carbody_registry
GROUP BY vehicle_id HAVING count(*) > 1;

-- MDS 字段非 NULL 率
SELECT
    round(count(body_type)     * 100.0 / count(*), 1) AS body_type_pct,
    round(count(platform_code) * 100.0 / count(*), 1) AS platform_pct,
    round(count(color_code)    * 100.0 / count(*), 1) AS color_pct
FROM dim.carbody_registry;

-- 数据样本
SELECT * FROM dim.carbody_registry ORDER BY first_seen_at DESC LIMIT 10;

-- 刷新日志
SELECT * FROM meta.sync_job_log WHERE job_name = 'refresh_carbody_dim' ORDER BY id DESC LIMIT 5;

-- 增量幂等性：连续执行两次 CALL meta.refresh_carbody_dim()，第二次影响行数（ROW_COUNT）应为 0
```

## 10. 后续怎么执行

### 10.1 手工刷新

后续在日常运维中，主要存在两条相互独立的刷新链路：

1. **常规分析链路（位置与缺陷数据）**：
   ```sql
   -- 刷新滚床数据、缺陷数据及除 carbody 外的基础维表和物化视图
   CALL meta.refresh_analytics_all();
   ```

2. **Carbody 车身过站链路**：
   由于解耦了 FDW，必须在宿主机激活 Conda 环境并运行 Python 脚本：
   ```powershell
   python carbody_etl/refresh_carbody_ods.py
   ```
   *(注：脚本内部会自动触发 `CALL meta.refresh_carbody_dim();` 及宽表刷新)*

### 10.2 Windows 定时任务 (自动化部署)

日常运营中建议通过 Windows 任务计划程序自动调度以上两条链路。

**1. 常规分析链路自动化**：
推荐直接调用仓库中的 PowerShell 包装脚本：
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\defect_database\scripts\refresh_analytics_db.ps1"
```
* 该脚本默认执行 `CALL meta.refresh_analytics_all();`
* 建议通过 `%APPDATA%\postgresql\pgpass.conf` 配置 `agent_ro` 或 `root` 密码。

**2. Carbody 链路自动化**：
需要在任务计划程序中配置触发 Python 脚本。
启动程序：`python`
参数：`carbody_etl/refresh_carbody_ods.py`
*(注：需确保任务计划的执行环境能够加载到必要的 Python 依赖包和 `.env`)*

### 10.3 建议刷新频率

- **滚床占位数据 (`rb_position_data`) 刷新**：建议每 `5` 分钟执行一次 `refresh_analytics_all()` (或单独剥离)。
- **缺陷数据汇总分析**：建议每 `15` 到 `30` 分钟执行一次 `refresh_analytics_all()`。
- **Carbody 增量拉取 (`refresh_carbody_ods.py`)**：建议每 `5` 分钟（由于是增量 UPSERT，日常每次批次仅几十至几百条，开销极低）。
- **Carbody 每周全量兜底**：每周日 03:00 自动执行一次 `python carbody_etl/refresh_carbody_ods.py --full-refresh`，以清理源库因滚动窗口机制已删除的过期过站记录。

## 11. 项目接入

确认 `analytics_db` 跑通后，再做两件事：

1. 在 `.env` 中增加：

```env
ANALYTICS_DATABASE_URL='postgresql://agent_ro:你的密码@localhost:5432/analytics_db'
```

2. 修改项目代码，让 SQL Agent 默认连接 `analytics_db`

## 12. 两个重要提醒

1. 当前 `mart.mart_vehicle_quality_360` 关联的是“缺陷检测”和“车辆当前最新位置”，不是“检测当时位置”。
2. 如果后面要分析“检测时所在区域”或“停留时长与缺陷关系”，下一步要补车辆位置历史快照层，而不是直接依赖当前这张 `mart` 表。
