# Data Saver Service (PostgreSQL V2)

本项目是一个基于 Python 的数据保存服务，主要负责订阅并保存来自 WebSocket 的车辆追踪与生产历史数据到 PostgreSQL 数据库。

**更新日期: 2026-08-27**（修正 `defect_database/` 残留条目，补充容器化部署与字典表初始化等新增组件）

## 📁 项目结构 (File Structure)

- `data_saver_service_v3_docker.py`: 核心服务脚本，支持 Docker 环境运行。
- `rb_position_manager_postgresql.py`: 数据库操作封装类。
- `init_rb_positions_postgresql.py`: RB 位置初始化脚本（读取 deviceConfig.json，初始化 98 个位置）。
- `init_seed_data_postgresql.py` + `seed_data.json`: 字典表预填充脚本（process_areas / carrier_types）。
- `create_tables_postgresql.sql`: 核心建表 SQL 脚本。
- `carbody_etl/`: 车辆过站历史 ETL 模块，直连 SQL Server 增量同步并触发 DIM 聚合处理。
- `defect_summary_etl/`: 车辆缺陷汇总 ETL 模块，支持双数据库源（PostgreSQL/SQL Server）与数据保留裁剪。
- `scheduler/`: 自动化定时数据同步与分析数仓刷新调度器服务。
  - `scheduler/scheduler_main.py`: 自动化三链路定时刷新常驻调度器。
- `Dockerfile` + `docker-compose.yml`: 主服务容器化部署与编排。
- `Dockerfile.defect-refresh`: 缺陷汇总刷新专用 Docker 镜像。
- `Dockerfile.scheduler`: 定时同步调度器的 Docker 镜像封装。
- `docs/`: 包含架构设计、数据库元数据中文注释脚本（`03_analytics_db_comments.sql`）、大模型关联防错去重指南（`04_analytics_db_fanout_prevention_guide.md`）、车辆分类规则与 LLM 提示词规范（`06_vehicle_classification_rules_and_llm_prompt.md`）、项目车集成规格书（`project_car/project_vehicle_integration_spec.md`）、配置说明与数据迁移方案。
- `utily/`: 设备配置（deviceConfig）生成与合并工具。
- `backup/`: 历史版本脚本与文档备份。
- `logs/`: 各 ETL 刷新任务运行日志。
- `README_DOCKER.md`: Docker 部署说明。
- `AGENTS.md`: 项目协作与 Agent 行为准则。
- `memory.md`: 项目长期记忆与技术约定。
- `changelog.md`: 项目变更历史记录。

## 🚀 快速开始

请参阅 [README_数据库改造使用说明.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/README_%E6%95%B0%E6%8D%AE%E5%BA%93%E6%94%B9%E9%80%A0%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E.md) 获取详细的部署与配置指南。

## 🛠 开发规范

- 运行环境：`conda activate websoket`
- 遵循 `AGENTS.md` 中的协作规则。
- 所有重大变更需同步更新 `changelog.md` 和 `memory.md`。
