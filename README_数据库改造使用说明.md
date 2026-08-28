# 数据库改造使用说明

本文档说明如何使用数据库改造相关的脚本和工具。
**更新日期: 2026-08-27**（修正过时文件名/路径，移除已废弃的增量迁移脚本，更新数据库示例值）

**运行环境：conda activate websoket**

## 📁 文件清单

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `create_tables_postgresql.sql` | 数据库表结构 DDL (PostgreSQL) | 创建 rb_position_data 主表和5个字典表（工艺区域、载体类型等） |
| `init_rb_positions_postgresql.py` | 位置数据初始化脚本 | 读取 deviceConfig.json,初始化98个位置记录 |
| `init_seed_data_postgresql.py` | 字典表预填充脚本 | 读取 seed_data.json,预填充 process_areas / carrier_types 字典表 |
| `seed_data.json` | 种子数据文件 | 工艺区域与载体类型的预置数据 |
| `deviceConfig.json` | 设备配置文件 | 包含98个RB位置的配置信息 (含 process_area) |
| `data_saver_service_v3_docker.py` | V3 数据保存服务 (Docker版) | **[推荐]** 同时支持车身数据(30字符)和载体ID的自动订阅与保存 |
| `rb_position_manager_postgresql.py` | 数据库操作封装类 (PostgreSQL) | 提供车辆数据更新、载体更新、查询、统计等方法 |

## 🚀 快速开始

### 步骤 1: 创建数据库表

使用 PostgreSQL 客户端执行全量建表脚本（内含 DROP TABLE IF EXISTS 重建逻辑，兼容全新部署与已存历史数据的数据库）:
```bash
psql -U root -d rollerbed_tracking_db -f create_tables_postgresql.sql
```

**创建/更新的表:**
- `rb_position_data` - 主表（新增 `process_area`, `carrier_id`, `carrier_type` 字段）
- `process_areas` - 生产工艺区域字典表
- `carrier_types` - **[新增]** 载体类型字典表 (hanger/skid)
- `vehicle_body_types` - 车身类型字典表
- `vehicle_color_codes` - 颜色代码字典表
- `vehicle_platforms` - 车型平台字典表

### 步骤 2: 初始化位置数据

运行 Python 初始化脚本:

```bash
cd f:\000_dev\Python\workplace\savedatabase-postgresql_v2
python init_rb_positions_postgresql.py
```

**注意:** 脚本默认读取项目根目录 `.env` 中的数据库连接配置（DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME），也可通过环境变量覆盖；默认连接 `rollerbed_tracking_db`（用户 root）。

**初始化结果:**
- 会在 `rb_position_data` 表中插入 98 条位置记录
- 每条记录包含: plc, tag, RBindex, remark
- 车辆相关字段初始为 NULL

### 步骤 3: 验证初始化

在 PostgreSQL 中验证:

```sql
-- 查询总记录数
SELECT COUNT(*) FROM rb_position_data;  -- 应该是 98

-- 按 PLC 分组统计
SELECT plc, COUNT(*) FROM rb_position_data GROUP BY plc;

-- 查看前几条记录
SELECT * FROM rb_position_data LIMIT 5;
```

### 步骤 4: 预填充字典表（可选但推荐）

```bash
python init_seed_data_postgresql.py
```

**说明:** 读取 `seed_data.json`，预填充 `process_areas`（工艺区域）和 `carrier_types`（载体类型）两张字典表；冲突策略为 `ON CONFLICT DO UPDATE`，可重复执行。

## 💻 使用数据库操作类

### 基本使用

```python
from rb_position_manager_postgresql import RBPositionDataManager

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

#### 2. 更新载体 ID (独立于车身数据)

```python
with RBPositionDataManager(db_config) as manager:
    # 从 WebSocket 接收到的载体数据
    tag = ".L3F13_1A_1A010LT_1A010RB.IL.SD.M1003_CarrierID"
    carrier_id = "C20240001"
    ts = "2024-03-20 10:00:00" # 可选，默认为当前时间
    
    # 更新数据库中的 carrier_id
    success = manager.update_carrier_id_by_tag(tag, carrier_id, ts)
    
    if success:
        print("载体数据更新成功")
```

#### 3. 查询位置信息

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
from rb_position_manager_postgresql import RBPositionDataManager

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

## 🐳 Docker 服务环境变量

在使用 `data_saver_service_v2_docker.py` 或 `v3` 时，建议通过环境变量进行配置：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DB_HOST` | 数据库主机地址 | `localhost` 或 `172.17.0.1` |
| `DB_PORT` | 数据库端口 | `5432` |
| `DB_USER` | 数据库用户名 | `root` |
| `DB_PASSWORD` | 数据库密码 | `******` |
| `DB_NAME` | 数据库名称 | `rollerbed_tracking_db` |
| `WS_SERVER_HOST` | WebSocket 服务器地址 | `10.123.45.67` |
| `WS_SERVER_PORT` | WebSocket 服务器端口 | `8081` |
| `DEVICE_CONFIG_PATH` | 配置文件路径 | `./deviceConfig.json` |

