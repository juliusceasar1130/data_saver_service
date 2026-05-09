好的，以下是完整的技术指南，可直接保存复用。

---

# Docker Desktop WSL2 后端容器访问外部私有网络问题指南

---

## 一、问题背景

### 1.1 环境信息

| 组件           | 版本/配置                            |
| -------------- | ------------------------------------ |
| Windows        | Windows 11 (10.0.22631.6199)         |
| WSL            | 2.6.3.0                              |
| WSL 内核       | 6.6.87.2-1                           |
| Docker Desktop | 4.43.2                               |
| WSL 网络模式   | `networkingMode=mirrored`            |
| 容器服务       | Python WebSocket 客户端 + PostgreSQL |

### 1.2 网络拓扑

```
┌─────────────────────────────────────────────────────────┐
│                    外部网络 172.21.0.0/16                  │
│              172.21.12.73 (EMOS WebSocket 服务器)          │
│                    ▲                                   │
│                    │                                   │
│    ┌───────────────┼───────────────┐                   │
│    │   Windows 宿主机              │                    │
│    │   (能访问 172.21.12.73)      │                    │
│    │       ▲                      │                    │
│    │       │ WSL2 虚拟网络         │                    │
│    │   ┌───┴──────────────────┐   │                    │
│    │   │  WSL 默认发行版      │   │                    │
│    │   │  172.20.10.4/28      │   │                    │
│    │   │  ✅ 能访问目标        │   │                    │
│    │   │       ▲              │   │                    │
│    │   │       │ Docker 隔离   │   │                    │
│    │   │   ┌───┴──────────┐   │   │                    │
│    │   │   │ Docker 容器   │   │   │                    │
│    │   │   │ 172.24.0.2/16│   │   │                    │
│    │   │   │ ❌ 无法访问     │   │   │                    │
│    │   │   └──────────────┘   │   │                    │
│    │   └──────────────────────┘   │                    │
│    └───────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 1.3 现象

- **WSL 能访问** `172.21.12.73`（ping、curl、WebSocket 均正常）
- **Windows 宿主机能访问** `172.21.12.73`
- **Docker 容器内无法访问** `172.21.12.73`（ping 100% 丢包，curl 超时）
- 容器内 `host.docker.internal` 访问正常（说明容器出网能力本身没问题）

---

## 二、原因分析

### 2.1 根本原因

**Docker Desktop WSL2 后端的容器网络与 WSL 物理网络存在路由隔离缺陷。**

Docker 容器运行在独立的 `docker-desktop` WSL2 发行版中，其网络路径为：

```
容器 (172.24.0.2)
    ↓
Docker bridge (172.24.0.1)
    ↓
docker-desktop VM (WSL2 发行版)
    ↓
vEthernet (WSL) 虚拟网卡
    ↓
Windows 宿主机网络
```

**问题点：** `docker-desktop` VM 到 Windows 宿主机的虚拟交换机层，对某些 RFC1918 私有网段（如 `172.21.0.0/16`）的路由转发存在缺陷，导致容器流量被丢弃。

### 2.2 排除过的可能性

| 可能性          | 验证结果                                   | 结论             |
| --------------- | ------------------------------------------ | ---------------- |
| 网段冲突        | 容器 `172.24.0.0/16`，目标 `172.21.0.0/16` | ❌ 不冲突        |
| Windows 防火墙  | 关闭防火墙后仍不通                         | ❌ 不是防火墙    |
| Docker iptables | 检查无异常规则                             | ❌ 不是 iptables |
| DNS 解析        | 目标 IP 直接访问也失败                     | ❌ 不是 DNS      |
| 目标服务器限制  | WSL 和 Windows 都能访问                    | ❌ 不是目标限制  |

### 2.3 关键发现

- `host.docker.internal` 在容器内正常 → Docker 网络栈本身工作
- `emos-proxy` 容器（alpine/socat）也无法访问目标 → **问题在 Docker 网络层，非应用层**
- WSL `networkingMode=mirrored` 只影响 WSL 默认发行版，不影响 `docker-desktop` VM

---

## 三、解决方案

### 3.1 方案对比

| 方案               | 原理                                                 | 可行性                          | 推荐度     |
| ------------------ | ---------------------------------------------------- | ------------------------------- | ---------- |
| Docker 容器代理    | 容器内跑 socat 转发                                  | ❌ 代理本身也访问不了目标       | ⭐         |
| `--network host`   | 容器共享宿主机网络                                   | ⚠️ Docker Desktop WSL2 支持有限 | ⭐⭐       |
| WSL socat 代理     | WSL 中跑 socat，容器通过 `host.docker.internal` 访问 | ✅ 稳定可靠                     | ⭐⭐⭐⭐⭐ |
| Windows 宿主机代理 | Windows 中跑 nginx/socat                             | ✅ 可行但复杂                   | ⭐⭐⭐     |

### 3.2 选定方案：WSL socat 代理

**核心思路：** 利用 WSL 能访问目标的网络能力，在 WSL 中运行代理，Docker 容器通过 `host.docker.internal` 连接到 WSL 代理，再由代理转发到目标服务器。

```
Docker 容器 (data-saver-service)
    ↓
