# 缺陷汇总同步模块 (Defect Summary ETL)

本模块负责从源数据库（PostgreSQL 或 SQL Server）同步车辆缺陷汇总数据 (`history_station_defect_summary`) 到本地数据库。

## 1. 核心组件
- `refresh_history_station_defect_summary.py`: 主同步脚本。
- `model_map.json`: 车型与属性（车型名称、黑顶标记）的映射配置文件。
- `DOCS_ARCHIVE.md`: 详细的协议设计与历史文档备份。

## 2. 环境配置
依赖项目根目录下的 `.env` 文件。关键变量：
- `DEFECT_SOURCE_DB_*`: 源库连接信息（支持 `sqlserver` 或 `postgres`）。
- `DEFECT_TARGET_DB_*`: 目标库连接信息（PostgreSQL）。
- `DEFECT_SUMMARY_RETENTION_MODE`: 数据保留策略（如 `max_months` 或 `max_rows`）。

## 3. 使用说明

### 首次初始化
如果您是第一次在当前数据库运行：
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py --bootstrap-mode from_zero
```

### 日常增量同步
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py
```

### 查看当前状态
不执行同步，仅查看数据库中的水位和窗口状态：
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py --print-status
```

## 4. 特色功能
- **双数据库支持**：可根据环境变量切换 SQL Server 或 PostgreSQL 作为源头。
- **自动裁剪 (Retention)**：支持按行数或按月数自动清理旧数据，防止 ODS 层无限膨胀。
- **车型映射**：自动读取 `model_map.json` 并同步到目标库的 `model_attribute_map` 表，实现 ID 到名称的自动转换。

## 5. 注意事项
- **车型更新**：如果现场新增了车型，请更新 `model_map.json` 后再次运行脚本。
- **锁机制**：同一时间只允许一个实例运行（基于 PostgreSQL Advisory Lock）。
- **日志**：运行日志记录在 `history_station_defect_summary_refresh_log` 表中。

---
*修改时间：2026-05-16*
