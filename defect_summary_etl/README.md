# 缺陷汇总同步模块 (Defect Summary ETL)

本模块负责从源数据库（PostgreSQL 或 SQL Server 双方言支持）增量同步车辆缺陷汇总数据并生成 `history_station_defect_summary` 宽表保存到本地数据库，为 LLM（大模型）分析与基础报表提供时区安全且高性能的数据集。

---

## 1. 📂 核心组件与文件目录

*   **[refresh_history_station_defect_summary.py](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/refresh_history_station_defect_summary.py)**：主同步执行脚本（包含双语方言解析、增量 UPSERT 算法、Advisory Lock 并发锁保护以及数据自动剪裁）。
*   **[model_map.json](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/model_map.json)**：车型编号到名称、黑车顶等外部属性的静态配置映射表。
*   **[history_station_defect_summary.sql](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/history_station_defect_summary.sql)**：本地 PostgreSQL 目标数据库建表 SQL（包含时区锁、明细汇总表、状态表与审计日志表声明，提供高质量的字段与表中文注释，是实现 LLM/大模型智能分析的语义基线）。
*   **[DOCS_ARCHIVE.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/DOCS_ARCHIVE.md)**：历史设计协议与设计背景文档归档。

---

## 2. ⚙️ 环境配置说明

本模块高度依赖项目根目录下的 `.env` 环境变量配置。运行前请务必确认以下变量已正确设置：

```ini
# ==========================================
# 1. 远程源数据库配置 (Source DB)
# ==========================================
DEFECT_SOURCE_DB_TYPE=sqlserver            # 源库类型：支持 sqlserver 或 postgres
DEFECT_SOURCE_DB_HOST=127.0.0.1            # 源数据库 IP
DEFECT_SOURCE_DB_PORT=1433                 # 端口（SQL Server 默认 1433, PG 默认 5432）
DEFECT_SOURCE_DB_NAME=source_db            # 源数据库名称
DEFECT_SOURCE_DB_USER=sa                   # 登录用户名
DEFECT_SOURCE_DB_PASSWORD=your_pwd         # 登录密码
DEFECT_SOURCE_DB_SCHEMA=dbo                # 外部 Schema（SQL Server 通常为 dbo，PG 通常为 public）

# ==========================================
# 2. 本地目标数据库配置 (Target DB)
# ==========================================
DEFECT_TARGET_DB_HOST=localhost            # 本地 PG 地址
DEFECT_TARGET_DB_PORT=5432
DEFECT_TARGET_DB_USER=postgres
DEFECT_TARGET_DB_PASSWORD=your_local_pwd
DEFECT_TARGET_DB_NAME=analytics_db

# ==========================================
# 3. 增量同步与自动剪裁策略 (Retention & Tuning)
# ==========================================
DEFECT_SUMMARY_BATCH_SIZE=2000             # 单次增量批次大小
DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW=500   # 并发防漏重放回溯窗口大小
DEFECT_SUMMARY_RETENTION_MODE=max_rows     # 数据裁剪策略：off (不清理), max_rows (按行限制), max_months (按时间限制), both
DEFECT_SUMMARY_RETENTION_MAX_ROWS=50000    # 本地汇总表最大保留数据行数
DEFECT_SUMMARY_RETENTION_MAX_MONTHS=3      # 本地汇总表最大保留月数（如 max_months 启用）
```

---

## 🚀 3. 完整操作与测试流程

测试前请先在命令行中激活指定 Conda 环境：
```powershell
conda activate websoket
```

### 步骤一：一键首次初始化 (Bootstrap Mode)
如果您是首次在当前本地数据库运行，或者想要重置表结构：
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py --init-state
```
*   **内置动作**：脚本会以会话级强锁上海时区方式自动执行**内置**的本地建表 SQL。如果本地表不存在将全自动创建，并自动读取 [model_map.json](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/model_map.json) 将静态车型数据同步导入目标库的 `model_attribute_map` 中，随后设定初始同步水位。
*   **💡 强力建议（LLM 大模型深度适配）**：
    虽然 Python 脚本会自动完成最基础的建表以确保“零依赖、开箱即用”，但**它在运行时并不会调用或读取外部的 [history_station_defect_summary.sql](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/history_station_defect_summary.sql) 文件**。
    为了能让您的 **LLM 数据库助手 (SQL Agent/AI Copilot)** 完美理解数据字段含义，强烈建议您在初始化完成后，在数据库管理工具（如 DBeaver, pgAdmin 或 psql）中手动执行一遍该 SQL 文件（尤其是后半部分的 `COMMENT ON COLUMN` 和 `COMMENT ON TABLE` 注释段落）。这会将高质量的字段中文注释刷入数据库元数据中，让大模型分析数据时更具智慧！

### 步骤二：执行增量同步刷新 (Incremental Sync)
运行增量同步任务，执行实际的缺陷提取、聚合与写入：
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py --refresh
```
*   **动作**：流式从源数据库拉取未处理的车辆缺陷信息，仅统计 `station` 在 1~5 且 `diameter > 0` 的缺陷总数，翻译车型后以 UPSERT 幂等方式写入本地表。完成后若超出保留上限，自动在数据库事务中进行低水位自动裁剪，最后推进水位线并记录审计日志。

### 步骤三：同步状态与审计查询 (Print Status)
如果您想查询当前数据同步的进度，而不执行任何数据修改，可以运行：
```powershell
python defect_summary_etl/refresh_history_station_defect_summary.py --print-status
```
*   **输出内容**：
    *   当前同步源库类型、连接配置及裁剪规则。
    *   本地汇总表的总行数、历史 ID 范围、绝对时间段（`TIMESTAMPTZ` 时区格式）。
    *   最后 5 次增量运行的详细监控日志（开始/结束时间、状态、处理条数、详细错误等）。

---

## 📅 4. 日常运维与生产调度

### ① Windows 计划任务后台静默调度
若要将该同步脚本部署在本地 Windows 服务器做持续后台同步（例如每 10 分钟运行一次）：
1.  在根目录下新建 `refresh_defect_summary.bat` 批处理文件：
    ```bat
    @echo off
    cd /d f:\000_dev\Python\workplace\savedatabase-postgresql_v2
    call conda activate websoket
    python defect_summary_etl/refresh_history_station_defect_summary.py --refresh >> defect_summary_sync.log 2>&1
    ```
2.  打开 Windows **任务计划程序 (Task Scheduler)**，创建一个新任务。
3.  触发器设为“每天运行”，并在高级设置中勾选“重复任务间隔：每 10 分钟”。
4.  操作设为“启动程序”，选择指向此 `.bat` 路径。

### ② 新增车型的维护机制
当现场有新车型（如车型代码 `88`）上线时，**完全不需要修改任何数据库 Schema 或代码**，仅需：
1.  修改 [model_map.json](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/defect_summary_etl/model_map.json)，在数组中追加新车型的映射信息：
    ```json
    {
      "model": 88,
      "type_name": "New SUV Model",
      "black_roof": "黑车顶"
    }
    ```
2.  下一次日常增量同步 `--refresh` 运行时，脚本会自动读取并热刷新数据库内的车型属性，之后的检测记录将被全自动翻译。

---

## 💎 5. 注意事项
*   **Advisory Lock**：本地同步进程开启了 PostgreSQL 会话锁限制（Lock Key: `20260413`），在同一台服务器上绝对不允许两个并发的 refresh 脚本实例同时对同一个库写入，防止任务重合时数据错乱。
*   **审计日志**：日常运行的批次和异常信息均可以通过查询本地 `history_station_defect_summary_refresh_log` 审计表获得。

---
*修改时间：2026-05-17*
