# 分析数仓三链路定时刷新技术方案

修改时间：2026-05-17 Asia/Shanghai

主要修改内容：
- **项目背景**：梳理 Phase 2 物理数据库 FDW 解耦后常规分析、缺陷汇总和 Carbody 三个刷新链路的现状。
- **业务需求**：定义了 2~5 分钟高频刷新、后台静默无弹窗、稳定开机自启、隔离无污染的诉求。
- **方案对比**：多维度比较 Windows 任务计划程序、WSL Cron 及 Docker Compose 统一调度的优劣。
- **推荐架构**：给出基于 Docker 容器的 Python 定时任务调度器的最稳定架构方案。
- **评审更新**：根据 DeepSeek 审查结果，明确了针对依赖构建、网络代理、重叠执行、日志轮转等核心风险的最终落地解决策略。

---

## 1. 项目背景 (Background)

随着项目分析数仓 (`analytics_db`) 的架构演进至 Phase 2，我们对外部数据源的抽取逻辑进行了彻底解耦与重构。当前系统中存在三条互相独立的底层数据刷新链路：
1. **Carbody 链路**：通过宿主机环境执行的纯 Python 直连 ETL 脚本 `python carbody_etl/refresh_carbody_ods.py`。负责增量抽取 SQL Server 源数据，并在库内触发维表及富集宽表的更新。
2. **缺陷汇总链路**：通过 Python ETL 脚本 `python defect_summary_etl/refresh_history_station_defect_summary.py --refresh`，从源库增量抽取缺陷检测结果写回本地汇总表。
3. **常规分析链路**：基于 PostgreSQL FDW（外部表）直接在库内执行的 `CALL meta.refresh_analytics_all();`，负责刷新滚床实时占位与缺陷汇总数据。

为了保障大屏和 AI Agent 能够随时读取到准实时的数据，必须将这三条链路按依赖顺序进行工程化的定时调度部署。

---

## 2. 业务与技术需求 (Requirements)

- **高频时效性**：三条数据链路均需满足 **2~5 分钟** 的高频次增量刷新要求。
- **运行环境兼容**：宿主机底座为 Windows 操作系统，同时启用了 WSL 2 子系统与 Docker Desktop 容器引擎，部署方案必须与该基础设施相融合。
- **极致稳定性**：调度器需要 7x24 小时后台静默运行，具备网络闪断重连机制，且**绝对不能**在运行时弹出黑框（Cmd/PowerShell 窗口）打断用户的日常桌面操作。
- **依赖隔离**：必须妥善处理 `psycopg2` (PG) 和 `pytds` (SQL Server) 在并发调度时的依赖环境，避免出现系统级的 DLL 冲突或路径错乱。

---

## 3. 部署方案对比分析 (Solution Comparison)

基于当前的宿主机环境，我们对三种主流调度方案进行了多维度对比：

| 评估维度 | 方案 A：Windows 任务计划程序 | 方案 B：WSL 2 原生 Cron | 方案 C：Docker 容器化统一调度 (推荐) |
| :--- | :--- | :--- | :--- |
| **底层实现** | 依赖 `taskschd.msc` 调用 PS1 与 Python.exe | 在 Ubuntu/Debian 内写 `crontab` 守护进程 | 编写 `scheduler.py` 驻留并打包在独立容器 |
| **静默运行** | ❌ 极易失败，若强制隐藏易导致 Session 环境变量丢失或网络映射失效 | ✅ 完全后台运行 | ✅ 容器化后台守护，极致静默 |
| **开机自启** | ✅ 支持，但配置“不管用户是否登录均运行”时极易踩坑报 `0x1` 错误 | ❌ WSL 的 cron 服务随系统重启后**默认不启动**，需额外部署 vbs 自启脚本，架构脆弱 | ✅ Docker 引擎原生支持 `restart: always`，稳定拉起 |
| **网络可达性** | ⚠️ 依赖宿主机网络到 Docker (localhost:5432) 的端口转发，高频并发时偶现 TCP 拥塞 | ⚠️ 依赖 WSL 虚拟网卡到 Windows 的 NAT 穿透 | ✅ **完美**，与 DB 同属 `app-network` 虚拟网，走服务名直连，网络链路最短最稳 |
| **依赖与隔离** | ❌ 强依赖 Windows 环境变量与 Conda 激活状态，极易被全局环境污染 | ✅ Linux 原生环境，Python 依赖兼容性极佳 | ✅ 完全沙盒隔离，基于轻量级 `python:3.10-slim`，无残留无污染 |

### 调研结论
经过综合研判，**方案 C（Docker 容器化统一调度）**具有压倒性优势。您的核心资产（PostgreSQL 与 data-saver-service）已经运行在 `docker-compose.yml` 的 `app-network` 中，将调度器一同接入该网络不仅能获得最佳的网络 IO 性能，更实现了项目运行依赖的“一键式编排 (One-Command Deployment)”。

---

## 4. 最终推荐架构设计 (Final Recommended Architecture)

我们将采用 **Docker Compose 容器化 Python 调度器** 方案。

### 架构图示简述
```text
[ Docker Compose : app-network ]
   ├── postgres (Database)
   ├── data-saver-service (WebSocket采集)
   └── refresh-scheduler (本次新增调度器)
         └── schedule.every(3).minutes ->
                ├── Step 1: subprocess 执行 refresh_carbody_ods.py (Carbody 链路)
                ├── Step 2: subprocess 执行 refresh_history_station_defect_summary.py --refresh (缺陷汇总链路)
                └── Step 3: psycopg2 执行 CALL meta.refresh_analytics_all() (分析链路)
```

