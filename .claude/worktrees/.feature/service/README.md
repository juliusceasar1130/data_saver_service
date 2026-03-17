# WebSocket服务器使用说明

**修改时间：2025年1月19日**
**修改内容：新增websocket_server_v2.py服务器程序说明**

## 概述

这是一个简洁的Python WebSocket服务器，专为工业数据采集系统设计，用于推送模拟数据到浏览器端。

## 文件结构

```
service/                    # 服务端目录
├── websocket_server.py     # 独立服务器程序（推荐使用）
├── websocket_server_v2.py  # V2版本服务器（30字符固定格式数据）
├── start_server.py         # 配置化启动脚本
├── server_config.py        # 配置文件
├── requirements.txt        # Python依赖包
├── start_server.bat        # Windows启动脚本
├── README.md              # 使用说明（本文件）
└── 测试指南.md             # 集成测试指南
```

## 快速开始

### 1. 安装依赖

```bash
cd service
pip install -r requirements.txt
```

### 2. 启动服务器

**方式一：直接运行（推荐）**
```bash
cd service
python websocket_server.py
```

**方式二：使用配置文件**
```bash
cd service
python start_server.py
```

**方式三：Windows批处理**
```cmd
cd service
start_server.bat
```

### 3. 服务器信息

- **监听地址**: `0.0.0.0:8088`
- **WebSocket路径**: `/ws/emosweb`
- **完整连接地址**: `ws://localhost:8088/ws/emosweb`

## 服务器程序选择

本项目提供两个WebSocket服务器程序，根据使用场景选择：

### websocket_server.py vs start_server.py

| 特性 | websocket_server.py | start_server.py |
|------|-------------------|-----------------|
| **设计理念** | 独立完整程序 | 配置化启动脚本 |
| **配置方式** | 硬编码在文件中 | 外部配置文件 |
| **依赖关系** | 无外部依赖 | 依赖server_config.py |
| **灵活性** | 低（需修改代码） | 高（修改配置文件） |
| **推荐场景** | 快速测试、学习演示 | 生产环境、长期维护 |

### 详细对比

#### **配置管理方式**

**websocket_server.py**（硬编码配置）:
```python
# 配置直接写在代码中
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8088
WEBSOCKET_PATH = "/ws/emosweb"
DATA_PUSH_MIN_INTERVAL = 2
DATA_PUSH_MAX_INTERVAL = 5
```

**start_server.py**（外部配置文件）:
```python
# 从配置文件导入
from server_config import get_config, get_device_config
config = get_config()
device_config = get_device_config()
```

#### **使用场景建议**

**选择 websocket_server.py：**
- ✅ **快速测试** - 无需配置，开箱即用
- ✅ **学习演示** - 代码简单易懂
- ✅ **临时使用** - 快速启动验证功能
- ✅ **单机开发** - 配置需求简单

**选择 start_server.py：**
- ✅ **生产环境** - 需要灵活配置
- ✅ **多环境部署** - 不同环境不同配置
- ✅ **长期维护** - 配置与代码分离
- ✅ **团队协作** - 配置文件可版本控制

#### **配置修改对比**

**修改端口为8089的示例：**

*websocket_server.py*:
```python
# 需要编辑代码第23行
SERVER_PORT = 8089  # 从8088改为8089
```

*start_server.py + server_config.py*:
```python
# 只需编辑server_config.py
SERVER_CONFIG = {
    "port": 8089,  # 从8088改为8089
    # 其他配置保持不变
}
```

### 推荐使用策略

1. **开发测试阶段**：使用 `websocket_server.py`
   - 快速启动，无需配置
   - 代码逻辑清晰易懂

2. **生产部署阶段**：使用 `start_server.py`
   - 配置灵活，便于维护
   - 支持多环境部署

### websocket_server_v2.py - 30字符固定格式版本

**新增时间：2025年1月19日**

websocket_server_v2.py 是 websocket_server.py 的V2版本，主要区别在于模拟数据的格式：

| 特性 | websocket_server.py | websocket_server_v2.py |
|------|-------------------|----------------------|
| **数据格式** | 原始格式（数字、浮点数、字符串混合） | 30字符固定格式 |
| **value示例** | "1234", "25.5", "782025..." | "78202612345678VS212T2TMLB11-" |
| **使用场景** | 通用模拟数据 | 特定格式要求的场景 |

