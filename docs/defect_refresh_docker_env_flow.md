# defect-refresh 容器环境变量传递说明

更新时间：2026-04-14 13:57 Asia/Shanghai

主要修改内容：

- 梳理 `.env`、`docker-compose.yml`、容器环境与 `refresh_history_station_defect_summary.py` 之间的变量传递关系
- 明确 `DEFECT_SOURCE_DB_HOST` 在容器中的来源
- 明确 `DEFECT_TARGET_DB_HOST_IN_DOCKER` / `DEFECT_TARGET_DB_PORT_IN_DOCKER` 的作用边界

## 1. 适用范围

本文档仅说明下面这条执行链路的环境变量来源：

- `docker compose --profile manual run --rm defect-refresh --refresh`

对应文件：

- `docker-compose.yml`
- `.env`
- `defect_database/refresh_history_station_defect_summary.py`

## 2. 结论速览

| 变量名 | 容器内最终是否存在 | 默认来源 | 是否被 compose 二次覆盖 | Python 脚本是否直接读取 |
| --- | --- | --- | --- | --- |
| `DEFECT_TARGET_DB_HOST` | 是 | `.env` | 是 | 是 |
| `DEFECT_TARGET_DB_PORT` | 是 | `.env` | 是 | 是 |
| `DEFECT_TARGET_DB_HOST_IN_DOCKER` | 不一定需要进入容器 | `.env` | 否 | 否 |
| `DEFECT_TARGET_DB_PORT_IN_DOCKER` | 不一定需要进入容器 | `.env` | 否 | 否 |
| `DEFECT_SOURCE_DB_HOST` | 是 | `.env` | 否 | 是 |
| `DEFECT_SOURCE_DB_PORT` | 是 | `.env` | 否 | 是 |
| `DEFECT_SOURCE_DB_NAME` | 是 | `.env` | 否 | 是 |
| `DEFECT_SOURCE_DB_USER` | 是 | `.env` | 否 | 是 |
| `DEFECT_SOURCE_DB_PASSWORD` | 是 | `.env` | 否 | 是 |

可以直接记住两句话：

- `DEFECT_SOURCE_DB_*` 在当前项目的 Docker 场景下，默认直接来自 `.env`
- `DEFECT_TARGET_DB_HOST_IN_DOCKER` / `DEFECT_TARGET_DB_PORT_IN_DOCKER` 只是给 `docker-compose.yml` 用的中转变量，脚本真正读取的是 `DEFECT_TARGET_DB_HOST` / `DEFECT_TARGET_DB_PORT`

## 3. 变量传递链路

### 3.1 目标库 target 变量

`.env` 中定义：

```env
DEFECT_TARGET_DB_HOST=localhost
DEFECT_TARGET_DB_PORT=5432
DEFECT_TARGET_DB_HOST_IN_DOCKER=postgres
DEFECT_TARGET_DB_PORT_IN_DOCKER=5432
```

`docker-compose.yml` 中：

```yaml
env_file:
  - .env
environment:
  DEFECT_TARGET_DB_HOST: ${DEFECT_TARGET_DB_HOST_IN_DOCKER:-postgres}
  DEFECT_TARGET_DB_PORT: ${DEFECT_TARGET_DB_PORT_IN_DOCKER:-5432}
```

这表示：

1. compose 会先读取 `.env`
2. `defect-refresh` 容器先拿到 `.env` 里的普通变量
3. 然后 compose 再把容器内的 `DEFECT_TARGET_DB_HOST` / `DEFECT_TARGET_DB_PORT` 覆盖成 `postgres` / `5432`
4. Python 脚本读取的就是覆盖后的 `DEFECT_TARGET_DB_HOST` / `DEFECT_TARGET_DB_PORT`

设计原因：

- 宿主机直接执行脚本时，`localhost` 指向宿主机本机
- 容器内执行脚本时，`localhost` 指向当前容器自己，不能用来访问 compose 里的 PostgreSQL 服务
- 因此容器场景必须改成服务名 `postgres`

### 3.2 源库 source 变量

`docker-compose.yml` 里当前只覆盖了 target 变量，没有覆盖 source 变量。

因此下面这些变量在 `defect-refresh` 容器里，默认沿用 `.env` 中的值：

