-- ============================================
-- 数据库改造 SQL 脚本
-- 创建日期: 2026-01-20
-- 说明: 基于 1_最终数据库设计方案_mysql版本.md 改造
--       改造 vehicle_data 为 rb_position_data
-- ============================================

-- 删除旧表(如果存在)
DROP TABLE IF EXISTS rb_position_data;
DROP TABLE IF EXISTS vehicle_body_types;
DROP TABLE IF EXISTS vehicle_color_codes;
DROP TABLE IF EXISTS vehicle_platforms;

-- ============================================
-- 1. 主表: rb_position_data (RB位置车辆数据表)
-- ============================================
CREATE TABLE rb_position_data (
    -- ========== 位置标识字段 (初始化时填充,来自 deviceConfig.json) ==========
    id BIGINT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键,自增ID',
    
    plc VARCHAR(20) NOT NULL 
        COMMENT 'PLC设备名称,如 L3F13、L3FCC2',
    
    tag VARCHAR(200) NOT NULL UNIQUE
        COMMENT 'Tag标签,用于订阅 WebSocket 数据,唯一标识一个位置',
    
    RBindex VARCHAR(20) NOT NULL UNIQUE
        COMMENT 'Robot位置索引,如 1A010RB,唯一标识机器人位置',
    
    remark VARCHAR(100) 
        COMMENT '位置备注信息,如"面漆存储线"',
    
    -- ========== 车辆数据字段 (车辆到达时更新,初始为 NULL) ==========
    vehicle_id VARCHAR(14) 
        COMMENT '车身唯一标识ID,从30字符数据的第0-13位提取,用于唯一标识每辆车',
    
    body_type VARCHAR(5) 
        COMMENT '车身类型代码,从30字符数据的第14-18位提取,标识车型种类(如奥迪A4L、Q5L等),关联vehicle_body_types表',
    
    color_code VARCHAR(4) 
        COMMENT '车身颜色代码,从30字符数据的第19-22位提取,标识车身颜色(如珍珠白、极地黑等),关联vehicle_color_codes表',
    
    platform_code VARCHAR(3) 
        COMMENT '车型平台代码,从30字符数据的第23-25位提取,标识底盘平台(如MLB、MQB等),关联vehicle_platforms表',
    
    black_roof_flag CHAR(1) 
        COMMENT '黑色车顶标志位,从30字符数据的第26位提取,1表示有黑色车顶,0表示无黑色车顶',
    
    rework_flag CHAR(1) 
        COMMENT '返工车标志位,从30字符数据的第27位提取,1表示返工车,0表示正常车辆(一次喷涂),2表示黑顶的第二次喷涂',
    
    reserved_1 CHAR(1) 
        COMMENT '预留字段1,从30字符数据的第28位提取,暂未使用',
    
    reserved_2 CHAR(1) 
        COMMENT '预留字段2,从30字符数据的第29位提取,暂未使用',
    
    raw_data VARCHAR(30) 
        COMMENT '原始30字符完整数据,用于数据追溯和调试',
    
    -- ========== 时间戳字段 ==========
    position_created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '位置记录创建时间(数据库初始化时间)',
    
    vehicle_updated_at DATETIME 
        COMMENT '车辆数据最后更新时间,初始为 NULL,有车辆数据时更新',
    
    -- ========== 索引 ==========
    INDEX idx_plc (plc),
    INDEX idx_RBindex (RBindex),
    INDEX idx_vehicle_id (vehicle_id),
    INDEX idx_body_type (body_type),
    INDEX idx_color_code (color_code),
    INDEX idx_platform_code (platform_code),
    INDEX idx_black_roof_flag (black_roof_flag),
    INDEX idx_rework_flag (rework_flag),
    INDEX idx_vehicle_updated_at (vehicle_updated_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='RB位置车辆数据表。每条记录代表一个机器人位置(RBindex)及其当前车辆信息。采用位置状态模式:98个位置预先创建,车辆到达时更新对应位置的车辆字段';


-- ============================================
-- 2. 辅助表: vehicle_body_types (车身类型字典表)
-- ============================================
CREATE TABLE vehicle_body_types (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键,自增ID',
    
    body_type VARCHAR(5) UNIQUE NOT NULL 
        COMMENT '车身类型代码,如VS21J、MK32A等,与rb_position_data.body_type对应',
    
    type_name VARCHAR(100) 
        COMMENT '车型名称,如"奥迪A4L"、"奥迪Q5L"等,便于人类阅读',
    
    description VARCHAR(200) 
        COMMENT '车型详细描述,包含车型的详细信息',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义,TRUE表示预先定义的已知车型,FALSE表示系统自动发现的未知车型',
    
    first_seen DATETIME 
        COMMENT '首次出现时间,记录该车型代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='车身类型字典表,存储车型代码与车型名称的映射关系,用于将代码转换为可读的车型名称';


-- ============================================
-- 3. 辅助表: vehicle_color_codes (颜色代码字典表)
-- ============================================
CREATE TABLE vehicle_color_codes (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键,自增ID',
    
    color_code VARCHAR(4) UNIQUE NOT NULL 
        COMMENT '颜色代码,如2LA1、3MB2等,与rb_position_data.color_code对应',
    
    color_name VARCHAR(50) 
        COMMENT '颜色名称,如"珍珠白"、"极地黑"等,便于人类阅读和查询',
    
    color_description VARCHAR(100) 
        COMMENT '颜色详细描述,如"珍珠白金属漆"等',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义,TRUE表示预先定义的已知颜色,FALSE表示系统自动发现的未知颜色',
    
    first_seen DATETIME 
        COMMENT '首次出现时间,记录该颜色代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='颜色代码字典表,存储颜色代码与颜色名称的映射关系,支持按颜色名称查询车辆';


-- ============================================
-- 4. 辅助表: vehicle_platforms (车型平台字典表)
-- ============================================
CREATE TABLE vehicle_platforms (
    id INT AUTO_INCREMENT PRIMARY KEY 
        COMMENT '主键,自增ID',
    
    platform_code VARCHAR(3) UNIQUE NOT NULL 
        COMMENT '平台代码,如MLB、MQB等,与rb_position_data.platform_code对应',
    
    platform_name VARCHAR(50) 
        COMMENT '平台名称,如"MLB Evo"、"MQB"等,便于人类阅读',
    
    description VARCHAR(200) 
        COMMENT '平台详细描述,如"大众MLB Evo纵置发动机模块化平台"',
    
    is_defined BOOLEAN DEFAULT FALSE 
        COMMENT '是否已定义,TRUE表示预先定义的已知平台,FALSE表示系统自动发现的未知平台',
    
    first_seen DATETIME 
        COMMENT '首次出现时间,记录该平台代码第一次在系统中出现的时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        COMMENT '记录创建时间',
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '记录最后更新时间',
    
    INDEX idx_is_defined (is_defined)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='车型平台字典表,存储平台代码与平台名称的映射关系,用于按平台统计和查询车辆';


-- ============================================
-- 创建完成提示
-- ============================================
SELECT 'Database tables created successfully!' AS status;
