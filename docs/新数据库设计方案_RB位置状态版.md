# 数据库设计方案 v2.0 (RB位置状态管理版 - PostgreSQL)

## 1. 设计概述

本方案是对原 `vehicle_data` 设计的升级改造。随着 `data_saver_service.py` 逻辑的重新设计,数据库的角色从纯粹的"流水记录"转变为"位置状态管理"。

### 核心变更点
- **数据库**: 使用 PostgreSQL
- **表重命名**: `vehicle_data` → `rb_position_data`
- **管理模式**: 由"新增记录模式"改为"位置状态模式"。预先根据设备配置初始化所有位置,通过 Tag 标签实时更新对应位置的车辆信息。
- **数据源**: 初始化数据来源于 `deviceConfig.json`,动态数据来源于 WebSocket 30字符车身数据。

## 2. 数据库表结构

### 2.1 主表：rb_position_data (RB位置车辆数据表)

```sql
CREATE TABLE rb_position_data (
    -- 位置静态属性 (初始化填充)
    id BIGSERIAL PRIMARY KEY,
    plc VARCHAR(20) NOT NULL,
    tag VARCHAR(200) NOT NULL UNIQUE,
    rb_index VARCHAR(20) NOT NULL UNIQUE,
    remark VARCHAR(100),

    -- 车辆动态属性 (实时更新, 初始为 NULL)
    vehicle_id VARCHAR(14),
    body_type VARCHAR(5),
    color_code VARCHAR(4),
    platform_code VARCHAR(3),
    black_roof_flag CHAR(1),
    rework_flag CHAR(1),
    reserved_1 CHAR(1),
    reserved_2 CHAR(1),
    raw_data VARCHAR(30),

    -- 时间戳
    position_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vehicle_updated_at TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE rb_position_data IS '存储采集点及当前位置的车辆状态信息';
COMMENT ON COLUMN rb_position_data.plc IS '所属PLC设备名称';
COMMENT ON COLUMN rb_position_data.tag IS 'WebSocket订阅Tag,唯一标识采集点';
COMMENT ON COLUMN rb_position_data.rb_index IS 'Robot位置索引(标识物理位置)';
COMMENT ON COLUMN rb_position_data.vehicle_id IS '车身唯一标识ID (0-13位)';
COMMENT ON COLUMN rb_position_data.body_type IS '车身类型代码 (14-18位), 关联vehicle_body_types表';
COMMENT ON COLUMN rb_position_data.color_code IS '颜色代码 (19-22位), 关联vehicle_color_codes表';
COMMENT ON COLUMN rb_position_data.platform_code IS '车型平台代码 (23-25位), 关联vehicle_platforms表';

-- 创建索引
CREATE INDEX idx_rb_position_plc ON rb_position_data(plc);
CREATE INDEX idx_rb_position_vehicle_id ON rb_position_data(vehicle_id);
CREATE INDEX idx_rb_position_body_type ON rb_position_data(body_type);
```

### 2.2 辅助表：vehicle_body_types (车身类型字典表)

```sql
CREATE TABLE vehicle_body_types (
    id SERIAL PRIMARY KEY,
    body_type VARCHAR(5) UNIQUE NOT NULL,
    type_name VARCHAR(100),
    description VARCHAR(200),
    is_defined BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vehicle_body_types IS '车型代码映射字典';
COMMENT ON COLUMN vehicle_body_types.is_defined IS '是否预定义 (TRUE: 已知, FALSE: 自动发现)';
```

### 2.3 辅助表：vehicle_color_codes (颜色代码字典表)

```sql
CREATE TABLE vehicle_color_codes (
    id SERIAL PRIMARY KEY,
    color_code VARCHAR(4) UNIQUE NOT NULL,
    color_name VARCHAR(50),
    color_description VARCHAR(100),
    is_defined BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vehicle_color_codes IS '颜色代码映射字典';
```

### 2.4 辅助表：vehicle_platforms (车型平台字典表)

```sql
CREATE TABLE vehicle_platforms (
    id SERIAL PRIMARY KEY,
    platform_code VARCHAR(3) UNIQUE NOT NULL,
    platform_name VARCHAR(50),
    description VARCHAR(200),
    is_defined BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vehicle_platforms IS '车型平台映射字典';
```

## 3. 关系设计 (Relationship Design)

### 3.1 逻辑关联 vs 硬外键

主表 `rb_position_data` 与辅助字典表之间采用 **逻辑关联 (Logical Relationship)**, 未在 SQL 层面强制定义 `FOREIGN KEY` 约束。

**设计理由**:
1. **自动发现机制**: 当收到"未定义"的新代码时能自动记录,硬外键会导致事务失败
2. **性能与解耦**: 减少高频更新时的外键检查开销
3. **LLM 友好性**: 通过字段命名建立的一致性,依然能让大模型清晰理解映射关系

### 3.2 关联方式
- **关联字段**: `rb_position_data.body_type` ↔ `vehicle_body_types.body_type`
- **查询方式**: 采用 `LEFT JOIN` 进行映射查询
- **一致性维护**: 由 `rb_position_manager_postgresql.py` 的 `_auto_discover_codes` 方法维护

## 4. 数据处理逻辑

### 4.1 初始化阶段 (Initialization)
1. **读取配置**: 从 `deviceConfig.json` 中提取所有 PLC 下的设备节点
2. **预建记录**: 使用 `INSERT ... ON CONFLICT DO NOTHING` 确保98个位置行存在

### 4.2 动态更新阶段 (Dynamic Update)
1. **数据订阅**: 服务通过 `tag` 订阅 WebSocket 消息
2. **数据解析**: 将收到的 `(tag, raw_data)` 进行 30 位字符解析
3. **状态刷新**: 执行 `UPDATE ... WHERE tag = $1`
4. **代码自动发现**: 使用 `INSERT ... ON CONFLICT DO NOTHING` 自动补全字典

## 5. 相关文件

| 文件 | 说明 |
|------|------|
| `create_tables_postgresql.sql` | DDL 脚本 |
| `init_rb_positions_postgresql.py` | 位置初始化脚本 |
| `rb_position_manager_postgresql.py` | 数据库操作封装类 |