ws://host.docker.internal:8082/ws/emosweb
    ↓
Docker DNS 解析 host.docker.internal → 192.168.65.254 (Windows 宿主机)
    ↓
Windows 宿主机 192.168.65.254:8082
    ↓
WSL 中 socat 监听 0.0.0.0:8082
    ↓
socat 转发到 172.21.12.73:80 (走 WSL 网络，能通！)
    ↓
目标服务器 172.21.12.73 ✅
```

---

## 四、实施步骤

### 4.1 WSL 中配置 socat 代理

#### 步骤 1：安装 socat

```bash
sudo apt update
sudo apt install -y socat
```

#### 步骤 2：创建启动脚本

```bash
mkdir -p /home/julius/wsl-scripts

cat << 'EOF' > /home/julius/wsl-scripts/start-socat-proxy.sh
#!/bin/bash

# 清理可能残留的旧进程
pkill -f "socat TCP-LISTEN:8082" 2>/dev/null || true
sleep 1

# 启动 socat 代理
# bind=0.0.0.0 确保 Windows 宿主机和 Docker 容器都能访问
nohup /usr/bin/socat TCP-LISTEN:8082,fork,keepalive,bind=0.0.0.0 TCP:172.21.12.73:80 >> /tmp/socat-proxy.log 2>&1 &

echo "$(date '+%Y-%m-%d %H:%M:%S'): Socat proxy started on 0.0.0.0:8082 -> 172.21.12.73:80" >> /tmp/socat-proxy.log
EOF

chmod +x /home/julius/wsl-scripts/start-socat-proxy.sh
```

#### 步骤 3：配置 WSL 开机启动

```bash
sudo tee /etc/wsl.conf << 'EOF'
[boot]
systemd=true
command = /bin/sh -c 'sleep 10 && /home/julius/wsl-scripts/start-socat-proxy.sh'
EOF
```

> **说明：** `sleep 10` 确保 WSL 网络完全就绪后再启动代理。

#### 步骤 4：重启 WSL 验证

```powershell
# Windows PowerShell
wsl --shutdown
# 等待 10 秒后重新打开 WSL
```

---

### 4.2 修改 docker-compose.yml

```yaml
services:
  # PostgreSQL 数据库服务
  postgres:
    image: postgres:17-alpine
    container_name: 120JPH_postgres
    restart: unless-stopped
    networks:
      - app-network
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-root}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-root}
      POSTGRES_DB: ${POSTGRES_DB:-rollerbed_tracking_db}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./create_tables_postgresql.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U ${POSTGRES_USER:-root} -d ${POSTGRES_DB:-rollerbed_tracking_db}",
        ]
      interval: 10s
      timeout: 5s
      retries: 5

  # Python 采集 WebSocket 数据保存到 PostgreSQL 服务
  data-saver-service:
    build: .
    image: data-saver-service:v3.1
    container_name: data_saver_service_v3.1
    restart: unless-stopped
    init: true
    networks:
      - app-network
    depends_on:
      postgres:
        condition: service_healthy

    environment:
      # 数据库配置
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${POSTGRES_USER:-root}
      - DB_PASSWORD=${POSTGRES_PASSWORD:-root}
      - DB_NAME=${POSTGRES_DB:-rollerbed_tracking_db}

      # WebSocket 配置：通过 WSL 代理访问外部服务器
      - WS_SERVER_HOST=${WS_SERVER_HOST:-host.docker.internal}
      - WS_SERVER_PORT=${WS_SERVER_PORT:-8082}
      - WS_SERVER_PATH=${WS_SERVER_PATH:-/ws/emosweb}
      - WS_USE_PORT_IN_URL=${WS_USE_PORT_IN_URL:-true}

      - LOG_LEVEL=INFO
      - DEVICE_CONFIG_PATH=/app/deviceConfig.json

    volumes:
      - ./deviceConfig.json:/app/deviceConfig.json:ro

volumes:
  pgdata:
    driver: local

networks:
  app-network:
    driver: bridge