---

## 5. 详细实施步骤 (Proposed Changes)

为了落地上述技术方案，我将在代码库中执行以下修改：

### 5.1 增加调度器核心依赖
- 在 `requirements.txt` 中引入轻量级任务编排库 `schedule==1.2.2`。

### 5.2 编写统一调度器服务主入口
- 在 `defect_database/scripts/scheduler_main.py` 实现一个稳健的 `while True` 守护进程。
- **顺序执行**：每轮调度按依赖顺序串行执行——先 Carbody 链路 (`refresh_carbody_ods.py`)，再缺陷汇总 (`refresh_history_station_defect_summary.py --refresh`)，最后通过 `psycopg2` Session 调用 `CALL meta.refresh_analytics_all()`，确保分析链路汇总的是最新的源数据。
- **容错与防御**：加入完善的 `try-except` 捕获块。即便单次（如第 N 个 3 分钟）因为网络抖动导致连接失败，调度器也会仅记录 `ERROR` 并在下一个 3 分钟自动重试，确保主进程永不崩溃。

### 5.3 制定容器镜像规范
- 编写 `Dockerfile.scheduler`，基于 `python:3.10-slim`（稳定且体积小）。
- 设置正确的时区环境变量（`TZ=Asia/Shanghai`），确保日志时间戳与本地一致。
- 注入项目代码依赖并定义服务启动入口。

### 5.4 注册到集群编排体系
- 在 `docker-compose.yml` 中新增名为 `refresh-scheduler` 的服务节点。
- 设置 `restart: always`。
- 与 `postgres` 服务共享 `app-network`，并在 `.env` 加载时让 DB_HOST 默认指向 `postgres`。

---

## 6. 验证计划 (Verification Plan)

### Automated Tests
1. 实施代码修改后，在您的终端内执行 `docker-compose up -d --build refresh-scheduler` 启动守护进程。
2. 通过 `docker logs -f refresh-scheduler` 实时监视输出，观察服务启动 3 分钟后，三条链路是否按序成功执行并打印成功日志。

### Manual Verification
- 服务平稳运行 10 分钟后，登录 PostgreSQL 数据库查阅 `meta.sync_job_log` 表，核对是否已经产生了至少 3 批（每 3 分钟一批）的自动调度执行审计记录。

---

## 7. DeepSeek 审核结果 (DeepSeek Audit)

审核时间：2026-05-17 | 审核模型：DeepSeek-v4-pro

### 审核与方案落地结论

根据最新一轮评审，针对 DeepSeek 提出的 P0-P3 问题，已确定如下落地解决策略：

| 优先级 | # | 问题关注点 | 落地解决策略 |
|--------|---|------------|--------------|
| **P0** | 1 | `CALL meta.refresh_analytics_all()` 是否存在 | ✅ 已确认：SP 已存在于 `analytics_db`，直接使用即可。 |
| **P0** | 2 | `python:3.10-slim` 缺乏编译依赖 | ✅ **方案**：直接在 `requirements.txt` 中使用 `psycopg2-binary`，避免在 slim 镜像中额外安装 C 编译环境，极大加快镜像构建速度。`pytds` 为纯 Python 库无需额外编译。 |
| **P0** | 11 | 跨网段连通两个 SQL Server 源库 | ✅ **方案**：配套 [Docker Desktop WSL2 后端容器访问外部私有网络与代理集成指南.md](../Docker%20Desktop%20WSL2%20后端容器访问外部私有网络与代理集成指南.md) 已完美覆盖，在 WSL2 配置两个 `socat` 代理，容器内通过 `host.docker.internal:14330/14331` 直连。 |
| **P1** | 3 | `schedule` 单线程 vs 多线程并发 | ✅ **方案**：业务需求为串行执行以保证 ODS 层数据先行落盘。`schedule` 单线程阻塞模型天然符合业务的串行时序诉求。 |
| **P1** | 4 | 任务重叠与耗时风险 | ✅ **方案**：`schedule` 库是单线程阻塞的，单次耗时超长会自动推迟下次调度，天然防止“叠跑”。可在主循环内补充全局锁 `is_running` 作为双重防御。 |
| **P1** | 5 | 缺失环境变量清单 | ✅ **方案**：在 `docker-compose.yml` 调度器节点配置 `env_file: .env`，使得所有代理端口和数据库账号密文能被容器读取。 |
| **P2** | 6 | 缺少容器 Healthcheck | ✅ **方案**：可于每轮执行结束时更新一个临时文件时间戳，并配置 Docker `healthcheck` 若长时间未更新则重启以防进程假死。首版开发可暂缓。 |
| **P2** | 7 | 日志长期累积导致磁盘膨胀 | ✅ **方案**：强烈建议首版即在 Compose 中配置 `logging.max-size: "10m"` 与 `max-file: "3"` 进行日志自动轮转清理。 |
| **P2/3** | 8-10 | 告警、回滚与库版本确认 | 建议在首版部署平稳运行后，再作为常规运维项迭代补齐。 |

### 最终实施结论

方案整体架构严谨且可行性极高，推荐的方案 C 在当前基础设施下属于最优解。通过上述落地策略对各优先级风险进行闭环后，目前已清除所有阻塞问题，可直接推进 `scheduler_main.py`、`Dockerfile.scheduler` 和 `docker-compose.yml` 的编码实现与落地。