## 📊 数据库表结构

### rb_position_data 主表

| 字段 | 类型 | 说明 | 初始值 |
|------|------|------|--------|
| id | BIGSERIAL | 主键 | 自增 |
| plc | VARCHAR(20) | PLC名称 | 来自配置 |
| tag | VARCHAR(200) | 标签(唯一) | 来自配置 |
| rb_index | VARCHAR(20) | RB位置(唯一) | 来自配置 |
| remark | VARCHAR(100) | 备注 | 来自配置 |
| **process_area** | **VARCHAR(50)** | **生产工艺区域(如:L2面漆存储线)** | **来自配置** |
| **carrier_id** | **VARCHAR(50)** | **载体唯一标识(如挂具编号)** | **来自配置** |
| **carrier_type** | **VARCHAR(20)** | **载体类型(hanger/skid)** | **来自配置** |
| vehicle_id | VARCHAR(14) | 车辆ID | NULL |
| body_type | VARCHAR(5) | 车型代码 | NULL |
| color_code | VARCHAR(4) | 颜色代码 | NULL |
| platform_code | VARCHAR(3) | 平台代码 | NULL |
| black_roof_flag | CHAR(1) | 黑顶标志 | NULL |
| rework_flag | CHAR(1) | 返工标志 | NULL |
| reserved_1 | CHAR(1) | 预留1 | NULL |
| reserved_2 | CHAR(1) | 预留2 | NULL |
| raw_data | VARCHAR(30) | 原始数据 | NULL |
| position_created_at | TIMESTAMP | 位置创建时间 | CURRENT_TIMESTAMP |
| vehicle_updated_at | TIMESTAMP | 车辆更新时间 | NULL |

### process_areas 字典表 [新增]

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| area_name | VARCHAR(50) | 工艺区域名称(唯一) |
| description | VARCHAR(200)| 区域描述 |
| sort_order | INT | 工艺流转顺序 |

### carrier_types 字典表 [新增]

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| type_code | VARCHAR(20) | 类型代码 (hanger/skid) |
| type_name_cn | VARCHAR(50) | 中文名称 (吊架/滑橇/雪橇) |
| description | VARCHAR(200)| 类型描述 |
| sort_order | INT | 排序权重 |

## 🔍 常用查询示例

```sql
-- 1. 查看特定工艺区域的有车位置
SELECT rb_index, vehicle_id, body_type, vehicle_updated_at
FROM rb_position_data
WHERE process_area = 'L2面漆存储线' AND vehicle_id IS NOT NULL
ORDER BY vehicle_updated_at DESC;

-- 2. 按工艺区域统计在线车辆数
SELECT process_area, COUNT(*) as count
FROM rb_position_data
WHERE vehicle_id IS NOT NULL
GROUP BY process_area;

-- 3. 关联字典表查看区域详细描述
SELECT r.rb_index, r.vehicle_id, p.description
FROM rb_position_data r
JOIN process_areas p ON r.process_area = p.area_name;

-- 4. 查看未定义的车型代码
SELECT * FROM vehicle_body_types WHERE is_defined = FALSE;

-- 5. 查看吊架(hanger)上的在线车辆数
SELECT COUNT(*) FROM rb_position_data 
WHERE carrier_type = 'hanger' AND vehicle_id IS NOT NULL;

-- 6. 关联查询位置及其载体类型的实际描述
SELECT r.rb_index, r.carrier_id, c.type_name_cn
FROM rb_position_data r
JOIN carrier_types c ON r.carrier_type = c.type_code;

-- 7. 查看特定载体的当前位置
SELECT rb_index, carrier_id, vehicle_id, vehicle_updated_at
FROM rb_position_data
WHERE carrier_id = 'C20240001';
```

## ⚠️ 注意事项

1. **数据库类型**: 本项目目前已全面转向 **PostgreSQL**。
2. **依赖安装**: 需要安装 `psycopg2` 或 `psycopg2-binary`
   ```bash
   pip install psycopg2-binary
   ```
3. **权限**: 确保数据库用户有 INSERT, UPDATE, SELECT 权限
4. **并发**: PostgreSQL 处理并发更新性能优异，推荐使用连接池。
5. **备份**: 定期备份数据库

## 📝 后续开发建议

- [ ] 添加历史数据表,记录车辆完整流转过程
- [ ] 实现车辆移动轨迹追踪
- [ ] 添加异常数据告警机制
- [ ] 实现数据统计和报表功能
- [ ] 添加 Web 界面实时监控
