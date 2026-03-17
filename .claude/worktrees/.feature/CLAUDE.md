# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个完整的WebSocket工业数据采集演示系统，包含Vue 3前端和Python WebSocket后端，用于实时监控工业设备数据。系统支持35个工业设备点位，采用8区域网格布局，具备雪橇数量统计功能。

## 关键命令

### 开发环境启动

```bash
# 前端开发 (项目根目录)
npm install          # 安装依赖
npm run dev         # 启动开发服务器 (端口3000)

# 后端开发 (service目录)
cd service
pip install -r requirements.txt
python websocket_server.py  # 启动WebSocket服务器 (端口8088)

# 一键启动 (Windows)
start_server.bat    # 自动启动后端服务
```

### 生产构建

```bash
# 前端构建
npm run build       # 构建到dist目录
npm run preview     # 预览构建结果

# 后端独立部署
# service目录可独立部署到任何Python环境
```

## 架构概述

### 前端架构 (src/)

**主要组件:**
- `home/App.vue` - 主应用组件(131KB)，包含完整WebSocket客户端实现
- `home/index.vue` - 页面入口组件
- `config/deviceConfig.json` - 设备配置文件，35个工业设备点位分布在8个区域

**技术栈:**
- Vue 3.4+ (Composition API)
- Element Plus 2.4+ (UI组件库)
- Vite 5.0+ (构建工具)
- 原生WebSocket API

### 后端架构 (service/)

**核心文件:**
- `websocket_server.py` - 主WebSocket服务器，端口8088，路径/ws/emosweb
- `server_config.py` - 服务器配置文件，支持动态修改
- `start_server.py` - 配置化启动脚本

**技术栈:**
- Python 3.7+
- websockets 12.0
- asyncio (异步处理)

### 核心功能特性

1. **WebSocket实时通信**:
   - 自动重连机制，心跳保活(2秒间隔)
   - 支持100+设备点位订阅
   - 多客户端并发连接

2. **8区域数据可视化**:
   - 工业设备点位分布在8个独立监控区域
   - L3FUB2和L3FKT1系列PLC设备
   - 实时数据表格，支持区域统计

3. **雪橇数量统计**:
   - 支持norm(5)和e5(5)两种计算因子
   - 每个设备可配置独立权重
   - 防抖和缓存优化性能

4. **响应式设计**:
   - 桌面端完整8区域布局 + 缩略图面板
   - 移动端自适应布局
   - 渐变色背景，现代化UI

## 数据流程

1. 前端连接到 `ws://localhost:8088/ws/emosweb`
2. 客户端发送"advise"消息订阅设备点位
3. 服务器推送模拟数据给订阅的客户端
4. 前端根据因子配置计算雪橇数量
5. 数据按区域分组显示在实时表格中

## 配置文件说明

### 前端配置
- `src/config/deviceConfig.json` - 设备配置，包含区域映射、计算因子、权重设置

### 后端配置
- `service/server_config.py` - 服务器配置，包含端口、推送间隔、调试选项
- `service/requirements.txt` - Python依赖管理

## 开发规范

基于 `.cursor/rules/` 配置:

1. **代码简洁**: 优先选择简单方案，避免重复代码
2. **环境区分**: 明确区分dev/test/prod环境
3. **谨慎修改**: 仅针对明确需求更改，彻底排查现有实现
4. **文件规范**: 控制单文件200-300行，保持代码库整洁
5. **数据管理**: 仅测试环境使用模拟数据

## 性能优化

- 前端: 防抖处理、统计缓存、响应式表格优化
- 后端: 异步WebSocket处理、客户端订阅管理、数据推送批处理
- 界面: 虚拟滚动、懒加载组件、CSS动画优化

## 扩展性设计

- **模块化**: 前后端分离，service目录独立部署
- **配置化**: 设备配置、服务器配置支持动态修改
- **文档完整**: 20+个技术文档，涵盖实现原理和优化方案

## 重要提示

- 尽量使用中文回复，对于专业词汇则使用英文补充
- 修改文件应该注明时间
- service目录可以独立部署，是完整的服务端解决方案