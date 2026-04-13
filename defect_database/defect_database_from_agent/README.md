# Database Snapshots

更新时间：2026-04-13 18:05 Asia/Shanghai

本目录用于保存缺陷数据库的结构快照、车型映射、初始化 SQL 与增量刷新说明，便于本地分析、上线初始化与后续运维。

当前文件：

- `defect_db_schema_snapshot.json`：`defect_db` 中 5 张源业务表的字段结构快照
- `model_map.json`：`history.model` 到 `type_name`、`black_roof` 的本地映射来源
- `history_station_defect_summary.sql`：本地 `defect_db` 初始化 SQL，负责创建汇总表、映射表、刷新状态表、刷新日志表与常用索引
- `history_station_defect_summary_schema.md`：面向大模型分析的汇总表 Markdown schema 说明
- `../refresh_history_station_defect_summary.py`：增量刷新脚本，支持本地 PostgreSQL target + PostgreSQL/SQL Server source

来源说明：

- 目标数据库：本地 `defect_db`
- 目标 schema：`public`
- 源表范围：`history`、`history_detail`
- 车型映射来源：本地 `model_map.json` 与 `model_attribute_map`

## 整体设计

当前方案的核心约束是：

- `history_station_defect_summary` 始终保留在本地 `defect_db`
- 只切换源库，不切换目标库
- 源表默认只有新增，不做历史更新和删除
- `model_attribute_map` 以本地映射为准，不从远程库同步
- 使用外部调度，不在脚本内常驻循环

这意味着脚本采用的是“**双连接、单次执行、增量落库**”模式：

- `TARGET` 连接：始终写本地 `defect_db`
- `SOURCE` 连接：读取 PostgreSQL 或 SQL Server 中的 `history`、`history_detail`
- 每次执行一次 `--refresh`，处理完当前增量后退出

## 刷新原理

### 1. 初始化对象

先执行：

- `defect_database/defect_database_from_agent/history_station_defect_summary.sql`

该 SQL 只负责初始化和补齐对象，不再做 `DROP TABLE`、`TRUNCATE` 或全量重刷。它会创建或补齐：

- `model_attribute_map`
- `history_station_defect_summary`
- `history_station_defect_summary_refresh_state`
- `history_station_defect_summary_refresh_log`
- 汇总表常用索引

### 2. 首次建立水位

首次上线前执行：

```bash
python defect_database/refresh_history_station_defect_summary.py --init-state
```

脚本会先保证目标侧表结构存在，再初始化一条刷新状态记录。

`DEFECT_SUMMARY_BOOTSTRAP_MODE` 决定首个水位怎么取：

- `from_summary`
  - 如果本地汇总表已经有历史数据，则把 `MAX(history_id)` 作为首个成功水位
  - 这样可以避免首次上线时把全量历史再刷一遍
- `from_zero`
  - 从 `0` 开始
  - 适合本地汇总表为空，或者希望重新从头补数的场景

### 3. 增量刷新主流程

执行：

```bash
python defect_database/refresh_history_station_defect_summary.py --refresh
```

每次刷新按下面的流程运行：

1. 加载 `.env`，确定目标库和源库连接参数。
2. 连接本地目标库 `defect_db`，并确保目标对象存在。
3. 尝试获取 PostgreSQL advisory lock，避免两个任务同时刷新。
4. 从 `history_station_defect_summary_refresh_state` 读取最近一次成功水位。
5. 根据源库类型选择对应 SQL 方言，从源库 `history` 中找出本次候选 `history_id`。
6. 用候选 `history_id` 去源库聚合 `history + history_detail`。
7. 用本地 `model_attribute_map` 补齐 `type_name`、`black_roof`。
8. 通过 `INSERT ... ON CONFLICT(history_id) DO UPDATE` 写回本地汇总表。
9. 当前批次成功后，更新状态表和日志表。
10. 如果还有新的 `history_id` 没处理完，继续下一批，直到追平为止。

### 4. 为什么不是单纯 `history_id > watermark`

当前增量逻辑不是只取“新 `history_id`”，而是每次由两部分候选集组成：

- 新数据：`history_id > last_success_history_id`
- 回放窗口：`history_id` 落在最近一段 replay window 内

原因是源数据可能不是严格原子写入。实际排查时已经看到过：

- `history_detail` 中出现比 `history` 更大的 `history_id`

