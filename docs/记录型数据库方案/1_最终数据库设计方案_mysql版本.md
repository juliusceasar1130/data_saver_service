# 最终数据库设计方案

本方案基于 WebSocket 接收的 30 字符车身数据进行解析和存储。设计的核心原则是语义化、支持大模型（LLM）理解，以及兼顾数据的完整性与扩展性。

## 1. 设计概述

- **主表 (vehicle_data)**：存储每辆车的核心解析数据及原始数据。
- **字典表 (Auxiliary Tables)**：提供车身类型、颜色、平台的语义映射，支持大模型自然语言查询。
- **混合模式 (Hybrid Mode)**：字典表支持预置已知代码 + 自动发现未知代码。
- **LLM 友好性**：包含详细的表级和字段级中文注释。

## 2. 数据库表结构 SQL

### 2.1 主表：vehicle_data (车身数据表)

```sql
CREATE TABLE vehicle_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键，自增ID',
    
    vehicle_id VARCHAR(14) UNIQUE NOT NULL 
        COMMENT '车身唯一标识ID，从30字符数据的第0-13位提取，用于唯一标识每辆车',
    
    body_type VARCHAR(5) NOT NULL 
        COMMENT '车身类型代码，从30字符数据的第14-18位提取，标识车型种类（如奥迪A4L、Q5L等），关联vehicle_body_types表',
    
    color_code VARCHAR(4) NOT NULL 
        COMMENT '车身颜色代码，从30字符数据的第19-22位提取，标识车身颜色（如珍珠白、极地黑等），关联vehicle_color_codes表',
    
    platform_code VARCHAR(3) NOT NULL 
        COMMENT '车型平台代码，从30字符数据的第23-25位提取，标识底盘平台（如MLB、MQB等），关联vehicle_platforms表',
    
    black_roof_flag CHAR(1) NOT NULL 
        COMMENT '黑色车顶标志位，从30字符数据的第26位提取，1表示有黑色车顶，0表示无黑色车顶',
    
    rework_flag CHAR(1) NOT NULL 
        COMMENT '返工车标志位，从30字符数据的第27位提取，1表示返工车，0表示正常车辆（一次喷涂），2表示黑顶的第二次喷涂',
    
    reserved_1 CHAR(1) 
        COMMENT '预留字段1，从30字符数据的第28位提取，暂未使用',
    
    reserved_2 CHAR(1) 
        COMMENT '预留字段2，从30字符数据的第29位提取，暂未使用',
    
    raw_data VARCHAR(30) NOT NULL 
        COMMENT '原始30字符完整数据，用于数据追溯和调试',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间，数据入库时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_body_type (body_type),
    INDEX idx_color_code (color_code),
    INDEX idx_platform_code (platform_code),
    INDEX idx_black_roof_flag (black_roof_flag),
    INDEX idx_rework_flag (rework_flag),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='车辆数据主表，存储从WebSocket接收的车辆信息，每条记录代表一辆车的完整信息';
```

### 2.2 辅助表：vehicle_body_types (车身类型字典表)

```sql
CREATE TABLE vehicle_body_types (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键，自增ID',
    
    body_type VARCHAR(5) UNIQUE NOT NULL 
        COMMENT '车身类型代码，如VS21J、MK32A等，与vehicle_data.body_type对应',
    
    type_name VARCHAR(100) 
        COMMENT '车型名称，如"奥迪A4L"、"奥迪Q5L"等，便于人类阅读',
    
    description VARCHAR(200) 
        COMMENT '车型详细描述，包含车型的详细信息',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义，TRUE表示预先定义的已知车型，FALSE表示系统自动发现的未知车型',
    
    first_seen DATETIME 
        COMMENT '首次出现时间，记录该车型代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='车身类型字典表，存储车型代码与车型名称的映射关系，用于将代码转换为可读的车型名称';
```

### 2.3 辅助表：vehicle_color_codes (颜色代码字典表)

```sql
CREATE TABLE vehicle_color_codes (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键，自增ID',
    
    color_code VARCHAR(4) UNIQUE NOT NULL 
        COMMENT '颜色代码，如2LA1、3MB2等，与vehicle_data.color_code对应',
    
    color_name VARCHAR(50) 
        COMMENT '颜色名称，如"珍珠白"、"极地黑"等，便于人类阅读和查询',
    
    color_description VARCHAR(100) 
        COMMENT '颜色详细描述，如"珍珠白金属漆"等',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义，TRUE表示预先定义的已知颜色，FALSE表示系统自动发现的未知颜色',
    
    first_seen DATETIME 
        COMMENT '首次出现时间，记录该颜色代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='颜色代码字典表，存储颜色代码与颜色名称的映射关系，支持按颜色名称查询车辆';
```

### 2.4 辅助表：vehicle_platforms (车型平台字典表)

```sql
CREATE TABLE vehicle_platforms (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键，自增ID',
    
    platform_code VARCHAR(3) UNIQUE NOT NULL 
        COMMENT '平台代码，如MLB、MQB等，与vehicle_data.platform_code对应',
    
    platform_name VARCHAR(50) 
        COMMENT '平台名称，如"MLB Evo"、"MQB"等，便于人类阅读',
    
    description VARCHAR(200) 
        COMMENT '平台详细描述，如"大众MLB Evo纵置发动机模块化平台"',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义，TRUE表示预先定义的已知平台，FALSE表示系统自动发现的未知平台',
    
    first_seen DATETIME 
        COMMENT '首次出现时间，记录该平台代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='车型平台字典表，存储平台代码与平台名称的映射关系，用于按平台统计和查询车辆';
```

## 3. 数据处理逻辑（伪代码）

在获取每一条 WebSocket 数据时：

1.  **解析数据**：将 30 字符切分为 ID、Type、Color、Platform 等字段。
2.  **字典校验 (混合模式)**：
    *   检查 `body_type` 是否在 `vehicle_body_types` 表中。
    *   **存在**：不做操作。
    *   **不存在**：插入一条新记录，`type_name` 为 "未定义车型-CODE"，`is_defined` 设为 `FALSE`。
    *   (同理处理 Color 和 Platform)
3.  **插入主表**：将解析后的数据存入 `vehicle_data`。

这种机制确保了：
*   **不丢数据**：即使遇到新车型也能保存主数据。
*   **即时发现**：新的代码会被捕捉并在字典表中标记为未定义。
*   **后续补全**：运维人员可以定期查询 `is_defined = FALSE` 的记录并补充名称。
