# 数据库改造使用说明

本文档说明如何使用数据库改造相关的脚本和工具。

**运行环境：conda activate websoket**

## 📁 文件清单

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `create_tables.sql` | 数据库表结构 DDL | 创建 rb_position_data 主表和3个字典表 |
| `init_rb_positions.py` | 位置数据初始化脚本 | 读取 deviceConfig.json,初始化98个位置记录 |
| `rb_position_manager.py` | 数据库操作封装类 | 提供车辆数据更新、查询、统计等方法 |
| `deviceConfig.json` | 设备配置文件 | 包含98个RB位置的配置信息 |

## 🚀 快速开始

### 步骤 1: 创建数据库表

使用 MySQL 客户端或工具执行 SQL 脚本:

```bash
mysql -u root -p your_database < create_tables.sql
```

或者在 MySQL 命令行中:

```sql
USE your_database;
SOURCE d:/Python/workplace/skid_count_websoket/savedatabase/create_tables.sql;
```

**创建的表:**
- `rb_position_data` - RB位置车辆数据主表
- `vehicle_body_types` - 车身类型字典表
- `vehicle_color_codes` - 颜色代码字典表
- `vehicle_platforms` - 车型平台字典表

### 步骤 2: 初始化位置数据

运行 Python 初始化脚本:

```bash
cd d:\Python\workplace\skid_count_websoket\savedatabase
python init_rb_positions.py
```

**注意:** 运行前需要修改脚本中的数据库连接配置:

```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的密码',  # ← 修改这里
    'database': '你的数据库名'  # ← 修改这里
}
```

**初始化结果:**
- 会在 `rb_position_data` 表中插入 98 条位置记录
- 每条记录包含: plc, tag, RBindex, remark
- 车辆相关字段初始为 NULL

### 步骤 3: 验证初始化

在 MySQL 中验证:

```sql
-- 查询总记录数
SELECT COUNT(*) FROM rb_position_data;  -- 应该是 98

-- 按 PLC 分组统计
SELECT plc, COUNT(*) FROM rb_position_data GROUP BY plc;

-- 查看前几条记录
SELECT * FROM rb_position_data LIMIT 5;
```

## 💻 使用数据库操作类

### 基本使用

```python
from rb_position_manager import RBPositionDataManager

# 配置数据库连接
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'your_database'
}

# 使用上下文管理器(推荐)
with RBPositionDataManager(db_config) as manager:
    # 你的操作代码
    pass
```

### 核心操作示例

#### 1. 更新车辆数据 (WebSocket 接收数据时)

```python
with RBPositionDataManager(db_config) as manager:
    # 从 WebSocket 接收到的数据
    tag = ".L3F13_1A_1A010LT_1A010RB.IL.SD.M1003_BodyID"
    raw_data_30 = "12345678901234VS21J2LA1MLB100"  # 30字符车身数据
    
    # 更新数据库
    success = manager.update_vehicle_by_tag(tag, raw_data_30)
    
    if success:
        print("车辆数据更新成功")
```

**自动功能:**
- 自动解析30字符数据
- 自动更新 `vehicle_updated_at` 时间戳
- 自动发现未知的车型/颜色/平台代码并插入字典表

#### 2. 查询位置信息

```python
with RBPositionDataManager(db_config) as manager:
    # 根据 tag 查询
    position = manager.get_position_by_tag(tag)
    print(f"RBindex: {position['RBindex']}")
    print(f"当前车辆ID: {position['vehicle_id']}")
    
    # 根据 RBindex 查询
    position = manager.get_position_by_rbindex("1A010RB")
```

#### 3. 查询所有有车的位置

```python
with RBPositionDataManager(db_config) as manager:
    occupied = manager.get_occupied_positions()
    
    for pos in occupied:
        print(f"RB: {pos['RBindex']}, 车辆: {pos['vehicle_id']}, 更新时间: {pos['vehicle_updated_at']}")
```

#### 4. 清空车辆数据 (车辆离开时)