这类情况说明存在“主记录和明细记录不同步到达”的可能。如果只按新 `history_id` 取数，就可能漏掉稍晚到达的 `history_detail`。因此脚本每次都会把最近一段 `history_id` 再算一遍，然后靠 `UPSERT` 覆盖旧结果。

### 5. 聚合口径

刷新脚本的聚合口径与现有汇总表定义保持一致：

- 一条汇总记录对应一个 `history_id`
- 只统计 `station IN (1, 2, 3, 4, 5)`
- 只统计 `diameter > 0`
- `total_defect_count` 等于五个站点缺陷数之和
- `type_name`、`black_roof` 来自本地 `model_attribute_map`

### 6. 写入方式

本地写入使用：

- `INSERT ... ON CONFLICT(history_id) DO UPDATE`

这样可以同时覆盖两种场景：

- 新的 `history_id`：插入新汇总行
- replay window 内已有的 `history_id`：更新旧汇总行

因此不会清空本地汇总表，也不会做全量重建。

### 7. 水位推进规则

主水位固定用：

- `history.history_id`

状态表中会记录：

- `last_success_history_id`
- `last_success_date_time`
- 最近一次开始时间、结束时间、状态、说明

其中：

- `last_success_history_id` 是真正用于增量筛选的主游标
- `last_success_date_time` 只是审计信息，便于排查，不参与主筛选条件

水位只会在“当前批次成功提交”之后才推进。如果批次失败：

- 本批事务回滚
- 水位不推进
- 日志表记录失败信息

### 8. 并发控制

刷新脚本使用 PostgreSQL advisory lock：

- `pg_try_advisory_lock(DEFECT_SUMMARY_LOCK_KEY)`

作用是避免同一时间两个调度任务重复刷新。如果抢不到锁：

- 当前脚本不会报错退出为失败
- 会记录一条 `skipped` 日志
- 状态表也会记录“本次因锁冲突跳过”

### 9. 状态表和日志表分别做什么

`history_station_defect_summary_refresh_state` 负责保存“当前结果”：

- 最近一次成功水位
- 最近一次执行状态
- 最近一次执行时间

`history_station_defect_summary_refresh_log` 负责保存“执行历史”：

- 每次批次的开始/结束时间
- 当前 source 来自哪个数据库
- 候选量、写入量
- 水位变化
- 状态和错误信息

如果只想看当前进度，查状态表；如果要追溯执行过程，查日志表。

## 配置参数说明

请参考根目录 [.env_example](/F:/000_dev/Python/workplace/savedatabase-postgresql_v2/.env_example:1)。

### 1. 目标库参数

- `DEFECT_TARGET_DB_HOST`
  - 本地目标库主机地址
  - 默认：`localhost`
- `DEFECT_TARGET_DB_PORT`
  - 本地目标库端口
  - 默认：`5432`
- `DEFECT_TARGET_DB_NAME`
  - 本地目标数据库名
  - 默认：`defect_db`
- `DEFECT_TARGET_DB_USER`
  - 本地目标库用户名
  - 默认：`root`
- `DEFECT_TARGET_DB_PASSWORD`
  - 本地目标库密码
  - 默认：`root`

说明：

- 这些参数决定“汇总表写到哪里”
- 当前设计要求它们始终指向本地 `defect_db`

### 2. 源库参数

- `DEFECT_SOURCE_DB_TYPE`
  - 源库类型
  - 可选：`postgres`、`sqlserver`
- `DEFECT_SOURCE_DB_HOST`
  - 源库主机地址
- `DEFECT_SOURCE_DB_PORT`
  - 源库端口
- `DEFECT_SOURCE_DB_NAME`
  - 源库数据库名
- `DEFECT_SOURCE_DB_USER`
  - 源库用户名
- `DEFECT_SOURCE_DB_PASSWORD`
  - 源库密码
- `DEFECT_SOURCE_DB_SCHEMA`
  - 源表所在 schema
  - `postgres` 默认：`public`
  - `sqlserver` 默认：`dbo`

说明：

