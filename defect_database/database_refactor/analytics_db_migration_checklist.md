# Analytics DB 新环境迁移清单

修改时间：2026-05-17 Asia/Shanghai

主要修改内容：
- **同步架构升级**：彻底移除 Carbody 的 `postgres_fdw` 外部连接与 `src_carbody` 相关配置。
- **解耦刷新逻辑**：废弃 `meta.refresh_carbody()` 过程，拆分为外部 Python 抽取和本地增量聚合过程 `meta.refresh_carbody_dim()`。
- **环境要求补充**：增加 Python 3 运行环境、依赖项以及 `.env` 变量配置的确认清单。
- **富集宽表校验**：新增车身事实富集宽表 `fct.fct_vehicle_defect_enriched` 的验收规范。

---

## 适用范围

本清单用于在新环境中迁移并落地当前正式版 `analytics_db`。

建议配合以下最新文档一起使用：

- 最终落地手册：
  - [analytics_db_architecture.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
- 源表结构入口：
  - [create_tables_postgresql.sql](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/create_tables_postgresql.sql)

使用原则：

- 本清单负责“顺序、检查点、验收”
- 具体 SQL 以 `analytics_db_architecture.md` 中的正式版本为准
- 若清单与正式手册有冲突，以正式手册为准

---

## 一、迁移前准备

- [ ] **运行环境准备**：
  - [ ] 确认目标机器已安装 Python 3.8+ 运行环境
  - [ ] 确认激活了工作环境（例如 `conda activate websoket`）
  - [ ] 安装核心依赖包：`psycopg2`、`python-tds` (即 `pytds`)、`python-dotenv`
- [ ] **数据库连接确认**：
  - [ ] 确认目标机可以访问 `rollerbed_tracking_db` (FDW)
  - [ ] 确认目标机可以访问 `defect_db` (FDW)
  - [ ] 确认目标机可以跨网直连外部 SQL Server 数据库 (Python 连接)
- [ ] **权限与账号准备**：
  - [ ] 确认你有 PostgreSQL `root` 或等价管理员权限
  - [ ] 确认计划给 `agent_ro` 设置新密码，而不是沿用示例密码
- [ ] **外部配置文件**：
  - [ ] 在项目根目录或 `carbody_etl/` 目录中建立 `.env` 配置文件
  - [ ] 配置 `CARBODY_SOURCE_*` 和 `CARBODY_TARGET_*` 系列独立环境变量（实现读写库的配置隔离）
  - [ ] 如果准备使用 Windows 定时任务，提前为任务运行账号准备 `pgpass.conf`

---

## 二、初始化清单

### 1. 检查数据库与 Schema 是否已存在
- [ ] 在管理库执行 `SELECT datname FROM pg_database WHERE datname = 'analytics_db';`
- [ ] 若不存在，创建 `analytics_db`
- [ ] 创建以下 Schema：
  - [ ] `src_rb`
  - [ ] `src_defect`
  - [ ] `ods`
  - [ ] `dim`
  - [ ] `fct`
  - [ ] `mart`
  - [ ] `meta`
  *(注意：由于废弃了 FDW，不再需要创建 `src_carbody` Schema)*

### 2. 创建只读角色并授权
- [ ] 创建只读角色 `agent_ro`
- [ ] 完成 `CONNECT` 与对 `ods, dim, fct, mart, meta` 的 `USAGE` 授权

### 3. 建立 FDW 外部连接（只连接 2 个业务源库）
- [ ] 执行 `CREATE EXTENSION IF NOT EXISTS postgres_fdw;`
- [ ] 创建 `rollerbed_srv` 连接到 `rollerbed_tracking_db`
- [ ] 创建 `defect_srv` 连接到 `defect_db`
- [ ] 为 `root` 创建对应的 `USER MAPPING`
*(注意：不再创建 `carbody_srv` FDW 连接)*

### 4. 导入外部表
- [ ] 从 `rollerbed_srv` 导入位置、工位等 6 张表到 `src_rb` Schema
- [ ] 从 `defect_srv` 导入 `history_station_defect_summary` 到 `src_defect` Schema
*(注意：不再使用 IMPORT 导入 carbody_history 外部表)*

### 5. 初始化本地 ODS / DIM / FCT / MART / META
- [ ] **创建普通 ODS 表**（通过 `src_rb` 和 `src_defect` 结构复制）
- [ ] **创建 ODS 主键与索引**
- [ ] **创建 `ods.carbody_history` 专用贴源表**：
  - [ ] 字段类型对齐：确认 `"SKID_ID"`、`"CYCLE_NUM"` 为 `VARCHAR(64)` 适配真实源库
  - [ ] 时间类型对齐：确认 `"DATE_EVT"`、`"ETL_MODIFY_DATE"` 为 `TIMESTAMPTZ` 处理时区
- [ ] **创建 `meta.sync_job_log`**
- [ ] **创建 `meta.refresh_watermark` 水位表**
- [ ] **创建维表及事实层物化视图**：
  - [ ] `dim.dim_process_area`
  - [ ] `dim.dim_vehicle_profile`（补齐 `current_*` 字段）
  - [ ] `dim.carbody_registry`（首末过站聚合，包含 7 个 MDS 翻译列及主键索引）
  - [ ] `fct` 层 5 张物化视图（含 `fct_vehicle_defect_enriched` 及其 `UNIQUE INDEX`）
  - [ ] `mart` 层 3 张物化视图
- [ ] 完成 `agent_ro` 对所有表的最终 `SELECT` 授权

### 6. 创建正式库内刷新过程
- [ ] **创建 `meta.refresh_analytics_all()`**：
  - 确认其负责：全量重载位置/缺陷 ODS ➡️ 重建 `dim_process_area` / `dim_vehicle_profile` ➡️ 刷新 `fct` / `mart` 常规物化视图 ➡️ 更新常规水位 ➡️ 记录审计日志。
- [ ] **创建 `meta.refresh_carbody_dim()`**：
  - 确认其负责：从 `ods.carbody_history` 增量读取 ➡️ 对新过站车辆执行 UPSERT 幂等聚合写入 `dim.carbody_registry`（首过不改、末过覆盖、频次累加、MDS 最优列匹配） ➡️ 更新 DIM 水位 ➡️ 记录审计日志。
*(注意：旧版 `meta.refresh_carbody()` 过程已废弃，不要创建)*

---

## 三、首次刷新清单

- [ ] **初始化刷新水位**：
  - [ ] 初始化 ODS 数据拉取水位：
    ```sql
    INSERT INTO meta.refresh_watermark(source_name, watermark_value)
    VALUES ('ods.carbody_history.max_id', '0') ON CONFLICT DO NOTHING;
    ```
  - [ ] 初始化 DIM 维表聚合水位：
    ```sql
    INSERT INTO meta.refresh_watermark(source_name, watermark_value)
    VALUES ('dim.carbody_registry.last_sync_id', '0') ON CONFLICT DO NOTHING;
    ```
- [ ] **执行常规链路刷新**：
  - [ ] 运行 `CALL meta.refresh_analytics_all();`
  - [ ] 验证执行无错，且 `meta.sync_job_log` 日志状态为 `success`
- [ ] **执行 Carbody 首次抽取与同步**：
  - [ ] 在激活 conda 环境的宿主机命令行运行：
    ```powershell
    python carbody_etl/refresh_carbody_ods.py
    ```
  - [ ] 监控命令行日志，确认无 pytds/psycopg2 连接或类型报错
  - [ ] 确认脚本同步完成后，已自动在内部触发了 `CALL meta.refresh_carbody_dim();` 以及下游富集视图的更新

---

## 四、验收清单

### 1. 验证对象是否齐全
- [ ] Schema 列表是否包含：`src_rb / src_defect / ods / dim / fct / mart / meta` *(不应有 src_carbody)*
- [ ] 对象列表：
  - [ ] 维表：`dim_process_area / dim_vehicle_profile / carbody_registry`
  - [ ] 过程：`meta.refresh_analytics_all() / meta.refresh_carbody_dim()` *(不应有 meta.refresh_carbody)*
  - [ ] 事实富集宽表：`fct.fct_vehicle_defect_enriched`

### 2. 验证数据完整性
- [ ] `ods.carbody_history` 成功导入数据（~101 万行）
- [ ] `dim.carbody_registry` 成功增量 UPSERT 数据（~1.3 万行，全为 78 前缀，首过站时间 <= 末过站时间）
- [ ] `fct.fct_vehicle_defect_enriched` 富集了车身首末过站时间、工位及 MDS 字段，且 `has_defect_record` 准确反映是否有缺陷关联

### 3. 验证日志与权限
- [ ] `meta.sync_job_log` 成功记录了 `refresh_carbody_ods` 和 `refresh_carbody_dim` 的执行耗时与插入行数
- [ ] 使用 `agent_ro` 登录，能成功对所有的 `dim, fct, mart` 视图执行 `SELECT`，且没有 `USAGE` 缺失报错

---

## 五、日常刷新清单与定时任务

### 手工刷新方式
- [ ] **位置与缺陷**：`CALL meta.refresh_analytics_all();`
- [ ] **车身过站链路**：命令行执行 `python carbody_etl/refresh_carbody_ods.py`

### 生产自动化部署（Windows 计划任务）
- [ ] **常规链路刷新任务**：
  - [ ] 运行脚本：使用 `defect_database/scripts/refresh_analytics_db.ps1`
  - [ ] 执行频率：建议每 15 分钟执行一次
- [ ] **Carbody 抽取与同步任务**：
  - [ ] 运行脚本：配置定时触发 `python carbody_etl/refresh_carbody_ods.py`
  - [ ] 执行频率：建议每 5 分钟执行一次，以保证准实时性
- [ ] **Carbody 每周兜底全量拉取**：
  - [ ] 执行命令：`python carbody_etl/refresh_carbody_ods.py --full-refresh` (或者设置重置水位)
  - [ ] 执行频率：每周日凌晨 03:00 自动触发，解决源库滚动窗口删除过期行的问题

---

## 六、迁移后应用接入清单

- [ ] **环境变量配置**：
  - [ ] 在接入应用（如 Agent 服务）的 `.env` 中添加：
    ```env
    ANALYTICS_DATABASE_URL='postgresql://agent_ro:你的强密码@localhost:5432/analytics_db'
    ```
  - [ ] 确保在激活的 `conda activate websoket` 环境中能够成功加载并解析该 URL

---

## 七、容易踩坑的点 (Critical Warnings)

- [ ] **【禁止库内直接执行旧同步】**：不要在数据库中调用已废弃的 `CALL meta.refresh_carbody();`，因其不再承担 ODS 抽取职责。
- [ ] **【ODS 表必须手动创建】**：`ods.carbody_history` 不能再使用 `SELECT INTO` 或 FDW 复制，必须采用 PL/pgSQL 显式创建，且 SKID_ID 与 CYCLE_NUM 必须为 VARCHAR，保证数据不溢出。
- [ ] **【时区处理】**：抽取时确认宿主机与 PG 的 session 时区均采用 `Asia/Shanghai`，保证 `TIMESTAMPTZ` 毫秒级对齐。

---

## 八、推荐执行顺序摘要

1. **环境就绪**：安装 Python 依赖库，配置 `.env` 变量。
2. **建库建架构**：创建 `analytics_db` 数据库及 7 个 Schema（除去 `src_carbody`）。
3. **外部挂载**：建立 `rollerbed_srv` 和 `defect_srv` 两个 FDW 挂载和外部表导入。
4. **结构创建**：手动创建 `ods.carbody_history`，依次创建维表、物化视图与水位表。
5. **过程发布**：在数据库中发布 `meta.refresh_analytics_all()` 与 `meta.refresh_carbody_dim()`。
6. **初始化水位**：向 `meta.refresh_watermark` 中插入 ODS 与 DIM 的两项 0 基础水位。
7. **首次同步验证**：
   - 执行 `CALL meta.refresh_analytics_all();`
   - 执行 `python carbody_etl/refresh_carbody_ods.py`（进行全量 ODS 导入与维表聚合转换）
8. **数据与日志验收**：运行 9.1 ~ 9.6 验证 SQL，确认数据和权限无误。
9. **接入 Agent**：在 Agent 的 `.env` 中接入 `agent_ro` 数据库连接。
10. **部署自动化**：在 Windows 任务计划程序中配置定时脚本。
