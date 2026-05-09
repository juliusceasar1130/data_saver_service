# Docker PostgreSQL 与 Windows PostgreSQL 端口冲突排故记录

更新时间：2026-04-16 Asia/Shanghai

简要概括：

- 说明为什么 `120JPH_postgres` 启动后，宿主机上会出现“`postgres/root` 能连、`root/root` 不符合预期”的现象
- 记录本次排故结论、验证结果与后续推荐方案

## 1. 问题现象

- `docker-compose.yml` 中的 `postgres` 服务容器名为 `120JPH_postgres`
- 配置里希望使用：
  - 用户：`root`
  - 密码：`root`
- 实际在宿主机上连接 `localhost:5432` 时：
  - 使用 `postgres/root` 可以连接
  - 使用 `root/root` 行为不符合预期

## 2. 核心结论

- 当前机器上同时存在两套 PostgreSQL：
  - Docker 容器内的 `120JPH_postgres`
  - Windows 本机安装的 PostgreSQL 17 服务
- 真正占用宿主机 `5432` 的是 Windows 本机 PostgreSQL 服务，不是 Docker 容器
- 因此宿主机访问 `localhost:5432` 时，默认连到的是 Windows PostgreSQL，而不是 `120JPH_postgres`
- `120JPH_postgres` 容器内部实际存在的管理员角色是 `root`，并不存在 `postgres`

## 3. 关键验证结果

### 3.1 Compose 配置解析结果

`docker compose config` 解析出的 PostgreSQL 环境变量为：

```yaml
POSTGRES_USER: root
POSTGRES_PASSWORD: root
POSTGRES_DB: rollerbed_tracking_db
```

对应 `docker-compose.yml` 中的关键配置：

```yaml
environment:
  POSTGRES_USER: ${POSTGRES_USER:-root}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-root}
  POSTGRES_DB: ${POSTGRES_DB:-rollerbed_tracking_db}
ports:
  - "${POSTGRES_PORT:-5432}:5432"
```

### 3.2 Docker 容器内部角色

在 `120JPH_postgres` 容器内查询到的角色为：

- `root`
- `agent_ro`

并且尝试使用 `postgres` 角色连接时，返回：

```text
FATAL:  role "postgres" does not exist
```

这说明当前 Docker 容器里的真实管理员用户是 `root`。

### 3.3 Docker 容器内部数据库

在 `120JPH_postgres` 容器内查询到的数据库包括：

- `agent_memory`
- `analytics_db`
- `defect_db`
- `postgres`
- `rollerbed_tracking_db`

说明当前项目使用的业务数据库实际已经存在于 Docker 容器中。

### 3.4 Windows 本机 PostgreSQL 状态

Windows 上存在并运行以下服务：

```text
postgresql-x64-17
```

并且本机 `5432` 端口已被该服务监听：

```text
0.0.0.0:5432 LISTENING
[::]:5432    LISTENING
```

这说明 Docker 容器无法再把宿主机 `5432` 成功绑定出来。

### 3.5 Windows 本机 PostgreSQL 中的数据库

使用 `postgres/root` 连接宿主机 `localhost:5432` 后，查询到的数据库只有：

- `postgres`
- `template0`
- `template1`

并不存在 `analytics_db`。

这进一步说明宿主机当前连到的是 Windows 本机 PostgreSQL，而不是 Docker 容器中的 PostgreSQL。

## 4. 为什么会出现“用户不一致”

原因不是 Docker 容器把用户改掉了，而是“连接目标弄错了”：

- Docker 容器里的目标用户是 `root`
- Windows 本机 PostgreSQL 的常见默认用户是 `postgres`
- 宿主机连 `localhost:5432` 时，实际命中了 Windows PostgreSQL

所以会出现：

- `postgres/root` 能连上
- 误以为这是 Docker 容器

但实际并不是同一个数据库实例。

## 5. 与旧数据卷相关的补充说明

容器日志中出现过如下提示：

```text
Database directory appears to contain a database; Skipping initialization
```

这表示 PostgreSQL 数据卷已经存在历史数据。

需要注意：

- `POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB` 这类变量只在首次初始化数据目录时生效
- 后续即使修改 `docker-compose.yml`，也不会自动重建角色和数据库

因此若需要完全按新参数重新初始化，必须删除旧数据卷后再启动容器。

## 6. 推荐处理方案

### 方案 A：保留 Windows PostgreSQL，Docker 改宿主机端口

适合场景：

- 仍需要 Windows 本机 PostgreSQL 服务

做法：

- 将 `docker-compose.yml` 中 PostgreSQL 的端口映射改为例如 `5433:5432`
- 宿主机改连 `localhost:5433`

优点：

- 风险小
- 不影响 Windows 本机 PostgreSQL

缺点：

- 以后需要明确区分：
  - `5432` 是 Windows PostgreSQL
  - `5433` 是 Docker PostgreSQL

### 方案 B：停用 Windows PostgreSQL，让 Docker 占用 5432

适合场景：

- 项目数据库主要都已经迁移到 Docker 容器中

做法：

- 停止并禁用 Windows 服务 `postgresql-x64-17`
- 重新创建 Docker PostgreSQL 容器
- 验证容器端口成功发布到宿主机 `5432`

优点：

- 宿主机访问路径最简单
- `localhost:5432` 直接就是 Docker 数据库

风险：

- 若本机还有其他工具或任务依赖 Windows PostgreSQL，会受影响

## 7. 关于 `psql.exe` 的建议

当前项目中的计划任务脚本 `defect_database/scripts/refresh_analytics_db.ps1` 只是调用 `psql.exe` 执行 SQL，不要求必须安装 Windows PostgreSQL Server。

因此后续更推荐：

- 数据库服务放在 Docker 中
- Windows 宿主机只保留 PostgreSQL 客户端工具，例如 `psql.exe`

这样可以避免：

- 本机 PostgreSQL 服务长期占用 `5432`
- 容易把宿主机实例与 Docker 实例混淆

## 8. 当前建议

如果当前目标是让项目环境更清晰、冲突更少，推荐优先采用：

- 停用 Windows PostgreSQL 服务
- 保留 `psql.exe` 客户端
- 让 Docker PostgreSQL 独占宿主机 `5432`

如果暂时不方便调整本机服务，则采用：

- Docker PostgreSQL 改映射到 `5433`
- 脚本和连接配置明确区分端口