- 这些参数决定“从哪里读取 `history` / `history_detail`”
- 如果源库相关字段全部留空，脚本会回退为“源库 = 目标库(PostgreSQL)”
- 如果开始填写远程源库参数，则必须把 `DEFECT_SOURCE_DB_TYPE / HOST / PORT / NAME / USER / PASSWORD` 一次性配齐
- 只填一部分时，脚本会直接报配置错误，避免误读本地库
- `DEFECT_SOURCE_DB_SCHEMA` 未填写时，会按源库类型使用默认 schema
- 如果远程 SQL Server 的密码本身就是空密码，请在 `.env` 中写成 `DEFECT_SOURCE_DB_PASSWORD=`，不要写占位符，也不要写成 `'-'`

推荐用法：

- 本地模式：`DEFECT_SOURCE_DB_*` 全部留空
- PostgreSQL 远程模式：`DEFECT_SOURCE_DB_TYPE=postgres`，并把其余源库参数补齐
- SQL Server 远程模式：`DEFECT_SOURCE_DB_TYPE=sqlserver`，并把其余源库参数补齐

### 3. SQL Server 连接说明

当前脚本在 SQL Server 模式下使用：

- `python-tds`

特点：

- 只需要安装 Python 包
- 不依赖 Windows ODBC Driver
- 不需要额外配置 `DEFECT_SOURCE_DB_DRIVER`

说明：

- 运行 SQL Server 源库模式前，Python 环境需要安装 `python-tds`
- `DEFECT_SOURCE_DB_SCHEMA` 通常填写为 `dbo`
- 如果 SQL Server 账号本身没有密码，请直接写成 `DEFECT_SOURCE_DB_PASSWORD=`

### 4. 刷新行为参数

- `DEFECT_SUMMARY_BATCH_SIZE`
  - 每批最多处理多少个“新增 `history_id`”
  - 默认：`2000`
  - 影响单批时长和单次事务大小
- `DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW`
  - 每次额外回放多少个最近的 `history_id`
  - 默认：`500`
  - 用于覆盖晚到明细
- `DEFECT_SUMMARY_LOCK_KEY`
  - advisory lock 的整数 key
  - 默认：`20260413`
  - 同一个任务的所有调度实例必须使用同一个 key
- `DEFECT_SUMMARY_BOOTSTRAP_MODE`
  - 首次初始化水位方式
  - 可选：`from_summary`、`from_zero`
  - 默认：`from_summary`
- `DEFECT_SUMMARY_LOG_LEVEL`
  - Python 日志级别
  - 默认：`INFO`
- `DEFECT_SUMMARY_TIMEZONE`
  - 数据库会话时区
  - 默认：`Asia/Shanghai`

### 5. 参数调优建议

- 如果源库和目标库都在本地、数据量不大：
  - `DEFECT_SUMMARY_BATCH_SIZE=2000`
  - `DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW=500`
- 如果源库是 SQL Server：
  - 优先确认 `DEFECT_SOURCE_DB_SCHEMA` 是否正确，通常为 `dbo`
  - 优先确认 Python 环境已安装 `python-tds`
- 如果远程网络较慢：
  - 先把 `DEFECT_SUMMARY_BATCH_SIZE` 降到 `500` 或 `1000`
- 如果晚到明细更常见：
  - 可以适当增大 `DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW`
- 如果调度会重叠触发：
  - 保持 `DEFECT_SUMMARY_LOCK_KEY` 不变，让后来的任务自动跳过

## 使用方式

### 1. 初始化本地表结构

先在本地 `defect_db` 执行：

- `defect_database/defect_database_from_agent/history_station_defect_summary.sql`

### 2. 初始化状态

```bash
python defect_database/refresh_history_station_defect_summary.py --init-state
```

这个命令的作用不是正式刷新数据，而是给增量刷新任务“建档案、定起点”。

它主要会做 3 件事：

1. 检查并补齐目标库基础对象
   - 确保 `model_attribute_map`
   - 确保 `history_station_defect_summary`
   - 确保 `history_station_defect_summary_refresh_state`
   - 确保 `history_station_defect_summary_refresh_log`
2. 同步本地车型映射
   - 读取 `model_map.json`
   - 写入或更新本地 `model_attribute_map`
3. 建立第一条刷新状态记录
   - 记录增量刷新从哪个 `history_id` 开始
   - 作为后续 `--refresh` 的起始水位

你可以把它理解成：

- `--init-state`：初始化目标对象和刷新水位
- `--refresh`：按水位真正执行增量刷新
- `--print-status`：查看当前水位和最近执行情况

