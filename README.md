# Data Saver Service (PostgreSQL V2)

本项目是一个基于 Python 的数据保存服务，主要负责订阅并保存来自 WebSocket 的车辆追踪与生产历史数据到 PostgreSQL 数据库。

## 📁 项目结构 (File Structure)

- `data_saver_service_v3_docker.py`: 核心服务脚本，支持 Docker 环境运行。
- `rb_position_manager_postgresql.py`: 数据库操作封装类。
- `carbody_history/`: 包含生产历史相关的架构说明。
  - `schema.md`: `carbody_history` 表的详细结构定义。
- `defect_database/`: 缺陷数据库相关的脚本与重构文档。
- `docs/`: 包含排故记录与环境配置说明。
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
