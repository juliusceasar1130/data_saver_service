# Changelog

## 2026-05-17 21:00 Asia/Shanghai

简要概括：全面落地分析数仓三链路（Carbody ODS ETL、缺陷汇总 ETL、分析库聚合过程）的 Docker 容器化定时同步调度器，实现免宿主机计划任务的后台静默、高可靠自动刷新架构。

主要修改内容：

- **实现常驻 Python 定时任务调度器**
  - 在根目录新建了 [scheduler/](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/scheduler) 文件夹并编写 [scheduler_main.py](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/scheduler/scheduler_main.py)：
    - 使用 `schedule` 库并支持从环境读取 `SCHEDULER_INTERVAL_MINUTES` 自定义配置（单位：分钟），实现极高灵活度。
    - 串行依次调度 Carbody ETL 脚本 (`refresh_carbody_ods.py`)、缺陷汇总 ETL 脚本 (`refresh_history_station_defect_summary.py --refresh`)，最后利用 `psycopg2-binary` 执行 `CALL meta.refresh_analytics_all();`，确保数仓内数据逻辑顺序一致。
    - 采用绝对路径与 `cwd` 自定义执行目录设计，确保容器与宿主机中在任意工作目录下运行均万无一失。
    - 添加全局锁 `IS_RUNNING` 机制双重防御防重叠“叠跑”。
    - 使用 `try-except` 闭环隔离单次网络闪断异常，并将每轮运行正常时间点写入健康检查文件 `/tmp/scheduler_health` 以供容器状态监控。
- **配置 Docker 容器化与网络互连**
  - 新增 [Dockerfile.scheduler](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/Dockerfile.scheduler)：基于 `python:3.10-slim` 构建并配置 `Asia/Shanghai` 时区，指令执行路径同步对齐。
  - 修改 [docker-compose.yml](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/docker-compose.yml)：
    - 新增 `refresh-scheduler` 独立服务，与 `postgres` 同属 `app-network` 虚拟网，走内部服务名直连减少时延。
    - 显式声明日志自动轮转选项（`max-size: 10m`，`max-file: 3`）防止容器日志撑爆磁盘。
    - 挂载健康检查参数 `healthcheck`，支持定时探测 `/tmp/scheduler_health` 的变更情况防假死，且自动通过 Shell 算术 `SCHEDULER_INTERVAL_MINUTES + 2` 分钟安全窗口动态适应自定义刷新时间。
    - 针对容器内的特殊运行环境进行环境变量精准覆写：`DB_HOST/CARBODY_TARGET_DB_HOST/DEFECT_TARGET_DB_HOST` 覆盖为 `postgres`；`CARBODY_SOURCE_DB_HOST/DEFECT_SOURCE_DB_HOST` 重定向至 WSL 的 `host.docker.internal`，并绑定代理端口 `14330/14331`，使得容器调度与宿主机本地调试配置完美兼容互不干扰。
- **项目基础设施及环境配置**
  - 重新规划调度器存放目录：将调度器文件独立收纳至根目录 `scheduler/` 文件夹，极其显眼易寻。
  - 修改 [requirements.txt](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/requirements.txt)：追加 `schedule==1.2.2` 依赖。
  - 修改 [.env](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/.env) 和 [.env.example](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/.env.example)：增加 `SCHEDULER_INTERVAL_MINUTES` 自定义调度时间段参数。
  - 修改 [README.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/README.md)：在项目文件结构中加入调度器文件夹与其下的常驻脚本及 Docker 镜像的最新描述。

## 2026-05-17 18:50 Asia/Shanghai

简要概括：新增双链路定时刷新技术方案设计，评估多种调度方案优劣并推荐基于 Docker Compose 容器化的 Python 调度器方案，实现分析数仓（`analytics_db`）2~5 分钟高频自动刷新的“一键式编排”与极致静默稳定运行。

主要修改内容：

- **新增分析数仓双链路定时刷新技术方案**
  - 新建了 [analytics_db_refresh_deployment_plan.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/docs/plan/analytics_db_refresh_deployment_plan.md)：
    - 分析了常规分析链路（`CALL meta.refresh_analytics_all();`）和 Carbody 链路（`refresh_carbody_ods.py`）的同步调度需求。
    - 对比了 Windows 任务计划程序、WSL 2 Cron 和 Docker 容器化统一调度方案，明确了 Docker 容器化方案的绝对优势。
    - 设计了基于 Docker Compose + Python `schedule` 守护进程的统一调度器架构，制定了具体的修改、容器化部署及双链路验证步骤。