如果当前 `DEFECT_SUMMARY_BOOTSTRAP_MODE=from_summary`：

- 脚本会读取本地 `history_station_defect_summary` 现有的 `MAX(history_id)`
- 把这个值写入状态表
- 表示“当前汇总表里的历史数据视为已处理”

如果当前 `DEFECT_SUMMARY_BOOTSTRAP_MODE=from_zero`：

- 脚本会把首个水位设为 `0`
- 表示后续允许从头补齐历史数据

通常在以下场景下先执行一次 `--init-state` 会比较合适：

- 汇总表已有人手工或历史脚本填过数据
- 你准备首次切到增量刷新方案
- 你希望后续调度任务直接从当前进度接着跑

### 3. 执行一次增量刷新

```bash
python defect_database/refresh_history_station_defect_summary.py --refresh
```

如果当前源库是 SQL Server，请先确认：

- `.env` 中已完整填写 `DEFECT_SOURCE_DB_TYPE=sqlserver` 及其连接参数
- Python 环境已安装 `python-tds`

### 4. 查看状态

```bash
python defect_database/refresh_history_station_defect_summary.py --print-status
```

会输出：

- 本地汇总表当前行数与最大 `history_id`
- 最近一次成功水位
- 最近状态
- 最近 5 条刷新日志

当前脚本运行日志中，批次会按以下类型输出：

- `new_and_replay`
  - 当前批次同时包含新增 `history_id` 和 replay window
- `replay_only`
  - 当前批次只有 replay window，没有新增 `history_id`
  - 通常表示本次刷新已经进入收尾阶段

## 调度建议

推荐使用外部调度，不在脚本内部常驻循环：

- Windows：任务计划程序，每 `5 / 15 / 30` 分钟执行一次 `--refresh`
- Linux / Docker：使用 `cron` 或宿主调度器执行同一命令

建议：

- 如果需要更实时：用 `5` 分钟
- 如果更关注稳定和数据库压力：用 `15` 分钟或 `30` 分钟

## 定期刷新最佳实践

### 1. 推荐模式

建议采用“**外部调度器 + 脚本单次执行**”模式，而不是把 Python 脚本改成死循环常驻服务。

原因是当前脚本已经内建了定时任务最关键的能力：

- 单次执行完即退出，适合被任务计划程序或 `cron` 托管
- 有 `history_id` 水位，不会每次全量重刷
- 有 replay window，可覆盖晚到的 `history_detail`
- 有 advisory lock，可避免同一时刻重复刷新
- 有状态表和日志表，便于追踪任务健康度

因此最佳实践不是再在脚本里加 `while true`，而是：

1. 先执行一次 `--init-state`
2. 后续由调度器固定周期执行 `--refresh`
3. 用 `--print-status` 或查询状态表做巡检

### 2. Windows 任务计划程序推荐做法

如果你的运行环境主要在 Windows，推荐使用“任务计划程序（Task Scheduler）”。

推荐配置如下：

- 触发器（Trigger）
  - 每 `5` 分钟执行一次，适合准实时
  - 或每 `15` 分钟执行一次，适合更稳妥的生产环境
- 操作（Action）
  - 不要直接写很多复杂命令
  - 最好固定调用一个 `PowerShell` 脚本或 `bat` 包装脚本
- 并发策略
  - 任务计划程序里建议设置“如果任务已经在运行，则不启动新实例”
  - 即使忘了配置，脚本里的 advisory lock 也会兜底，但调度器层面最好也限制一次只跑一个实例
- 超时策略
  - 建议配置“运行超过预期时长后停止”，阈值可先设为 `30` 到 `60` 分钟
- 工作目录
  - 建议显式设置为仓库根目录，避免 `.env`、相对路径和日志路径解析错误

推荐的包装脚本逻辑：

```powershell
# 修改时间：2026-04-13 17:10 Asia/Shanghai
$ProjectRoot = "F:\000_dev\Python\workplace\savedatabase-postgresql_v2"
$PythonExe = "C:\Path\To\Miniconda3\envs\websoket\python.exe"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "history_station_defect_summary_refresh.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectRoot

$startAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$startAt] start refresh"

& $PythonExe "defect_database/refresh_history_station_defect_summary.py" --refresh *>> $LogFile
$exitCode = $LASTEXITCODE

$endAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$endAt] finish refresh exit_code=$exitCode"

exit $exitCode
```

