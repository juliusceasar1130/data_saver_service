# 数据保存服务使用说明

**修改时间：2025年9月1日14点05分**  
**修改内容：创建数据保存服务文档**

## 功能说明

数据保存服务是一个独立的 WebSocket 客户端服务，用于：
- 连接到 WebSocket 服务器
- 订阅所有设备数据
- 接收数据并自动保存到 `production_record.production` 表
- 支持自动重连和心跳保活

## 数据库表结构

表名：`production_record.production`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| tag | VARCHAR(255) | 标签字符串 |
| value | VARCHAR(255) | 数据值字符串 |
| ts | TIMESTAMP | 时间戳 |

## 安装依赖

```bash
cd savedatabase
pip install -r requirements.txt
```

## 配置说明

### WebSocket 服务器配置

在 `data_saver_service.py` 中修改：

```python
WS_SERVER_HOST = "localhost"  # WebSocket服务器地址
WS_SERVER_PORT = 8088          # WebSocket服务器端口
WS_SERVER_PATH = "/ws/emosweb" # WebSocket路径
```

### 数据库配置

在 `data_saver_service.py` 中修改：

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'production_record',
    'charset': 'utf8mb4'
}
```

## 启动服务

### Windows 系统

```bash
# 方式1：使用启动脚本
start_data_saver.bat

# 方式2：直接运行
python data_saver_service.py
```

### Linux/Mac 系统

```bash
# 方式1：使用启动脚本
chmod +x start_data_saver.sh
./start_data_saver.sh

# 方式2：直接运行
python3 data_saver_service.py
```

## 使用流程

1. **确保 WebSocket 服务器正在运行**
   ```bash
   # 在 service 目录下启动
   python websocket_server.py
   ```

2. **确保数据库服务正在运行**
   - MySQL 服务必须启动
   - 数据库 `production_record` 必须存在
   - 表 `production` 必须已创建

3. **启动数据保存服务**
   ```bash
   cd savedatabase
   python data_saver_service.py
   ```

4. **查看日志**
   - 控制台输出实时日志
   - 日志文件：`data_saver_service.log`

## 功能特性

- ✅ **自动订阅所有设备**：从 `deviceConfig.json` 读取设备列表并订阅
- ✅ **自动保存数据**：接收到的数据自动保存到数据库
- ✅ **心跳保活**：每 2 秒发送心跳，保持连接
- ✅ **自动重连**：连接断开时自动重连（最多 10 次）
- ✅ **错误处理**：数据库保存失败不影响数据接收
- ✅ **详细日志**：记录所有操作和错误信息

## 日志说明

服务运行时会生成日志文件：`data_saver_service.log`

日志级别：
- `INFO`：正常操作信息
- `WARNING`：警告信息
- `ERROR`：错误信息
- `DEBUG`：调试信息（心跳等）

## 注意事项

1. **服务依赖**
   - WebSocket 服务器必须先启动
   - 数据库服务必须正在运行
   - 确保设备配置文件路径正确

2. **性能考虑**
   - 每条消息都会立即保存到数据库
   - 高频数据时，数据库写入可能成为瓶颈
   - 建议定期检查数据库性能

3. **错误处理**
   - 数据库保存失败不会影响数据接收
   - 连接断开会自动重连
   - 所有错误都会记录到日志文件

4. **独立运行**
   - 服务可以独立运行，不影响其他服务
   - 可以同时运行多个实例（不推荐）
   - 建议使用进程管理工具（如 systemd、supervisor）管理服务

## 故障排查

### 问题1：无法连接到 WebSocket 服务器

**解决方案：**
- 检查 WebSocket 服务器是否正在运行
- 检查服务器地址和端口是否正确
- 检查防火墙设置

### 问题2：数据库连接失败

**解决方案：**
- 检查 MySQL 服务是否正在运行
- 检查数据库配置是否正确
- 检查数据库用户权限

### 问题3：设备订阅失败

**解决方案：**
- 检查 `deviceConfig.json` 文件是否存在
- 检查配置文件格式是否正确
- 检查文件路径是否正确

### 问题4：数据保存失败

**解决方案：**
- 检查数据库表是否存在
- 检查表结构是否正确
- 查看日志文件获取详细错误信息

## 停止服务

按 `Ctrl+C` 停止服务

服务会优雅地关闭，完成当前的数据保存操作。

