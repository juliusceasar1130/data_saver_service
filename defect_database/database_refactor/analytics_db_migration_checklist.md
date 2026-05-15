# Analytics DB 新环境迁移清单

修改时间：2026-05-12 Asia/Shanghai

主要修改内容：
- 新增 carbody_history 数据库接入相关初始化、验收、刷新清单项
- 原始变动（2026-04-15）：
  - 补充 Windows 定时任务场景下 `pgpass.conf` 的认证准备与配置说明
  - 新增面向新环境迁移的独立初始化与刷新指导清单
  - 从最终落地手册中提炼执行顺序、验收点与常见注意事项
  - 保留对最终 SQL 手册的引用，避免在清单中重复维护大段 DDL

## 适用范围

本清单用于在新环境中迁移并落地当前正式版 `analytics_db`。

建议配合以下最终文档一起使用：

- 最终落地手册：
  - [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
- 源表结构入口：
  - [create_tables_postgresql.sql](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/create_tables_postgresql.sql)

使用原则：

- 本清单负责“顺序、检查点、验收”
- 具体 SQL 以 `analytics_db_architecture.md` 中的正式版本为准
- 若清单与正式手册有冲突，以正式手册为准

## 一、迁移前准备

- [ ] 确认 PostgreSQL 已安装并可登录
- [ ] 确认目标机可以访问 `rollerbed_tracking_db`
- [ ] 确认目标机可以访问 `defect_db`
- [ ] 确认目标机可以访问 `carbody_history`
- [ ] 确认 `rollerbed_tracking_db` 已具备基础表
- [ ] 确认 `defect_db` 已具备 `history_station_defect_summary`
- [ ] 确认 `carbody_history` 已具备 `carbody_history` 表
- [ ] 确认你有 `root` 或等价管理员权限
- [ ] 确认计划给 `agent_ro` 设置新密码，而不是沿用示例密码
- [ ] 如果准备使用 Windows 定时任务，提前为任务运行账号准备 `pgpass.conf`

建议提前准备这些参数：

- PostgreSQL 主机
- PostgreSQL 端口
- `root` 用户名与密码
- `rollerbed_tracking_db` 连接信息
- `defect_db` 连接信息
- `agent_ro` 新密码

如果你计划使用 Windows 定时任务，推荐同时准备：

- `pgpass.conf` 文件路径
- 任务实际运行账号
- `psql.exe` 的完整路径

`pgpass.conf` 推荐配置：

- Windows 路径：
  - `%APPDATA%\postgresql\pgpass.conf`
- 一行格式：
  - `hostname:port:database:username:password`
- 当前默认环境示例：

```txt
localhost:5432:analytics_db:root:root
```

注意：

- 如果数据库不在本机，请将 `localhost` 改成真实主机名或 IP
- 如果任务计划程序使用的是其他 Windows 账号，`pgpass.conf` 也必须放在那个账号的 `%APPDATA%\postgresql\` 下

## 二、初始化清单

### 1. 检查数据库是否已存在

- [ ] 在管理库执行 `SELECT datname FROM pg_database WHERE datname = 'analytics_db';`
- [ ] 若不存在，创建 `analytics_db`
- [ ] 若已存在，确认这是不是要复用的库，避免误覆盖

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `5.1 检查 analytics_db 是否已存在`
  - `5.2 创建 analytics_db`

### 2. 创建 schema 和只读角色

- [ ] 创建 `src_rb`
- [ ] 创建 `src_defect`
- [ ] 创建 `ods`
- [ ] 创建 `dim`
- [ ] 创建 `fct`
- [ ] 创建 `mart`
- [ ] 创建 `meta`
- [ ] 创建只读角色 `agent_ro`
- [ ] 完成 `CONNECT` 与 `USAGE` 授权

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `5.3 创建 schema`
  - `5.4 创建只读角色`

### 3. 建立 FDW 外部连接

- [ ] 执行 `CREATE EXTENSION IF NOT EXISTS postgres_fdw;`
- [ ] 创建 `rollerbed_srv`
- [ ] 创建 `defect_srv`
- [ ] 创建 `carbody_srv`
- [ ] 为 `root` 创建三个 `USER MAPPING`
- [ ] 确认外部连接参数与新环境一致，不要直接照抄老环境主机名

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `5.5 创建 FDW 连接`
  - `5.7 创建 carbody FDW 连接与外部表`

### 4. 导入外部表

- [ ] 从 `rollerbed_srv` 导入：
  - `rb_position_data`
  - `process_areas`
  - `carrier_types`
  - `vehicle_body_types`
  - `vehicle_color_codes`
  - `vehicle_platforms`
- [ ] 从 `defect_srv` 导入：
  - `history_station_defect_summary`
- [ ] 从 `carbody_srv` 导入：
  - `carbody_history`
- [ ] 只在外部表尚未导入时执行 `IMPORT FOREIGN SCHEMA`

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `5.6 导入外部表`
  - `5.7 创建 carbody FDW 连接与外部表`

### 5. 初始化本地 ODS / DIM / FCT / MART / META

- [ ] 创建 ODS 表
- [ ] 创建 ODS 主键与索引
- [ ] 创建 `meta.sync_job_log`
- [ ] 创建 `meta.refresh_watermark`
- [ ] 创建 `dim.dim_process_area`
- [ ] 创建 `dim.dim_vehicle_profile`
- [ ] 若迁移的是旧版库，补齐 `dim.dim_vehicle_profile.current_*` 字段
- [ ] 创建 `ods.carbody_history`
- [ ] 创建 `dim.carbody_registry`
- [ ] 若表已存在（老版本升级），执行 ALTER TABLE 补齐 7 个 MDS 字段（`body_type / platform_code / color_code / black_roof_flag / rework_flag / reserved_1 / reserved_2`）
- [ ] 初始化增量水位：`ods.carbody_history.max_id`，新环境设为 `'0'`，老环境设为当前 `MAX("ID")`
- [ ] 创建 `fct` 物化视图（含 `fct_vehicle_defect_enriched` 及 `UNIQUE INDEX`）
- [ ] 创建 `mart` 物化视图
- [ ] 完成 `agent_ro` 的最终 `SELECT` 授权

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `6.1 创建 ODS 表`
  - `6.2 ODS 主键与索引`
  - `6.3 创建 meta 表`
  - `6.4 创建 dim 表`
  - `6.5 创建事实层与分析层物化视图`
  - `6.6 授权`

### 6. 创建正式刷新过程

- [ ] 创建或替换 `meta.refresh_analytics_all()`
- [ ] 确认刷新过程包含以下动作：
  - 全量重载 ODS
  - 重建 `dim.dim_process_area`
  - 重建 `dim.dim_vehicle_profile`
  - 刷新 `fct` 物化视图
  - 刷新 `mart` 物化视图
  - 更新 `meta.refresh_watermark`
  - 记录 `meta.sync_job_log`
- [ ] 创建 `meta.refresh_carbody()`
- [ ] 确认 carbody 刷新为增量模式：
  - ODS 增量 INSERT（基于 `max("ID")` 水位，不 TRUNCATE）
  - DIM 增量 UPSERT（`ON CONFLICT DO UPDATE`，`first_*` 保留、`last_*` 覆盖、`station_pass_count` 累加）
  - MDS_DATA 提取 7 个字段（取末次 `MDS_DATA`）
  - 更新 `meta.refresh_watermark`

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `7. 最新正式版一键刷新过程`
  - `7.2 carbody 刷新过程`

## 三、首次刷新清单

- [ ] 初始化增量水位（若尚未在初始化阶段完成）：
  - 新环境：`INSERT INTO meta.refresh_watermark VALUES ('ods.carbody_history.max_id', '0') ON CONFLICT DO NOTHING;`
  - 老环境：设为当前 `SELECT MAX("ID") FROM ods.carbody_history`
- [ ] 执行 `CALL meta.refresh_analytics_all();`
- [ ] 执行 `CALL meta.refresh_carbody();`（新环境为全量，老环境为增量）
- [ ] 确认两个过程都执行成功，没有异常中断
- [ ] 检查 `meta.sync_job_log` 最新两条状态是否为 `success`
- [ ] 检查 `meta.refresh_watermark` 是否已写入（含 carbody 水位）
- [ ] 检查 `fct` / `mart` 物化视图是否已有数据

最小执行命令：

```sql
CALL meta.refresh_analytics_all();
```

对应正式 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `8. 首次刷新`

## 四、验收清单

### 1. 验证对象是否齐全

- [ ] schema：`src_rb / src_defect / src_carbody / ods / dim / fct / mart / meta`
- [ ] `dim` 表：`dim_process_area / dim_vehicle_profile / carbody_registry`
- [ ] `ods` 表：含 `carbody_history`
- [ ] `fct` 物化视图：
  - `fct_position_current_all`
  - `fct_vehicle_position_current`
  - `fct_abnormal_vehicle_current`
  - `fct_vehicle_defect_detection`
  - `fct_vehicle_defect_enriched`
- [ ] `mart` 物化视图：
  - `mart_vehicle_quality_360`
  - `mart_abnormal_vehicle_current`
  - `mart_position_current_overview`
- [ ] 过程：`meta.refresh_analytics_all() / meta.refresh_carbody()`

### 2. 验证关键数据是否已刷新

- [ ] `ods.rb_position_data` 有数据
- [ ] `ods.history_station_defect_summary` 有数据
- [ ] `dim.dim_process_area` 有数据
- [ ] `dim.dim_vehicle_profile` 有数据
- [ ] `fct.fct_position_current_all` 有数据
- [ ] `fct.fct_vehicle_position_current` 有数据
- [ ] `fct.fct_abnormal_vehicle_current` 有数据
- [ ] `mart.mart_vehicle_quality_360` 有数据
- [ ] `mart.mart_abnormal_vehicle_current` 有数据
- [ ] `mart.mart_position_current_overview` 有数据
- [ ] `ods.carbody_history` 有数据（~101 万行）
- [ ] `dim.carbody_registry` 有数据（~1.3 万行）
- [ ] `fct.fct_vehicle_defect_enriched` 有数据，且 `has_defect_record` 标记准确
- [ ] `dim.carbody_registry.first_seen_at <= last_seen_at`（无不合理的首末时间）
- [ ] `dim.carbody_registry` 全为 78 前缀
- [ ] MDS 7 字段非 NULL 率合理（`body_type / platform_code / color_code` 覆盖率 > 90%）

### 3. 验证权限

- [ ] `agent_ro` 对 `ods / dim / fct / mart / meta` 具有 `USAGE`
- [ ] `agent_ro` 对最终查询对象具有 `SELECT`

建议直接执行正式手册中的验证 SQL：

- [analytics_db_architecture.md](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)
  - `9.1 验证 schema / 表 / 物化视图`
  - `9.2 验证数据量`
  - `9.3 验证刷新日志与水位`
  - `9.4 验证异常车分类结果`
  - `9.5 验证 agent_ro 权限`

## 五、日常刷新清单

### 手工刷新

- [ ] 执行 `CALL meta.refresh_analytics_all();`
- [ ] 执行 `CALL meta.refresh_carbody();`
- [ ] 检查 `meta.sync_job_log`
- [ ] 如有需要，再检查 `meta.refresh_watermark`

### Windows 定时任务

- [ ] 优先使用仓库中的包装脚本：
  - [refresh_analytics_db.ps1](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/scripts/refresh_analytics_db.ps1)
- [ ] 确认目标机器的 `psql` 可直接执行
- [ ] 若不可直接执行，给脚本传入 `-PsqlExe`
- [ ] 优先使用 `pgpass.conf` 提供数据库密码；必要时再传入 `-DbPassword`
- [ ] 确认 `pgpass.conf` 与计划任务实际运行账号一致
- [ ] 首次上线后至少人工观察一次执行结果

参考命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\defect_database\scripts\refresh_analytics_db.ps1"
```

### 建议频率

- [ ] `rb_position_data` 相关分析：每 `5` 分钟
- [ ] 缺陷汇总相关分析：每 `15` 到 `30` 分钟
- [ ] carbody 增量刷新：每 `5` 分钟
- [ ] carbody 每周兜底：重置水位为 `'0'` + TRUNCATE ODS + TRUNCATE DIM + `CALL meta.refresh_carbody()`（清理源库已滚动删除的过期行）

## 六、迁移后应用接入清单

- [ ] 在目标环境 `.env` 中增加 `ANALYTICS_DATABASE_URL`
- [ ] 确认 SQL Agent 默认连接已切换到 `analytics_db`
- [ ] 使用 `agent_ro` 账号做一次只读连接验证

示例：

```env
ANALYTICS_DATABASE_URL='postgresql://agent_ro:你的密码@localhost:5432/analytics_db'
```

## 七、最容易踩坑的点

- [ ] 不要把 `fct.fct_vehicle_position_current` 当成“全部当前占位”入口，它只面向正式产品车
- [ ] `mart.mart_vehicle_quality_360` 关联的是“缺陷检测 + 当前最新位置”，不是“检测当时位置”
- [ ] `IMPORT FOREIGN SCHEMA` 不要重复执行到已存在对象上
- [ ] 新环境迁移时，FDW 的主机、端口、账号密码必须按目标环境重填
- [ ] `agent_ro` 示例密码必须替换
- [ ] carbody 为增量刷新（ODS 只增不删 + DIM UPSERT），首次使用前必须初始化水位，否则会重复全量插入
- [ ] 老环境已有全量数据时，水位应设为当前 `MAX(“ID”)`，跳过全量重刷

## 八、推荐执行顺序摘要

1. 准备源库与账号
2. 创建 `analytics_db`
3. 创建 schema、角色、FDW、外部表（含 `carbody_srv`）
4. 创建本地 ODS / DIM / FCT / MART / META 对象（含 `ods.carbody_history`、`dim.carbody_registry`）
5. 创建 `meta.refresh_analytics_all()` + `meta.refresh_carbody()`（增量版）
6. 初始化增量水位（`ods.carbody_history.max_id`，新环境 `'0'` / 老环境 `MAX("ID")`）
7. 首次执行 `CALL meta.refresh_analytics_all();` + `CALL meta.refresh_carbody();`
8. 跑完整体验证 SQL（含 9.6 carbody 验证 + MDS 字段检查）
9. 配置 `agent_ro` 与应用接入
10. 配置定时刷新（含 carbody 增量 5min + 每周兜底）