任务计划程序中可参考以下配置：

- Program/script：
  - `powershell.exe`
- Add arguments：
  - `-NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\scripts\refresh_history_station_defect_summary.ps1"`
- Start in：
  - `F:\000_dev\Python\workplace\savedatabase-postgresql_v2`

说明：

- 最稳妥的方式是直接指定 `websoket` 环境里的 `python.exe`
- 比起在计划任务里临时执行 `conda activate websoket`，这样更稳定，也更容易排查
- 如果你确实要用 `conda activate`，建议也放到包装脚本里，而不是直接塞进任务计划程序参数

### 3. Linux / Docker 推荐做法

如果部署在 Linux 或 Docker 宿主机，推荐使用 `cron` 或宿主层调度器。

示例：

```cron
*/5 * * * * cd /path/to/savedatabase-postgresql_v2 && /path/to/miniconda3/envs/websoket/bin/python defect_database/refresh_history_station_defect_summary.py --refresh >> logs/history_station_defect_summary_refresh.log 2>&1
```

建议：

- 仍然使用单次 `--refresh`
- 仍然直接写绝对路径的 `python`
- 仍然把日志重定向到固定文件
- 如果在容器里运行，优先让宿主机调度容器命令，不建议在业务脚本里自己做循环

### 3.1 Docker Desktop 最稳方案

如果当前环境是 Windows + Docker Desktop，推荐使用：

- Docker 负责提供 `postgres`、`data-saver-service` 和独立的 `defect-refresh` 运行环境
- Windows 任务计划程序负责按固定周期触发一次 `defect-refresh`
- 每次任务仍然只执行单次命令，然后退出

当前仓库已补充以下文件：

- 根目录 `Dockerfile.defect-refresh`
  - 专门用于构建缺陷汇总刷新镜像
- 根目录 `docker-compose.yml`
  - 新增 `defect-refresh` 服务定义
- `scripts/refresh_history_station_defect_summary_docker.ps1`
  - 供 Windows 任务计划程序调用的包装脚本

推荐执行模型：

1. 常驻启动基础服务

```bash
docker compose up -d postgres data-saver-service
```

2. 首次初始化状态

```bash
docker compose --profile manual run --rm defect-refresh --init-state
```

3. 手工执行一次刷新

```bash
docker compose --profile manual run --rm defect-refresh --refresh
```

4. 查看状态

```bash
docker compose --profile manual run --rm defect-refresh --print-status
```