## 2026-05-17 14:15 Asia/Shanghai

简要概括：彻底清理和纠正数仓架构手册及新环境迁移清单中遗留的旧版 FDW 及 `refresh_carbody` 废弃方法，消除多期/历史版本口径冲突，确保数仓文档与 Phase 2 的 Python ETL 新架构 100% 精准对齐。

主要修改内容：

- **重构架构设计手册中 Carbody 链路描述**
  - 修改了 [analytics_db_architecture.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)：
    - 在 6.9 节正式补齐了增量维表聚合存储过程 `meta.refresh_carbody_dim()` 的 PL/pgSQL DDL 完整定义。
    - 将 7.2 节重写为 `Carbody 刷新过程的重构与废弃说明`，详细阐述了取消 `postgres_fdw` 挂载后的“库内/外解耦”架构演进，明确声明 `meta.refresh_carbody()` 过程彻底废弃。
    - 在 8 节（首次刷新）中，移除了旧的库内 `CALL meta.refresh_carbody();` 命令，替换为首选的水位初始化与运行 Python 直连抽取脚本 `python carbody_etl/refresh_carbody_ods.py` 指引。
    - 将 2.2 节历史对象快照中的 `src_carbody` 和 `refresh_carbody()` 修正为遗留/废弃标注。
- **全面重构新环境迁移清单以对齐 Phase 2 架构**
  - 彻底覆写了 [analytics_db_migration_checklist.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_migration_checklist.md)：
    - **移除旧版多期残留**：删除了所有关于创建 `carbody_srv` FDW 连接、外部表导入以及在 PG 中调用旧 `refresh_carbody()` 存储过程的清单项。
    - **对齐 Python 架构**：增设 Python 运行环境验证（如 `conda activate websoket` 激活验证）、独立 `.env` 配置文件配置项、本地 `ods.carbody_history` 显式创建等清单要求。
    - **重构同步与验收顺序**：将首次刷新流程调整为运行外部 Python ETL 脚本触发增量维表聚合的规范顺序；增设富集事实宽表 `fct.fct_vehicle_defect_enriched` 的数据完整性和 `agent_ro` USAGE 权限验收清单。

## 2026-05-17 11:25 Asia/Shanghai

简要概括：优化 `defect_summary_etl` 表结构时间类型，由 `TIMESTAMP` 变更为时区安全的 `TIMESTAMPTZ` 格式；同时补全并完善数仓架构手册中的物化视图删除依赖逻辑。

主要修改内容：

- **优化 `defect_summary_etl` 模块中的时间数据类型**
  - 修改了 [history_station_defect_summary.sql](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/history_station_defect_summary.sql)：将 `history_station_defect_summary.date_time` 和 `history_station_defect_summary_refresh_state.last_success_date_time` 字段类型由 `TIMESTAMP` 升级为 `TIMESTAMPTZ`。
  - 修改了 [refresh_history_station_defect_summary.py](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/refresh_history_station_defect_summary.py)：同步更新了脚本中内置的 `TARGET_SCHEMA_SQL` 自动建表声明。
  - **优化价值**：实现了整个分析数仓（`analytics_db`）时间维度的 100% 带时区一致性，彻底根治跨表比较时隐式类型转换引起的索引性能下降以及 LLM 时间戳时区（如 8 小时错位）差错。
- **完善数仓架构手册依赖关系**
  - 修改了 [analytics_db_architecture.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_database/database_refactor/analytics_db_architecture.md)：在“物化视图升级删除旧视图”脚本中，补齐了遗漏的 `fct.fct_vehicle_defect_enriched` 与 `fct.fct_vehicle_defect_detection`，并按照拓扑依赖顺序（Mart 层 ➡️ Fact 富集层 ➡️ Fact 基础检测层）重新编排了 `DROP` 语句，彻底避免重建时的依赖报错冲突。

## 2026-05-17 Asia/Shanghai

简要概括：重构重组 ETL 模块目录，并实施 carbody 源库 PostgreSQL → SQL Server 迁移方案与字段/时间类型容错对齐。