**V2版本数据格式（30字符）**：
```
位置        内容
0-5         "782026" (固定)
6-13        8位随机数字
14-18       "2N211" 或 "VS21J"
19-22       "2LA1" 或 "2T2T"
23-25       "MLB" 或 "MQB"
26          "0" 或 "1"
27          "0", "1" 或 "2"
28          "1" (固定)
29          "-" (固定)
```

**启动方式**：
```bash
cd service
python websocket_server_v2.py
```

## 配置修改

### 修改端口（server_config.py）

```python
SERVER_CONFIG = {
    "port": 8089,  # 修改为新端口
    # 其他配置...
}
```

### 修改数据推送频率

```python
SERVER_CONFIG = {
    "push_interval_min": 1,  # 最小间隔1秒
    "push_interval_max": 3,  # 最大间隔3秒
    # 其他配置...
}
```

## 前端连接配置

修改前端 `src/App.vue` 中的连接地址：

```javascript
// 原地址（第228行）
const wsUrl = ref('localhost:8088/ws/emosweb')

// 如果修改了端口，需要相应更新
const wsUrl = ref('localhost:8089/ws/emosweb')
```

## 功能特性

- ✅ WebSocket连接管理
- ✅ 设备订阅处理
- ✅ 动态数据模拟（2-5秒间隔）
- ✅ 心跳保活机制
- ✅ 多客户端支持
- ✅ 自动清理断开连接
- ✅ 可配置参数

## 数据格式

### 客户端订阅消息
```json
{
  "id": "",
  "type": "advise",
  "plc": "L3FUB2",
  "tag": ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"
}
```

### 服务器推送数据
```json
{
  "type": "dataChange",
  "id": "",
  "tag": "L3FUB2.L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID",
  "ts": "2025-09-01T14:05:30.123+08:00",
  "value": "782025836495102N54Y2T2TMQB000-",
  "quality": 192,
  "source": "PythonSimulator",
  "userRights": 0
}
```

### 心跳消息
```json
{
  "type": "info",
  "info": "alive"
}
```

## 监控信息

服务器运行时会显示：
- 客户端连接/断开状态
- 设备订阅信息
- 数据推送日志
- 心跳接收状态

## 故障排除

### 1. WebSocket路径参数错误
**错误信息**: `BaseEventLoop.create_server() got an unexpected keyword argument 'path'`

**原因**: 较新版本的websockets库不支持在`serve()`函数中直接使用`path`参数

**解决方案**: 已在代码中修复，路径检查移至`handle_websocket`函数内部
```python
# 修复前（错误）
async with websockets.serve(handle_websocket, host, port, path="/ws/emosweb"):

# 修复后（正确）
async with websockets.serve(handle_websocket, host, port):
    # 路径检查在handle_websocket函数中进行
```

### 2. 端口占用
```bash
# 检查端口占用
netstat -an | findstr 8088

# 修改配置中的端口号
```

### 3. 依赖安装失败
```bash
# 升级pip
python -m pip install --upgrade pip

# 重新安装依赖
pip install websockets==12.0
```

### 4. 前端连接失败
- 检查服务器是否启动
- 确认IP地址和端口正确
- 检查防火墙设置
- 验证WebSocket路径: `/ws/emosweb`

## 扩展功能

如需添加更多功能，可以修改配置文件：

```python
# 添加新的设备类型
DEVICE_CONFIG["新设备"] = [
    ".新设备_标签1",
    ".新设备_标签2"
]

# 修改模拟数据生成规则
# 在 generate_mock_data 函数中添加新的数据类型判断
```

## 目录结构说明

- **独立部署**: service目录可以独立部署到任何服务器
- **配置分离**: 所有配置集中在server_config.py文件
- **依赖管理**: requirements.txt包含所有必需的Python包
- **文档完整**: 包含详细的使用说明和测试指南

## 技术说明

- **WebSocket库**: websockets 12.0
- **异步处理**: asyncio
- **Python版本**: 3.7+
- **并发支持**: 多客户端异步处理
- **内存使用**: 轻量级，无持久化存储