- `DEFECT_SOURCE_DB_HOST`
- `DEFECT_SOURCE_DB_PORT`
- `DEFECT_SOURCE_DB_NAME`
- `DEFECT_SOURCE_DB_USER`
- `DEFECT_SOURCE_DB_PASSWORD`
- `DEFECT_SOURCE_DB_TYPE`
- `DEFECT_SOURCE_DB_SCHEMA`

所以用户问题“在容器中 `DEFECT_SOURCE_DB_HOST` 这个变量来自于 `.env` 吗”的答案是：

是，当前实现里它默认来自 `.env`。

## 4. Python 脚本实际读取谁

`defect_database/refresh_history_station_defect_summary.py` 读取的是这些变量：

- target：
  - `DEFECT_TARGET_DB_HOST`
  - `DEFECT_TARGET_DB_PORT`
  - `DEFECT_TARGET_DB_NAME`
  - `DEFECT_TARGET_DB_USER`
  - `DEFECT_TARGET_DB_PASSWORD`
- source：
  - `DEFECT_SOURCE_DB_TYPE`
  - `DEFECT_SOURCE_DB_HOST`
  - `DEFECT_SOURCE_DB_PORT`
  - `DEFECT_SOURCE_DB_NAME`
  - `DEFECT_SOURCE_DB_USER`
  - `DEFECT_SOURCE_DB_PASSWORD`
  - `DEFECT_SOURCE_DB_SCHEMA`

脚本不会直接读取：

- `DEFECT_TARGET_DB_HOST_IN_DOCKER`
- `DEFECT_TARGET_DB_PORT_IN_DOCKER`

也就是说，`*_IN_DOCKER` 只负责帮助 compose 生成真正传给脚本的 target 变量。

## 5. 两种运行方式对比

### 5.1 宿主机直接运行脚本

执行示意：

```powershell
python defect_database/refresh_history_station_defect_summary.py --refresh
```

变量结果：

- `DEFECT_TARGET_DB_HOST=localhost`
- `DEFECT_TARGET_DB_PORT=5432`
- `DEFECT_SOURCE_DB_*` 直接取 `.env`

### 5.2 通过 Docker 运行脚本

执行示意：

```powershell
docker compose --profile manual run --rm defect-refresh --refresh
```

变量结果：

- `DEFECT_TARGET_DB_HOST` 被覆盖为 `postgres`
- `DEFECT_TARGET_DB_PORT` 被覆盖为 `5432`
- `DEFECT_SOURCE_DB_*` 继续直接取 `.env`

## 6. 一张图看懂

```text
.env
  |- DEFECT_TARGET_DB_HOST=localhost
  |- DEFECT_TARGET_DB_PORT=5432
  |- DEFECT_TARGET_DB_HOST_IN_DOCKER=postgres
  |- DEFECT_TARGET_DB_PORT_IN_DOCKER=5432
  |- DEFECT_SOURCE_DB_HOST=...
  |- DEFECT_SOURCE_DB_PORT=...
  |- DEFECT_SOURCE_DB_NAME=...
  |- DEFECT_SOURCE_DB_USER=...
  |- DEFECT_SOURCE_DB_PASSWORD=...
  v
docker-compose.yml
  |- env_file: .env
  |- environment:
  |    DEFECT_TARGET_DB_HOST <- DEFECT_TARGET_DB_HOST_IN_DOCKER
  |    DEFECT_TARGET_DB_PORT <- DEFECT_TARGET_DB_PORT_IN_DOCKER
  v
defect-refresh 容器
  |- DEFECT_TARGET_DB_HOST=postgres
  |- DEFECT_TARGET_DB_PORT=5432
  |- DEFECT_SOURCE_DB_* = 继续沿用 .env
  v
refresh_history_station_defect_summary.py
  |- 读取 DEFECT_TARGET_DB_HOST / PORT
  |- 读取 DEFECT_SOURCE_DB_*
```

## 7. 排查建议

如果后续发现容器里源库连不上，优先检查：

1. `.env` 中的 `DEFECT_SOURCE_DB_HOST` 是否对 Docker 容器可达
2. `DEFECT_SOURCE_DB_PORT`、`DEFECT_SOURCE_DB_NAME`、`DEFECT_SOURCE_DB_USER`、`DEFECT_SOURCE_DB_PASSWORD` 是否完整
3. 如果源库不是 PostgreSQL，`DEFECT_SOURCE_DB_TYPE` 是否设置正确
4. 不要把 `DEFECT_TARGET_DB_HOST_IN_DOCKER` 误认为脚本直接读取的变量