主要修改内容：

- **重构并新增 `carbody_etl` 模块**
  - 新增 `carbody_etl/refresh_carbody_ods.py` 增量同步脚本，直连 SQL Server 源库提取数据写入 PostgreSQL `ods.carbody_history`，并调用存储过程触发 DIM/FCT 刷新。
  - 新增 `carbody_etl/README.md` 架构与部署文档。
  - 迁移原 `carbody_history/` 下的 `schema.md` 与 `MDS数据提取规则.md` 进 `carbody_etl/carbody_history/`。
- **重构并新增 `defect_summary_etl` 模块**
  - 迁移并整合 `refresh_history_station_defect_summary.py` 脚本、`model_map.json` 及所有 SQL 和 Schema 文档到 `defect_summary_etl/` 目录下。
  - 新建 `defect_summary_etl/README.md` 与缺陷协议历史文档归档 `defect_summary_etl/DOCS_ARCHIVE.md`。
- **升级设计与迁移规划文档**
  - 新建 `docs/plan/carbody_history_sqlserver_migration.md`，提供完整的 carbody_history 源库 PostgreSQL → SQL Server 架构转换与回退策略设计。
  - 重构 `defect_database/database_refactor/analytics_db_architecture.md`：
    - 废弃原 PostgreSQL FDW 连接方式，切换为直连 SQL Server 的 Python 管道。
    - 显式定义 `ods.carbody_history` 结构，将 `SKID_ID` 与 `CYCLE_NUM` 容错修正为 `VARCHAR(64)` 兼容非数字 skid/cycle 现场数据。
    - 统一时区处理，将 `dim.dim_vehicle_profile.defect_last_seen_at` 和 `dim.carbody_registry` 中的 `first_seen_at/last_seen_at` 统一修正为 `TIMESTAMPTZ`。
- **基础配置适配**
  - 修改 `.mcp.json`，切换 postgres 服务到本地 `analytics_db` 库，并追加 `mssql` (SQL Server) 调试服务配置。
  - 新增项目级 `.env.example`，提供完整的 ETL 调试连接占位配置。

## 2026-05-11 Asia/Shanghai

简要概括：`dim.carbody_registry` 从全量刷新重构为增量 UPSERT，新增 MDS_DATA 7 字段提取。

主要修改内容：

- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 6.8 DDL：`dim.carbody_registry` 新增 7 个 MDS 字段（`body_type / platform_code / color_code / black_roof_flag / rework_flag / reserved_1 / reserved_2`）+ ALTER TABLE 升级语句
  - 7.2 存储过程：从 TRUNCATE + INSERT 全量刷新重写为增量 UPSERT（水位 `max("ID")`、ODS 纯增量、DIM `ON CONFLICT DO UPDATE`）
  - 新增 UPSERT 语义表（`first_*` 保留、`last_*` 覆盖、`station_pass_count` 累加）
  - 新增每周兜底流程（重置水位 + TRUNCATE ODS/DIM + 全量重建）
  - 8 首次刷新：新增水位初始化步骤（新/老环境区分）
  - 9.6 验证 SQL：新增水位检查、MDS 字段非 NULL 率、增量幂等性验证
  - 10.3 频率：carbody 从 15-30min → 5min 增量 + 每周全量兜底
- 更新 `defect_database/database_refactor/analytics_db_migration_checklist.md`
  - 初始化清单新增 ALTER TABLE 补齐 MDS 字段、水位初始化检查项
  - 刷新过程清单更新为增量模式描述
  - 首次刷新新增水位初始化前置步骤
  - 验收清单新增 MDS 字段覆盖率检查
  - 日常刷新新增 5min 增量频率 + 每周兜底流程
  - 踩坑点从"全量刷新"更新为"增量刷新"注意事项
  - 执行顺序摘要新增水位初始化步骤
- 新增 `carbody_history/MDS数据提取规则.md`
  - MDS_DATA 固定位置提取规则（1-indexed）：vehicle_id、body_type、platform_code、color_code、black_roof_flag、rework_flag、reserved_1、reserved_2

## 2026-05-10 15:35 Asia/Shanghai

简要概括：接入 `carbody_history` 数据库到 `analytics_db`（阶段一：ODS + DIM 落地）。

主要修改内容：

