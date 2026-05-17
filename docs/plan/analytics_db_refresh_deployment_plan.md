# 分析数仓双链路定时刷新技术方案

修改时间：2026-05-17 Asia/Shanghai

主要修改内容：
- **项目背景**：梳理 Phase 2 物理数据库 FDW 解耦后常规分析和 Carbody 两个刷新链路的现状。
- **业务需求**：定义了 2~5 分钟高频刷新、后台静默无弹窗、稳定开机自启、隔离无污染的诉求。
- **方案对比**：多维度比较 Windows 任务计划程序、WSL Cron 及 Docker Compose 统一调度的优劣。
- **推荐架构**：给出基于 Docker 容器的 Python 定时任务调度器的最稳定架构方案。

---

## 1. 项目背景 (Background)

随着项目分析数仓 (`analytics_db`) 的架构演进至 Phase 2，我们对外部数据源的抽取逻辑进行了彻底解耦与重构。当前系统中存在两条互相独立的底层数据刷新链路：
1. **常规分析链路**：基于 PostgreSQL FDW（外部表）直接在库内执行的 `CALL meta.refresh_analytics_all();`。负责刷新滚床实时占位与缺陷汇总数据。
2. **Carbody 链路**：由于废弃了存在多期冲突的旧版 FDW，现已转为通过宿主机环境执行的纯 Python 直连 ETL 脚本 `python carbody_etl/refresh_carbody_ods.py`。该脚本负责增量抽取 SQL Server 源数据，并在库内触发维表及富集宽表的更新。

为了保障大屏和 AI Agent 能够随时读取到准实时的数据，必须将这两条独立链路进行工程化的定时调度部署。

---

## 2. 业务与技术需求 (Requirements)

- **高频时效性**：两条数据链路均需满足 **2~5 分钟** 的高频次增量刷新要求。
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
         ├── Thread 1: schedule.every(3).minutes -> 调用 psycopg2 执行 refresh_analytics_all()
         ├── Thread 2: schedule.every(3).minutes -> 调用 subprocess 执行 refresh_carbody_ods.py
         └── Thread 3: 每周日凌晨 03:00         -> 执行 refresh_carbody_ods.py --full-refresh
```

---

## 5. 详细实施步骤 (Proposed Changes)

为了落地上述技术方案，我将在代码库中执行以下修改：

### 5.1 增加调度器核心依赖
- 在 `requirements.txt` 中引入轻量级任务编排库 `schedule==1.2.2`。

### 5.2 编写统一调度器服务主入口
- 在 `defect_database/scripts/scheduler_main.py` 实现一个稳健的 `while True` 守护进程。
- **任务隔离**：利用 `subprocess.run()` 挂载执行 Carbody 抽取任务，避免内存泄漏；通过独立的 `psycopg2` Session 调用 PG 分析链路刷新。
- **容错与防御**：加入完善的 `try-except` 捕获块。即便单次（如第 N 个 3 分钟）因为网络抖动导致连接失败，调度器也会仅记录 `ERROR` 并在下一个 3 分钟自动重试，确保主进程永不崩溃。

### 5.3 制定容器镜像规范
- 编写 `Dockerfile.scheduler`，基于 `python:3.10-slim`（稳定且体积小）。
- 设置正确的时区环境变量（`TZ=Asia/Shanghai`），确保“周日 3 点”触发时间准确无误。
- 注入项目代码依赖并定义服务启动入口。

### 5.4 注册到集群编排体系
- 在 `docker-compose.yml` 中新增名为 `refresh-scheduler` 的服务节点。
- 设置 `restart: always`。
- 与 `postgres` 服务共享 `app-network`，并在 `.env` 加载时让 DB_HOST 默认指向 `postgres`。

---

## 6. 验证计划 (Verification Plan)

### Automated Tests
1. 实施代码修改后，在您的终端内执行 `docker-compose up -d --build refresh-scheduler` 启动守护进程。
2. 通过 `docker logs -f refresh-scheduler` 实时监视输出，观察服务启动 3 分钟后，两条链路是否成功触发了第一次并发执行并打印成功日志。

### Manual Verification
- 服务平稳运行 10 分钟后，登录 PostgreSQL 数据库查阅 `meta.sync_job_log` 表，核对是否已经产生了至少 3 批（每 3 分钟一批）的自动调度执行审计记录。
