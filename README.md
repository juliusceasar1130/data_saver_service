# Data Saver Service (PostgreSQL V2)

本项目是一个基于 Python 的数据保存服务，主要负责订阅并保存来自 WebSocket 的车辆追踪与生产历史数据到 PostgreSQL 数据库。

## 📁 项目结构 (File Structure)

- `data_saver_service_v3_docker.py`: 核心服务脚本，支持 Docker 环境运行。
- `rb_position_manager_postgresql.py`: 数据库操作封装类。
- `carbody_etl/`: 车辆过站历史 ETL 模块，直连 SQL Server 增量同步并触发 DIM 聚合处理。
- `defect_summary_etl/`: 车辆缺陷汇总 ETL 模块，支持双数据库源（PostgreSQL/SQL Server）与数据保留裁剪。
- `defect_database/`: 缺陷数据库重构的相关设计文档与主刷新过程。
- `docs/`: 包含排污记录、环境配置说明与 carbody 数据源迁移详细方案。
- `init_rb_positions_postgresql.py`: 数据库初始化脚本。
- `create_tables_postgresql.sql`: 核心建表 SQL 脚本。
- `AGENTS.md`: 项目协作与 Agent 行为准则。
- `memory.md`: 项目长期记忆与技术约定。
- `changelog.md`: 项目变更历史记录。

## 🚀 快速开始

请参阅 [README_数据库改造使用说明.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/README_%E6%95%B0%E6%8D%AE%E5%BA%93%E6%94%B9%E9%80%A0%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E.md) 获取详细的部署与配置指南。

## 🛠 开发规范

- 运行环境：`conda activate websoket`
- 遵循 `AGENTS.md` 中的协作规则。
- 所有重大变更需同步更新 `changelog.md` 和 `memory.md`。