- 新增 `carbody_history/schema.md`
  - 通过 PostgreSQL MCP 连接数据库获取了 `carbody_history` 表的完整 Schema
  - 整理了字段名、数据类型、约束以及初步说明
- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 新增 `src_carbody` schema、`carbody_srv` FDW server 与 user mapping（5.7）
  - 新增 `ods.carbody_history` 表结构、PK 与索引（6.7）
  - 新增 `dim.carbody_registry` 维度表（78 前缀过滤，首/末过站聚合）（6.8）
  - 新增 `meta.refresh_carbody()` 独立存储过程（7.2）
  - 新增 9.6 carbody 验证 SQL 与 10.3 建议频率
  - 更新对象列表、目录、刷新命令
- 更新 `defect_database/database_refactor/analytics_db_migration_checklist.md`
  - 新增 carbody 相关的迁移前准备、初始化、验收、日常刷新清单项

## 2026-04-16 Asia/Shanghai

简要概括：补充 Docker PostgreSQL 与 Windows PostgreSQL 端口冲突排故记录。

主要修改内容：

- 新增 `docs/docker_postgres_windows_port_conflict_troubleshooting.md`
  - 总结 `120JPH_postgres` 与 Windows PostgreSQL 17 并存时的连接混淆原因
  - 记录 `localhost:5432` 实际连接目标、角色验证结果与数据库验证结果
  - 整理后续推荐方案，包括“Docker 改端口”与“停用 Windows PostgreSQL 服务”两种处理路径

## 2026-04-14 19:56 Asia/Shanghai

简要概括：将脚本目录迁移到 `defect_database/scripts` 并统一更新引用路径。

主要修改内容：

- 移动脚本目录
  - 将根目录 `scripts` 迁移为 `defect_database/scripts`
- 更新 `defect_database/scripts/refresh_history_station_defect_summary.ps1`
  - 调整 `ProjectRoot` 解析逻辑，兼容新目录层级
- 更新 `defect_database/scripts/refresh_history_station_defect_summary_docker.ps1`
  - 调整 `ProjectRoot` 解析逻辑，兼容新目录层级
- 更新 `README_DOCKER.md`
  - 将宿主机与 Docker 计划任务命令路径切换到 `defect_database/scripts/...`
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 将部署命令与说明中的脚本路径切换到 `defect_database/scripts/...`

## 2026-04-14 19:47 Asia/Shanghai

简要概括：将宿主机计划任务部署命令补充到缺陷汇总 README。

主要修改内容：

- 更新 `defect_database/defect_database_from_agent/README.md`
  - 补充当前环境下可直接复制的 `--init-state`、`--refresh`、`--print-status` 部署命令
  - 明确 `websoket` 环境的 `python.exe` 实际路径
  - 更新任务计划程序中的 `Add arguments` 推荐写法

## 2026-04-14 15:33 Asia/Shanghai

简要概括：补齐宿主机计划任务执行缺陷汇总刷新脚本的落地文件，并调整文档推荐顺序。

主要修改内容：

- 新增 `defect_database/scripts/refresh_history_station_defect_summary.ps1`
  - 提供宿主机执行 `refresh_history_station_defect_summary.py` 的 PowerShell 包装脚本
  - 支持 `-Mode`、`-PythonExe`、`-CondaEnv`
  - 仅在当前激活环境确实为目标 Conda 环境时才直接复用，否则优先尝试 `conda run -n websoket`
  - 通过 `CONDA_NO_PLUGINS=true` 与 `conda --no-plugins run` 降低计划任务中的 Conda 插件干扰风险
  - 兼容企业内网源库场景下的 Windows 任务计划程序调用
- 更新 `README_DOCKER.md`
  - 新增“企业内网源库优先宿主机”推荐方案
  - 将 Docker Desktop 定时刷新调整为备选方案说明
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 补充宿主机包装脚本已落地的信息
  - 明确企业内网源库场景优先宿主机执行

## 2026-04-14 13:57 Asia/Shanghai

简要概括：补充 defect-refresh 容器环境变量传递关系说明文档。

主要修改内容：