```python
with RBPositionDataManager(db_config) as manager:
    tag = ".L3F13_1A_1A010LT_1A010RB.IL.SD.M1003_BodyID"
    manager.clear_vehicle_by_tag(tag)
```

#### 5. 获取统计信息

```python
with RBPositionDataManager(db_config) as manager:
    stats = manager.get_statistics()
    
    print(f"总位置数: {stats['total_positions']}")
    print(f"有车位置: {stats['occupied_positions']}")
    print(f"空位置: {stats['empty_positions']}")
    
    print("\n按PLC统计:")
    for plc_stat in stats['by_plc']:
        print(f"  {plc_stat['plc']}: {plc_stat['occupied']}/{plc_stat['total']}")
```

## 🔄 与 data_saver_service.py 集成

在 `data_saver_service.py` 中集成数据库操作:

```python
from rb_position_manager import RBPositionDataManager

class DataSaverService:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'your_password',
            'database': 'your_database'
        }
        
        # 创建数据库管理器
        self.db_manager = RBPositionDataManager(self.db_config)
        self.db_manager.connect()
    
    def on_websocket_message(self, tag, value):
        """WebSocket 消息回调"""
        # 假设 value 是30字符车身数据
        if len(value) == 30:
            # 更新数据库
            self.db_manager.update_vehicle_by_tag(tag, value)
        else:
            print(f"数据格式错误: {value}")
    
    def close(self):
        """关闭服务"""
        self.db_manager.close()
```

## 📊 数据库表结构

### rb_position_data 主表

| 字段 | 类型 | 说明 | 初始值 |
|------|------|------|--------|
| id | BIGINT | 主键 | 自增 |
| plc | VARCHAR(20) | PLC名称 | 来自配置 |
| tag | VARCHAR(200) | 标签(唯一) | 来自配置 |
| RBindex | VARCHAR(20) | RB位置(唯一) | 来自配置 |
| remark | VARCHAR(100) | 备注 | 来自配置 |
| vehicle_id | VARCHAR(14) | 车辆ID | NULL |
| body_type | VARCHAR(5) | 车型代码 | NULL |
| color_code | VARCHAR(4) | 颜色代码 | NULL |
| platform_code | VARCHAR(3) | 平台代码 | NULL |
| black_roof_flag | CHAR(1) | 黑顶标志 | NULL |
| rework_flag | CHAR(1) | 返工标志 | NULL |
| reserved_1 | CHAR(1) | 预留1 | NULL |
| reserved_2 | CHAR(1) | 预留2 | NULL |
| raw_data | VARCHAR(30) | 原始数据 | NULL |
| position_created_at | DATETIME | 位置创建时间 | 当前时间 |
| vehicle_updated_at | DATETIME | 车辆更新时间 | NULL |

## 🔍 常用查询示例

```sql
-- 查看所有有车的位置
SELECT RBindex, vehicle_id, body_type, color_code, vehicle_updated_at
FROM rb_position_data
WHERE vehicle_id IS NOT NULL
ORDER BY vehicle_updated_at DESC;

-- 按车型统计
SELECT body_type, COUNT(*) as count
FROM rb_position_data
WHERE vehicle_id IS NOT NULL
GROUP BY body_type;

-- 查看未定义的车型代码
SELECT * FROM vehicle_body_types WHERE is_defined = FALSE;

-- 查看30分钟内更新的车辆
SELECT * FROM rb_position_data
WHERE vehicle_updated_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE);
```

## ⚠️ 注意事项

1. **数据库连接**: 使用前确保 MySQL 服务已启动
2. **依赖安装**: 需要安装 `mysql-connector-python`
   ```bash
   pip install mysql-connector-python
   ```
3. **权限**: 确保数据库用户有 INSERT, UPDATE, SELECT 权限
4. **并发**: 如果有多个进程同时写入,考虑使用连接池
5. **备份**: 定期备份数据库

## 📝 后续开发建议

- [ ] 添加历史数据表,记录车辆完整流转过程
- [ ] 实现车辆移动轨迹追踪
- [ ] 添加异常数据告警机制
- [ ] 实现数据统计和报表功能
- [ ] 添加 Web 界面实时监控
