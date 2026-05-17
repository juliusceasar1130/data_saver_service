# carbody_history 表结构 (Schema)

修改时间：2026-05-10 15:35 Asia/Shanghai

主要修改内容：
- 初始化 `carbody_history` 表结构文档
- 记录了从 PostgreSQL 数据库中提取的字段定义、数据类型及约束

## 表结构详单

| 列名 (Column Name) | 数据类型 (Data Type) | 允许为空 (Nullable) | 最大长度 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **ID** | numeric | YES | - | 唯一标识 ID |
| **DATE_EVT** | timestamp | **NO** | - | 事件时间 |
| **SHIFT_NR** | numeric | YES | - | 班次编号 |
| **RW_STATION_ID** | varchar | YES | 64 | 读写站 ID |
| **RW_STATION_STATUS** | numeric | YES | - | 读写站状态 |
| **SKID_ID** | varchar | YES | 6 | 滑撬 ID |
| **SKID_TYPE** | varchar | YES | 4 | 滑撬类型 |
| **SKID_IS_EMPTY** | numeric | YES | - | 滑撬是否为空 |
| **BODY_ID** | varchar | YES | 18 | 车身 ID |
| **BODY_TYPE** | varchar | YES | 12 | 车身类型 |
| **MDS_DATA** | varchar | **NO** | - | MDS 数据内容 |
| **MDS_TELEGRAM_TYPE** | varchar | YES | 2 | MDS 电报类型 |
| **FK_ERP_HIST_ID** | numeric | YES | - | ERP 历史关联 ID |
| **CYCLE_NUM** | varchar | YES | 3 | 循环周期数 |
| **PRODUCTION_SEGMENT_ID** | numeric | YES | - | 生产线段 ID |
| **ETL_MODIFY_DATE** | timestamp | **NO** | - | ETL 修改时间 |
| **ETL_SOURCE_ID** | numeric | YES | - | ETL 数据源 ID |