- 新增 `docs/defect_refresh_docker_env_flow.md`
  - 说明 `.env`、`docker-compose.yml`、容器环境与 `refresh_history_station_defect_summary.py` 之间的变量流转
  - 明确 `DEFECT_SOURCE_DB_HOST` 在容器中默认来自 `.env`
  - 明确 `DEFECT_TARGET_DB_HOST_IN_DOCKER` / `DEFECT_TARGET_DB_PORT_IN_DOCKER` 仅用于 compose 覆盖 target 变量

## 2026-04-13 18:05 Asia/Shanghai

简要概括：落地 Docker Desktop 下最稳的缺陷汇总定时刷新方案。

主要修改内容：

- 新增 `Dockerfile.defect-refresh`
  - 为 `defect_database/refresh_history_station_defect_summary.py` 提供独立镜像
  - 通过 `ENTRYPOINT` 直接承载 `--init-state / --refresh / --print-status`
- 更新 `docker-compose.yml`
  - 新增 `defect-refresh` 服务
  - 为容器内运行场景补充 `DEFECT_TARGET_DB_HOST_IN_DOCKER` 覆盖逻辑
- 新增 `defect_database/scripts/refresh_history_station_defect_summary_docker.ps1`
  - 供 Windows 任务计划程序稳定触发 `docker compose --profile manual run --rm defect-refresh`
- 更新 `.env_example`
  - 补充 Docker Desktop 下的目标库主机覆盖参数模板
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 新增 Docker Desktop 最稳方案、执行步骤与前置条件说明
- 更新 `README_DOCKER.md`
  - 补充缺陷汇总定时刷新的 Docker Desktop 部署与调度说明

## 2026-04-13 17:10 Asia/Shanghai

简要概括：补充缺陷汇总增量刷新任务的定期调度落地方案与运维最佳实践。

主要修改内容：

- 更新 `defect_database/defect_database_from_agent/README.md`
  - 新增“定期刷新最佳实践”章节
  - 补充 Windows 任务计划程序的推荐配置方式与包装脚本示例
  - 补充 Linux / Docker 的 `cron` 调度示例
  - 补充刷新频率选择、批次参数调优、监控巡检与上线顺序建议

## 2026-04-13 11:20 Asia/Shanghai

简要概括：为 `defect_db.history_station_defect_summary` 新增本地落库、源库可切换的增量刷新能力。

主要修改内容：

- 新增 `defect_database/refresh_history_station_defect_summary.py`
  - 支持 `--init-state`、`--refresh`、`--print-status`
  - 支持本地 target + 可切换 source 的双连接模式
  - 支持 `history_id` 水位推进、replay window 回放、`UPSERT` 写回、advisory lock 并发控制
- 重构 `defect_database/defect_database_from_agent/history_station_defect_summary.sql`
  - 从全量 `DROP/TRUNCATE` 刷新脚本调整为幂等初始化 SQL
  - 新增刷新状态表、刷新日志表、目标侧索引
  - 保留并同步 `model_attribute_map` 本地映射
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 说明初始化方式、增量刷新方式、源库切换方式和外部调度建议
- 更新 `.env_example`
  - 新增 `DEFECT_TARGET_DB_*`、`DEFECT_SOURCE_DB_*` 与增量刷新相关环境变量模板

## 2026-04-13 11:45 Asia/Shanghai

简要概括：补充缺陷汇总增量刷新机制的详细文档说明。

主要修改内容：

- 更新 `defect_database/defect_database_from_agent/README.md`
  - 新增“刷新原理”章节，详细说明双连接、初始化水位、增量候选集、replay window、UPSERT、水位推进、锁控制与状态/日志表职责
  - 新增“配置参数说明”章节，逐项解释 `DEFECT_TARGET_DB_*`、`DEFECT_SOURCE_DB_*` 和刷新行为参数
  - 新增调优建议与常见排查点，便于后续运维

## 2026-04-13 12:20 Asia/Shanghai

简要概括：将缺陷汇总增量刷新脚本扩展为“PostgreSQL 目标库 + PostgreSQL/SQL Server 源库”兼容方案。

主要修改内容：

- 重构 `defect_database/refresh_history_station_defect_summary.py`
  - 新增 `DEFECT_SOURCE_DB_TYPE`、`DEFECT_SOURCE_DB_SCHEMA`、`DEFECT_SOURCE_DB_DRIVER` 等配置支持
  - 目标库继续固定 PostgreSQL，源库支持 PostgreSQL / SQL Server 双方言
  - SQL Server 源库改用 `pyodbc` 连接，并使用 SQL Server 方言查询 `history` / `history_detail`
  - 移除“源库参数不完整时静默回退本地”的行为，改为直接报配置错误
