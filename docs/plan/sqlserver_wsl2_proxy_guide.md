# Docker 容器调度器访问外部 SQL Server 源库 — WSL2 代理方案

修改时间：2026-05-17 Asia/Shanghai

## 1. 问题背景

根据已验证的 [Docker Desktop WSL2 后端容器访问外部私有网络问题指南](../Docker%20Desktop%20WSL2%20后端容器访问外部私有网络问题指南.md)，Docker Desktop WSL2 后端的容器网络对 RFC1918 私有网段（如 `172.21.x.x`、`172.22.x.x`）存在路由缺陷。`refresh-scheduler` 容器化部署后，面临同样的网络隔离问题。

### 受影响的两个 ETL 链路

| 链路 | 脚本 | 源库 | 目标 IP | 端口 | 连接库 |
|------|------|------|---------|------|--------|
| Carbody | `carbody_etl/refresh_carbody_ods.py` | SQL Server | `172.21.12.97` | 1433 | `pytds` |
| 缺陷汇总 | `defect_summary_etl/refresh_history_station_defect_summary.py` | SQL Server | `172.22.37.52` | 1433 | `pytds` |

两个源库位于**不同** SQL Server 实例，因此需要**两个独立的 socat 代理端口**。

## 2. 解决方案

沿用已验证的 **WSL socat 代理** 方案，在 WSL 中新增两个 TCP 端口转发：

```text
Docker 容器 (refresh-scheduler)
    │
    ├── CARBODY_SOURCE_DB_HOST=host.docker.internal:14330
    │         ↓
    │   Windows 宿主机 (host.docker.internal = 192.168.65.254)
    │         ↓
    │   WSL socat TCP-LISTEN 0.0.0.0:14330
    │         ↓
    │   172.21.12.97:1433 (Carbody SQL Server)
    │
    └── DEFECT_SOURCE_DB_HOST=host.docker.internal:14331
              ↓
        Windows 宿主机 (host.docker.internal = 192.168.65.254)
              ↓
        WSL socat TCP-LISTEN 0.0.0.0:14331
              ↓
        172.22.37.52:1433 (Defect SQL Server)
```

### 架构对比

**当前宿主机运行（无问题）：**
```text
Python 宿主机 → 172.21.12.97:1433 ✅ 直连可达 (Carbody)
Python 宿主机 → 172.22.37.52:1433 ✅ 直连可达 (Defect)
```

**容器化后（需要代理）：**
```text
refresh-scheduler 容器 → host.docker.internal:14330 → WSL socat → 172.21.12.97:1433
refresh-scheduler 容器 → host.docker.internal:14331 → WSL socat → 172.22.37.52:1433
```

## 3. 实施步骤

### 3.1 WSL 中新增 SQL Server 代理

在已有的 `start-socat-proxy.sh` 中追加两行：

```bash
# 编辑 /home/julius/wsl-scripts/start-socat-proxy.sh，追加：

# Carbody SQL Server 源库代理 (172.21.12.97:1433)
pkill -f "socat TCP-LISTEN:14330" 2>/dev/null || true
nohup /usr/bin/socat TCP-LISTEN:14330,fork,keepalive,bind=0.0.0.0 TCP:172.21.12.97:1433 >> /tmp/socat-proxy.log 2>&1 &

# Defect SQL Server 源库代理 (172.22.37.52:1433)
pkill -f "socat TCP-LISTEN:14331" 2>/dev/null || true
nohup /usr/bin/socat TCP-LISTEN:14331,fork,keepalive,bind=0.0.0.0 TCP:172.22.37.52:1433 >> /tmp/socat-proxy.log 2>&1 &
```

或者参照已有指南的 systemd 方案，新增两个 service 文件。

### 3.2 .env 配置调整

容器内需要将 `*_SOURCE_DB_HOST` 改为 `host.docker.internal`，端口改为对应代理端口：

```bash
#---------------------------------------------------------carbody_history SQL Server Source------------------------------
CARBODY_SOURCE_DB_HOST=host.docker.internal    # ← 原 localhost
CARBODY_SOURCE_DB_PORT=14330                    # ← 原 1433，经 WSL socat 转发至 172.21.12.97:1433
CARBODY_SOURCE_DB_NAME=DXQcontrol_SVWMEB_BI_DWH
CARBODY_SOURCE_DB_USER=sa
CARBODY_SOURCE_DB_PASSWORD=Sa123456!
CARBODY_SOURCE_DB_SCHEMA=dwh
CARBODY_SOURCE_TABLE_NAME=MDS_HISTORIC

#---------------------------------------------------------defect_db SQL Server Source------------------------------
DEFECT_SOURCE_DB_TYPE=sqlserver                 # ← 必须切换为 sqlserver
DEFECT_SOURCE_DB_HOST=host.docker.internal      # ← 原 localhost
DEFECT_SOURCE_DB_PORT=14331                      # ← 原 5432，经 WSL socat 转发至 172.22.37.52:1433
DEFECT_SOURCE_DB_NAME=defect_db
DEFECT_SOURCE_DB_USER=sa
DEFECT_SOURCE_DB_PASSWORD=
DEFECT_SOURCE_DB_SCHEMA=dbo
```

### 3.3 Docker Compose 配置

`refresh-scheduler` 服务无需特殊网络配置，只需与 `postgres` 同属 `app-network`。`host.docker.internal` 由 Docker Desktop 自动解析。

### 3.4 验证

```bash
# 1. WSL 中确认两个代理均监听
ss -tlnp | grep -E "14330|14331"

# 2. 容器内测试 Carbody SQL Server 连通性
docker exec refresh-scheduler python -c "
import pytds
conn = pytds.connect(server='host.docker.internal', port=14330,
    database='DXQcontrol_SVWMEB_BI_DWH', user='sa', password='Sa123456!')
print('Carbody OK:', conn)
conn.close()
"

# 3. 容器内测试 Defect SQL Server 连通性
docker exec refresh-scheduler python -c "
import pytds
conn = pytds.connect(server='host.docker.internal', port=14331,
    database='defect_db', user='sa', password='')
print('Defect OK:', conn)
conn.close()
"

# 4. 端到端验证：启动调度器，观察日志中两条链路是否正常从 SQL Server 抽取数据
docker logs -f refresh-scheduler
```

## 4. 已部署代理端口汇总

| 端口 | 用途 | 转发目标 |
|------|------|----------|
| 8082 | WebSocket (data-saver-service) | `172.21.12.73:80` |
| 14330 | Carbody SQL Server (refresh-scheduler) | `172.21.12.97:1433` |
| 14331 | Defect SQL Server (refresh-scheduler) | `172.22.37.52:1433` |

## 5. 注意事项

1. WSL 重启后 socat 代理自动启动（依赖 `wsl.conf` 的 `boot.command`），首次部署需手动执行一次启动脚本
2. 两个代理端口对应不同的 SQL Server 实例，不可混用
3. 容器内的 `host.docker.internal` 在 Docker Desktop 重启后可能短暂不可用，调度器的 `try-except` + 自动重试机制可以覆盖这个场景

---

**关联文档：**
- [Docker Desktop WSL2 后端容器访问外部私有网络问题指南](../Docker%20Desktop%20WSL2%20后端容器访问外部私有网络问题指南.md)
- [分析数仓三链路定时刷新技术方案](./analytics_db_refresh_deployment_plan.md)