```

**关键变更：**

- 删除 `emos-proxy` Docker 服务
- `WS_SERVER_HOST` 改为 `host.docker.internal`（指向 WSL 代理）
- `WS_SERVER_PORT` 改为 `8082`（与 WSL socat 监听端口一致）
- 移除对 `emos-proxy` 的 `depends_on`

---

### 4.3 启动服务

```bash
# 进入项目目录
cd /path/to/your/project

# 重新启动
docker-compose down
docker-compose up -d

# 查看日志
docker-compose logs -f data-saver-service
```

---

## 五、测试验证

### 5.1 WSL 层验证

```bash
# 检查 socat 进程
ps aux | grep socat

# 检查端口监听
ss -tlnp | grep 8082
# 预期输出：0.0.0.0:8082

# WSL 本地测试
curl -I http://localhost:8082

# 查看代理日志
tail -f /tmp/socat-proxy.log
```

### 5.2 Windows 层验证

```powershell
# Windows PowerShell
curl -I http://localhost:8082
```

### 5.3 Docker 容器层验证

```bash
# 容器内测试代理连通性
docker exec data_saver_service_v3.1 curl -I http://host.docker.internal:8082

# 查看数据服务日志
docker-compose logs -f data-saver-service
```

### 5.4 端到端验证

观察 `data-saver-service` 日志，确认：

- WebSocket 连接成功
- 数据正常接收并写入 PostgreSQL

---

## 六、维护与故障排查

### 6.1 日常维护

| 操作         | 命令                                 |
| ------------ | ------------------------------------ |
| 查看代理状态 | `ps aux \| grep socat`               |
| 查看代理日志 | `tail -f /tmp/socat-proxy.log`       |
| 重启代理     | `~/wsl-scripts/start-socat-proxy.sh` |
| 查看端口占用 | `ss -tlnp \| grep 8082`              |

### 6.2 目标 IP 变更

修改 `/home/julius/wsl-scripts/start-socat-proxy.sh` 中的 IP 地址，然后重启 WSL：

```bash
wsl --shutdown
# 重新打开 WSL
```

### 6.3 常见问题

| 现象                               | 原因                | 解决                               |
| ---------------------------------- | ------------------- | ---------------------------------- |
| WSL 重启后代理未启动               | `wsl.conf` 未生效   | 确认 `wsl --shutdown` 后重新打开   |
| 端口 8082 被占用                   | 旧进程残留          | `pkill -f "socat TCP-LISTEN:8082"` |
| 容器内 `host.docker.internal` 不通 | Docker Desktop 问题 | 重启 Docker Desktop                |
| 代理日志显示 `Operation timed out` | 目标服务器不可达    | 检查目标服务器状态                 |

### 6.4 注意事项

1. **WSL 重启后需等待 10 秒**，让 `boot.command` 完成启动
2. **不要同时使用 Docker 容器代理和 WSL 代理**，避免端口冲突
3. **如需多个外部服务**，可在 WSL 中启动多个 socat 实例（不同端口）
4. **生产环境建议**使用 systemd 或 supervisor 管理 socat，WSL 环境建议用 `boot.command`

---

## 七、方案总结

| 项目             | 说明                                                   |
| ---------------- | ------------------------------------------------------ |
| **问题本质**     | Docker Desktop WSL2 后端容器网络对特定私有网段路由缺陷 |
| **解决核心**     | 利用 WSL 网络能力，通过代理桥接容器与外部网络          |
| **代理位置**     | WSL 中（能访问目标的网络环境）                         |
| **容器访问方式** | `host.docker.internal:端口`                            |
| **持久化机制**   | WSL `boot.command`                                     |
| **维护成本**     | 低（单脚本、单配置、自动恢复）                         |

---

## 八、附录：systemd 方案（备用）

如果 WSL 环境支持稳定的 systemd，可使用以下配置：

```bash
sudo tee /etc/systemd/system/socat-proxy.service << 'EOF'
[Unit]
Description=Socat Proxy to EMOS WebSocket Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP-LISTEN:8082,fork,keepalive,bind=0.0.0.0 TCP:172.21.12.73:80
Restart=always
RestartSec=30
StandardOutput=append:/tmp/socat-proxy.log
StandardError=append:/tmp/socat-proxy.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable socat-proxy
sudo systemctl start socat-proxy
```

> **注意：** 部分 WSL 环境下 systemd 服务启动可能不稳定，如遇问题请回退到 `boot.command` 方案。

---

**文档版本：** v1.0  
**适用场景：** Docker Desktop WSL2 后端容器访问外部 RFC1918 私有网络  
**最后更新：** 2026-05-09