- 更新 `.env_example`
  - 新增 SQL Server 源库所需配置模板
- 更新 `requirements_standard.txt`
  - 新增 `pyodbc`
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 补充 SQL Server 源库配置说明、驱动要求与排查要点

## 2026-04-13 15:40 Asia/Shanghai

简要概括：补充 SQL Server 源库空密码兼容说明。

主要修改内容：

- 更新 `defect_database/refresh_history_station_defect_summary.py`
  - 允许 `DEFECT_SOURCE_DB_PASSWORD` 以空字符串形式参与 SQL Server 源库连接
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 明确空密码时应写成 `DEFECT_SOURCE_DB_PASSWORD=`，不要写占位符或引号包裹的伪值

## 2026-04-13 15:55 Asia/Shanghai

简要概括：将 SQL Server 源库连接从 `pyodbc` 切换为 `python-tds`，移除对 Windows ODBC Driver 的依赖。

主要修改内容：

- 更新 `defect_database/refresh_history_station_defect_summary.py`
  - SQL Server 源库改为 `python-tds`
  - 移除 ODBC Driver / Encrypt / TrustServerCertificate 配置依赖
  - SQL Server 查询改为不依赖驱动参数占位符的整数直拼方式
- 更新 `.env_example`
  - 移除 SQL Server 的 ODBC 专属配置项
  - 明确当前脚本不需要额外安装 Windows ODBC Driver
- 更新 `requirements.txt`
  - 用 `python-tds` 替换 `pyodbc`
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 将 SQL Server 驱动说明调整为 `python-tds`

## 2026-04-13 16:20 Asia/Shanghai

简要概括：优化缺陷汇总增量刷新日志的可读性。

主要修改内容：

- 更新 `defect_database/refresh_history_station_defect_summary.py`
  - 默认压低 `python-tds` 底层调试日志，仅保留业务刷新日志
  - 为每个批次新增 `batch_type`，区分 `new_and_replay` 与 `replay_only`
  - 在一次 `--refresh` 结束时新增总汇总日志，输出总批次数、总新增量、总回放量、总写入量和最终水位
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 补充批次日志类型说明与“两批日志”的常见原因

## 2026-04-13 11:52 Asia/Shanghai

简要概括：补充 `--init-state` 命令用途说明。

主要修改内容：

- 更新 `defect_database/defect_database_from_agent/README.md`
  - 在“初始化状态”小节中补充 `--init-state` 的职责说明
  - 明确区分 `--init-state`、`--refresh`、`--print-status` 三个命令的作用
  - 补充 `from_summary` 与 `from_zero` 对首个水位的影响
## 2026-04-14 20:25 Asia/Shanghai

简要概括：核对 `analytics_db` 文档与实际数据库对象，并修正 `database_refactor` 文档中的旧仓库绝对路径。

主要修改内容：

- 核对 `analytics_db` 实际实现状态
  - 对照数据库中的 `src_rb / src_defect / ods / dim / fct / mart / meta` schema、表、物化视图、刷新过程与样例数据量
  - 确认 `defect_database/database_refactor` 目录下的核心落地文档与当前数据库实现基本一致
- 更新文档引用路径
  - 修正 `defect_database/database_refactor/analytics_db_architecture.md`
  - 修正 `defect_database/database_refactor/why_analytics_db.md`
  - 修正 `defect_database/database_refactor/unimplemented_phases_todolist.md`
  - 将旧仓库 `rearch_agent` 的绝对路径更新为当前仓库 `savedatabase-postgresql_v2` 下的实际文件路径

## 2026-04-14 21:17 Asia/Shanghai

简要概括：将 `analytics_db_architecture.md` 收敛为唯一最终落地文档，并按实时 `analytics_db` 校验结果补齐口径说明。

主要修改内容：

- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 明确该文档为 `analytics_db` 最终落地口径
  - 补充基于 MCP 实时校验得到的对象、字段、数据量、异常分类与水位结果
  - 合并 `current_vehicle_fact_refactor.md` 中仍需保留的设计解释、边界说明与查询入口建议
