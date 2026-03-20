# WebSocket 数据格式说明

本文档记录了面漆雪橇返回线监控系统（skid_count_websocket）中 WebSocket 通信的订阅及返回数据格式。

## 1. 订阅数据格式（Client -> Server）

客户端在建立 WebSocket 连接后，会向服务端发送点位数据的订阅请求。

### JSON 结构示例

```json
{
  "id": "",
  "type": "advise",
  "plc": "L3FUB2",
  "tag": ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"
}
```

### 字段说明

| 字段名 | 类型   | 默认值   | 说明 |
| :--- | :--- | :--- | :--- |
| `id`   | String | `""` | 订阅唯一标识，通常可留空 |
| `type` | String | `"advise"` | 消息类型，表示订阅请求 |
| `plc`  | String | 无   | PLC 设备名称（如 "L3FUB2"） |
| `tag`  | String | 无   | 具体的点位标签路径，需与服务器点位对应 |


## 2. 返回数据格式（Server -> Client）

服务端在点位数据发生变化时，会向已订阅的客户端推送数据更新。

### JSON 结构示例

```json
{
  "type": "dataChange",
  "id": "",
  "tag": "L3FUB2.L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID",
  "ts": "2025-09-05T14:27:34.781+08:00",
  "value": "782025836495102N54Y2T2TMQB000-",
  "quality": 192,
  "source": "CNSVWSFVM131",
  "userRights": 0
}
```

### 字段说明

| 字段名 | 类型   | 说明 |
| :--- | :--- | :--- |
| `type` | String | 消息类型，通常点位数据变化时为 `"dataChange"` |
| `id`   | String | 对应订阅请求时的 id 标识 |
| `tag`  | String | 服务器完整点位标签，格式为 `[PLC名称].[标签路径]`，前端客户端会将其拆分比对本地配置 |
| `ts`   | String | 服务器时间戳，遵循 ISO 8601 标准并包含时区信息（如 `...T14:27:34.781+08:00`） |
| `value`| String/Number| 实际的数据值，如雪橇号信息、状态信息等 |
| `quality`| Number | 数据质量代码（如 `192` 通常代表 Good/数据正常） |
| `source` | String | 数据源标识（如具体的服务器节点名称 `"CNSVWSFVM131"`） |
| `userRights`| Number| 用户权限标识码 |


## 3. 心跳保活格式（Client -> Server）

前端客户端为保持 WebSocket 长连接在线不断开，会定时（默认每隔 2 秒）发送心跳数据。

### JSON 结构示例

```json
{
  "type": "info",
  "info": "alive"
}
```

### 字段说明

| 字段名 | 类型   | 说明 |
| :--- | :--- | :--- |
| `type` | String | 固定为 `"info"`，表示这仅是一条信息通知 |
| `info` | String | 固定为 `"alive"`，表明当前客户端系统仍处于活跃状态 |