5. 最后由 Windows 任务计划程序定时执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\000_dev\Python\workplace\savedatabase-postgresql_v2\scripts\refresh_history_station_defect_summary_docker.ps1"
```

说明：

- 包装脚本默认执行 `--refresh`
- 如果要初始化或查看状态，也可以手工追加参数：
  - `-Mode --init-state`
  - `-Mode --print-status`
- 宿主机日志会写到 `logs/history_station_defect_summary_docker.log`

### 3.2 Docker Desktop 方案的前置条件

Docker Desktop 方案里，`defect-refresh` 容器会自动把：

- `DEFECT_TARGET_DB_HOST` 覆盖为 `postgres`

原因是容器内访问 compose 网络中的 PostgreSQL，应该使用服务名，而不是 `localhost`。

但仍然要注意下面两个前置条件：

- `DEFECT_TARGET_DB_NAME` 指向的目标数据库必须已经存在
- 当前 compose 里的 `postgres` 默认初始化数据库仍是 `POSTGRES_DB`，通常是 `rollerbed_tracking_db`

如果你希望缺陷汇总写入 `defect_db`，请确认以下二选一已经完成：

- 在 compose 的 PostgreSQL 实例里手工创建过 `defect_db`
- 或者把 `.env` 中的 `DEFECT_TARGET_DB_NAME` 改成当前实际存在的目标数据库名

一旦目标数据库存在，后续表结构、状态表、日志表都可以由：

```bash
docker compose --profile manual run --rm defect-refresh --init-state
```

自动补齐。

### 4. 刷新频率怎么选

推荐从 `5` 分钟或 `15` 分钟开始，不建议一上来就按分钟级甚至更短周期跑。

经验建议：

- `5` 分钟
  - 适合希望尽快看到新汇总结果
  - 前提是单次刷新通常能在 `1` 到 `2` 分钟内完成
- `15` 分钟
  - 更适合生产默认值
  - 能明显降低对源库、目标库和网络链路的压力
- `30` 分钟
  - 适合业务低频或夜间补数场景

判断是否需要调小频率，可以重点看：

- 单次 `--refresh` 的总耗时是否持续接近调度间隔
- 日志里是否经常出现 `skipped`
- 每批 `candidate_count` 和 `upserted_count` 是否长期偏大

### 5. 参数调优建议

定期刷新稳定性，通常比“极限吞吐”更重要。建议优先控制下面两个参数：

- `DEFECT_SUMMARY_BATCH_SIZE`
  - 默认 `2000`
  - 如果远程 SQL Server 较慢，建议先降到 `500` 或 `1000`
  - 如果本地 PostgreSQL 很稳定、网络也快，再考虑逐步上调
- `DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW`
  - 默认 `500`
  - 如果确认存在明细晚到，宁可略大，也不要设成 `0`
  - 如果日志显示每次 replay 都很重、但晚到几乎没有，再考虑适当下调

比较稳妥的起步组合：

- 本地 PostgreSQL 源：`BATCH_SIZE=2000`，`REPLAY_HISTORY_WINDOW=500`
- 远程 PostgreSQL 源：`BATCH_SIZE=1000`，`REPLAY_HISTORY_WINDOW=500`
- 远程 SQL Server 源：`BATCH_SIZE=500`，`REPLAY_HISTORY_WINDOW=500`

### 6. 监控与巡检建议

不要只看计划任务“是否触发”，还要看业务水位是否真的推进。

至少建议做这几件事：

- 每天或每班次执行一次 `--print-status`
- 关注 `last_success_history_id` 是否持续增长
- 关注 `last_status` 是否长期为 `success / noop / skipped`
- 如果连续多次为 `failed`，优先检查源库连通性、账号权限、schema 名称和 Python 依赖
- 定期查看 `history_station_defect_summary_refresh_log`，确认是否出现异常长耗时或异常大批次

如果后续要接企业监控，推荐把下面这些指标纳入告警：

- 最近一次成功时间
- 最近一次成功水位
- 连续失败次数
- 单次刷新耗时
- 最近 N 次任务里 `skipped` 的比例

### 7. 上线注意事项

正式启用定期刷新前，建议按这个顺序执行：

1. 本地确认 `.env` 已配置正确，尤其是 `DEFECT_TARGET_DB_*` 与 `DEFECT_SOURCE_DB_*`
2. 先执行一次 `--init-state`
3. 手工执行一次 `--refresh`
4. 执行一次 `--print-status`，确认状态表、日志表和汇总表都正常
5. 最后再把 `--refresh` 加入任务计划程序或 `cron`

不建议把下面这些动作放进周期任务里：

- 不要每次调度都执行 `--init-state`
- 不要在周期任务里自动改 `.env`
- 不要把“清表 / 重刷全量”混进同一个定时命令

## 常见排查点

- `--init-state` 后水位不为 `0`
  - 说明当前使用的是 `from_summary`
  - 脚本读取了本地汇总表已有的最大 `history_id`
- `--refresh` 执行了但没有新增
  - 先用 `--print-status` 查看最近状态和日志
  - 如果日志是 `noop`，说明当前没有可处理的新数据
  - 如果日志是 `skipped`，说明本次没有抢到锁
- 明明没有新 `history_id`，为什么还会写入
  - 因为 replay window 会重新计算最近一段数据
  - 这属于预期行为，用来覆盖晚到的 `history_detail`
- 为什么一次 `--refresh` 经常看到两批日志
  - 常见情况是第一批为 `new_and_replay`
  - 第二批为 `replay_only`
  - 第二批通常是最新水位附近的收尾重算，不代表重复全量刷新
- 远程切换后为什么结果还写到本地
  - 这是当前方案的固定设计
  - 远程只影响源数据读取，不影响本地目标落库
- 只填了 `DEFECT_SOURCE_DB_HOST`，为什么脚本直接报错
  - 这是新版本的保护机制
  - 只要开始配置远程源库，就必须把必要字段一次性补齐
  - 这样可以避免误回退到本地目标库
- SQL Server 模式报 `python-tds` 导入错误
  - 说明当前 Python 环境还没安装 `python-tds`
  - 先执行 `pip install python-tds`
