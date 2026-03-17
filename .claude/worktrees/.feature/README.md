# WebSocket工业数据采集演示系统

**修改时间：2025年9月1日14点05分**  
**修改内容：更新项目结构说明 - 服务端代码移动到service目录**
**运行环境：conda activate websoket**

## 项目简介

这是一个完整的WebSocket工业数据采集演示系统，包含Vue 3前端界面和Python WebSocket服务器端，用于实时监控和显示工业设备数据。

## 功能特性

### 🔌 WebSocket连接管理

- 支持自定义WebSocket服务器地址
- 实时连接状态显示
- 自动心跳保活机制（每2秒发送一次心跳）
- 连接时长统计

### 📊 数据监控展示

- 实时数据表格展示（100个工业设备点位）
- 支持显示设备点位标签、数据值、消息类型等
- 数据更新次数统计
- 支持数据清空和刷新功能

### 🏭 工业设备支持

- 预配置L3FUB2和L3FKT1系列PLC设备
- 支持多种传感器数据类型（温度、液位、车身ID等）
- 可扩展的设备参数配置

### 🎨 现代化界面

- 响应式设计，支持桌面和移动端
- 美观的渐变色主题
- 实时状态指示器
- 加载动画和用户反馈

### 🔧 服务器端功能

- Python WebSocket服务器
- 动态数据模拟（2-5秒推送间隔）
- 多客户端支持
- 可配置参数

## 技术栈

### 前端

- **前端框架**: Vue 3.4+ (Composition API)
- **UI组件库**: Element Plus 2.4+
- **构建工具**: Vite 5.0+
- **WebSocket**: 原生WebSocket API
- **图标库**: @element-plus/icons-vue

### 后端

- **服务器**: Python 3.7+
- **WebSocket库**: websockets 12.0
- **异步处理**: asyncio
- **数据模拟**: 动态生成工业数据

## 项目结构

```
websocket-project/
├── service/              # 🔥 服务端文件夹（新结构）
│   ├── websocket_server.py   # 主服务器程序
│   ├── server_config.py      # 服务器配置文件
│   ├── start_server.py       # 配置化启动脚本
│   ├── requirements.txt      # Python依赖
│   ├── start_server.bat      # Windows启动脚本
│   ├── README.md            # 服务端说明
│   └── 测试指南.md           # 集成测试指南
├── src/                  # 前端文件夹
│   ├── App.vue           # 主应用组件
│   ├── main.js           # 应用入口
│   ├── style.css         # 全局样式
│   └── config/           # 配置文件
│       └── deviceConfig.json  # 设备配置
├── start_server.bat      # 根目录启动脚本（自动进入service目录）
├── package.json         # 前端项目配置
├── vite.config.js       # Vite配置
└── README.md           # 项目说明（本文件）
```

## 快速开始

### 环境要求

**前端**:

- Node.js 16+
- npm 或 yarn

**后端**:

- Python 3.7+
- pip

### 1. 启动WebSocket服务器

**🎯 方式一：Windows一键启动（推荐）**

```cmd
# 在项目根目录运行
start_server.bat
```

**方式二：手动启动**

```bash
# 进入服务端目录
cd service

# 安装Python依赖
pip install -r requirements.txt

# 启动服务器
python websocket_server.py
```

### 2. 启动前端应用

```bash
# 在项目根目录

# 安装前端依赖
npm install

# 启动开发模式
npm run dev
```

### 3. 访问应用

- **前端地址**: `http://localhost:5173`
- **WebSocket服务器**: `ws://localhost:8088/ws/emosweb`

## 使用指南

### WebSocket连接

1. **启动服务器**: 确保WebSocket服务器在service目录中正常运行
2. **打开前端**: 浏览器访问前端应用
3. **连接服务器**: 点击"连接服务器"按钮
4. **监控数据**: 观察表格中的实时数据更新

### 配置修改

**服务器配置** (`service/server_config.py`)：

```python
SERVER_CONFIG = {
    "port": 8088,           # 修改端口
    "push_interval_min": 2, # 最小推送间隔
    "push_interval_max": 5, # 最大推送间隔
}
```

**设备配置** (`src/config/deviceConfig.json`)：

```json
{
  "config": {
    "L3FUB2": [...],
    "L3FKT1": [...]
  }
}
```

## 目录说明

### 🆕 service/ 目录（服务端）

所有服务器端相关文件都统一放在 `service/` 目录中：

- 便于独立部署
- 配置文件集中管理
- 依赖关系清晰
- 维护更方便

### 主要文件说明

- `service/websocket_server.py` - 主服务器程序（推荐直接运行）
- `service/start_server.py` - 支持配置文件的启动脚本
- `service/server_config.py` - 可修改的配置文件
- `service/README.md` - 详细的服务端使用说明
- `service/测试指南.md` - 完整的测试步骤

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

## 开发指南

### 前端开发

```bash
npm run dev     # 开发模式
npm run build   # 构建生产版本
npm run preview # 预览构建结果
```

### 服务端开发

```bash
cd service
python websocket_server.py  # 启动服务器
```

### 添加新设备

1. 编辑 `src/config/deviceConfig.json` 添加前端配置
2. 编辑 `service/server_config.py` 添加服务端配置
3. 重启服务器和前端

## 测试验证

详细测试步骤请参考：**`service/测试指南.md`**

**基本验证**：

1. ✅ 服务器启动成功（service目录）
2. ✅ 前端连接成功
3. ✅ 数据实时更新
4. ✅ 心跳正常工作

## 故障排除

### 连接问题

1. 确认WebSocket服务器在 `service/` 目录中启动
2. 检查端口8088是否被占用
3. 验证防火墙设置

### 路径问题

- **服务器启动**: 必须在 `service/` 目录中执行
- **前端启动**: 必须在项目根目录执行
- **配置修改**: 编辑 `service/server_config.py`

### Python环境

```bash
# 检查Python版本
python --version

# 安装依赖
cd service
pip install -r requirements.txt
```

## 部署说明

### 开发环境

- 前端: `npm run dev` (项目根目录)
- 后端: `python websocket_server.py` (service目录)

### 生产环境

- **前端**: `npm run build` 然后部署dist目录
- **后端**: service目录可独立部署到任何服务器

## 更新说明

**v2.0 (2025-09-01)**

- ✨ 服务端代码移动到 `service/` 目录
- 🔧 配置文件独立管理
- 📚 文档结构优化
- 🚀 一键启动脚本

## 许可证

本项目仅用于演示和学习目的。
