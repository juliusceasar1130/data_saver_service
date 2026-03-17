# WebSocket工业数据采集演示系统 - 项目上下文

## 项目概述

这是一个完整的WebSocket工业数据采集演示系统，包含Vue 3前端界面和Python WebSocket服务器端，用于实时监控和显示工业设备数据。项目采用现代化的前后端分离架构，实现了设备数据的实时推送和可视化展示。

## 技术栈

### 前端
- **框架**: Vue 3.4+ (Composition API)
- **UI组件库**: Element Plus 2.4+
- **构建工具**: Vite 5.0+
- **WebSocket**: 原生WebSocket API
- **图标库**: @element-plus/icons-vue

### 后端
- **语言**: Python 3.7+
- **WebSocket库**: websockets 12.0
- **异步处理**: asyncio
- **数据模拟**: 动态生成工业数据

## 项目结构

```
websocket-project/
├── service/              # 🔥 服务端文件夹
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
└── README.md           # 项目说明
```

## 核心功能

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

## 构建和运行

### 环境要求
**前端**:
- Node.js 16+
- npm 或 yarn

**后端**:
- Python 3.7+
- pip

### 前端开发
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 后端服务器
```bash
# 进入服务端目录
cd service

# 安装Python依赖
pip install -r requirements.txt

# 启动服务器
python websocket_server.py
```

## 配置说明

### 服务器配置 (service/server_config.py)
```python
SERVER_CONFIG = {
    "host": "0.0.0.0",          # 监听地址
    "port": 8088,               # 监听端口
    "path": "/ws/emosweb",      # WebSocket路径
    "push_interval_min": 2,     # 最小推送间隔
    "push_interval_max": 5,     # 最大推送间隔
    "enable_mock_data": True,   # 是否启用数据模拟
    "debug_mode": True,         # 是否显示调试信息
}
```

### 设备配置 (src/config/deviceConfig.json)
设备配置文件包含PLC设备的详细配置，包括：
- PLC标识符
- 数据点位标签
- 雪橇数量计算系数
- 滚床编号
- 权重值
- 区域标识
- 位置序号

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

## 开发约定

### 前端开发
- 使用Vue 3 Composition API
- 采用Element Plus组件库
- 遵循响应式设计原则
- 使用Vite作为构建工具

### 后端开发
- 使用Python 3.7+和asyncio异步编程
- 采用websockets库处理WebSocket连接
- 配置与代码分离的设计模式
- 日志输出用于调试和监控

### 代码维护
- 配置文件集中管理
- 依赖关系清晰
- 文档完整详细
- 支持多环境部署

## 部署说明

### 开发环境
- 前端: `npm run dev` (项目根目录)
- 后端: `python websocket_server.py` (service目录)

### 生产环境
- 前端: `npm run build` 然后部署dist目录
- 后端: service目录可独立部署到任何服务器

## 故障排除

### 连接问题
1. 确认WebSocket服务器在 `service/` 目录中启动
2. 检查端口8088是否被占用
3. 验证防火墙设置

### 路径问题
- 服务器启动: 必须在 `service/` 目录中执行
- 前端启动: 必须在项目根目录执行
- 配置修改: 编辑 `service/server_config.py`

### Python环境
```bash
# 检查Python版本
python --version

# 安装依赖
cd service
pip install -r requirements.txt
```