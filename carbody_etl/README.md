# Carbody 数据同步与处理模块 (Carbody ETL)

本目录包含了将 Carbody 过站历史数据从 SQL Server 源库同步到 PostgreSQL 并在内部进行聚合处理的全套逻辑。

## 1. 核心组件
- `refresh_carbody_ods.py`: 主同步脚本，负责 ODS 搬运及触发后链路（DIM/FCT）刷新。
- `meta.refresh_carbody_dim`: (数据库内存储过程) 负责将 ODS 数据聚合为按车汇总的维度表。

## 2. 环境配置
脚本依赖项目根目录下的 `.env` 文件。请确保包含以下隔离变量：
- `CARBODY_SOURCE_DB_*`: SQL Server 源库连接信息。
- `CARBODY_TARGET_DB_*`: PostgreSQL 目标库连接信息。
- `CARBODY_SOURCE_TABLE_NAME`: 默认为 `MDS_HISTORIC`。

## 3. 使用说明

### 首次使用 (或重置全量)
如果需要清空现有数据并重新从头同步（耗时较长）：
```powershell
python carbody_etl/refresh_carbody_ods.py --full-refresh
```
**注意**：这会清空 PostgreSQL 中的 `ods.carbody_history` 表，并重置水位线。

### 日常增量使用 (定时任务)
平时仅需同步最新产生的数据：
```powershell
python carbody_etl/refresh_carbody_ods.py
```
**建议**：建议在 Windows 任务计划程序中配置每 10-30 分钟运行一次。

## 4. 数据链路流程
脚本运行后会触发以下闭环：
1. **ODS 层**：从 SQL Server 拉取新 ID，写入 `ods.carbody_history`。
2. **DIM 层**：调用存储过程，对新增行进行聚合，更新 `dim.carbody_registry`（一车一行）。
3. **FCT 层**：刷新物化视图 `fct.fct_vehicle_defect_enriched`，产出最终分析看板数据。

## 5. 注意事项
- **时区安全**：脚本强制使用 `Asia/Shanghai` 会话，确保 `DATE_EVT` (timestamptz) 字段不发生 8 小时偏移。
- **并发锁**：脚本内置了 PostgreSQL Advisory Lock，防止多个进程同时同步同一张表导致的水位冲突。
- **数据对齐**：源表的 `SKID` 和 `CYCLE` 字段包含非数字字符，ODS 表中已对应设为 `VARCHAR`。
- **监控**：运行结果可在数据库表 `meta.sync_job_log` 中通过 `job_name = 'refresh_carbody_ods'` 查询。

---
*修改时间：2026-05-16*
