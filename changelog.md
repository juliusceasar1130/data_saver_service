# Changelog

## 2026-05-10 15:35 Asia/Shanghai

简要概括：整理并保存 `carbody_history` 表结构文档。

主要修改内容：

- 新增 `carbody_history/schema.md`
  - 通过 PostgreSQL MCP 连接数据库获取了 `carbody_history` 表的完整 Schema
  - 整理了字段名、数据类型、约束以及初步说明

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