- 更新 `defect_database/database_refactor/current_vehicle_fact_refactor.md`
  - 明确该文档降级为历史设计记录
  - 指向 `analytics_db_architecture.md` 作为唯一执行与落地基线

## 2026-04-14 21:28 Asia/Shanghai

简要概括：删除 `analytics_db` 最终文档中已过时的下一阶段优化建议章节。

主要修改内容：

- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 删除 `10.4 下一阶段优化建议` 章节
  - 避免该章节与当前已落地状态重复，减少“已实现内容仍被描述为下一阶段”的歧义

## 2026-04-14 21:29 Asia/Shanghai

简要概括：为 `analytics_db` 最终文档补充章节目录。

主要修改内容：

- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 在文档开头新增目录
  - 为长文档提供章节跳转入口，便于定位初始化、刷新、验证与接入部分

## 2026-04-14 21:33 Asia/Shanghai

简要概括：新增 `analytics_db` 新环境迁移专用初始化与刷新清单。

主要修改内容：

- 新增 `defect_database/database_refactor/analytics_db_migration_checklist.md`
  - 提炼新环境迁移时的初始化顺序、首次刷新、验收、日常刷新与应用接入清单
  - 引用最终落地手册中的正式 SQL，避免在迁移清单中重复维护大段对象定义

## 2026-04-14 22:12 Asia/Shanghai

简要概括：新增 `analytics_db` Windows 宿主机定时刷新包装脚本，并同步更新迁移文档。

主要修改内容：

- 新增 `defect_database/scripts/refresh_analytics_db.ps1`
  - 封装 `psql` 调用 `CALL meta.refresh_analytics_all();`
  - 默认写入 `logs/analytics_db_refresh.log`
  - 支持 `-PsqlExe / -DbHost / -DbPort / -DbName / -DbUser / -DbPassword / -ProcedureName`
- 更新 `defect_database/database_refactor/analytics_db_migration_checklist.md`
  - 将 Windows 定时任务推荐入口切换为 `refresh_analytics_db.ps1`
  - 补充 `pgpass.conf` 与 `-PsqlExe` 的使用提示
- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 在 `10.2 Windows 定时任务` 中补充包装脚本的推荐命令与参数示例

## 2026-04-15 09:53 Asia/Shanghai

简要概括：补充 `analytics_db` Windows 定时任务下的 `pgpass.conf` 密码认证说明。

主要修改内容：

- 更新 `defect_database/database_refactor/analytics_db_architecture.md`
  - 在 `10.2 Windows 定时任务` 中补充 `pgpass.conf` 的路径、格式、示例与任务运行账号注意事项
- 更新 `defect_database/database_refactor/analytics_db_migration_checklist.md`
  - 在迁移前准备和 Windows 定时任务清单中补充 `pgpass.conf` 的配置要求

## 2026-04-15 15:10 Asia/Shanghai

简要概括：新增 `history_station_defect_summary` 固定窗口表参数化保留方案。

主要修改内容：

- 新增 `defect_database/defect_database_from_agent/history_station_defect_summary_retention_window_plan.md`
  - 制定将 `history_station_defect_summary` 收敛为最近 `N` 条或最近 `N` 个月窗口表的参数化方案
  - 说明与现有 watermark、replay window、UPSERT、状态表和下游 `analytics_db` 的兼容关系
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 在文件列表与整体设计部分补充固定窗口表方案文档入口

## 2026-04-15 15:24 Asia/Shanghai

简要概括：为 `history_station_defect_summary` 增量刷新脚本落地固定窗口裁剪能力，并输出是否裁剪日志。

主要修改内容：

- 更新 `defect_database/refresh_history_station_defect_summary.py`
  - 新增 retention 参数：`DEFECT_SUMMARY_RETENTION_MODE / MAX_ROWS / MAX_MONTHS / DELETE_BATCH_SIZE`
  - 在整轮 `--refresh` 成功后执行窗口裁剪
  - 输出 `retention_applied / retention_noop` 日志
  - 在 `--print-status` 中补充 retention 配置与汇总表最小/最大范围
- 更新 `.env_example`
  - 补充 retention 相关环境变量模板
- 更新 `defect_database/defect_database_from_agent/README.md`
  - 补充 retention 参数说明、使用建议与状态输出说明
