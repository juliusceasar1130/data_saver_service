-- ============================================
-- 数据库改造 SQL 脚本 (PostgreSQL 版本)
-- 创建日期: 2026-01-20
-- 说明: 基于 RB位置状态版 设计方案
-- ============================================

-- 删除旧表(如果存在)
DROP TABLE IF EXISTS rb_position_data CASCADE;
DROP TABLE IF EXISTS vehicle_body_types CASCADE;
DROP TABLE IF EXISTS vehicle_color_codes CASCADE;
DROP TABLE IF EXISTS vehicle_platforms CASCADE;

-- ============================================
-- 1. 主表: rb_position_data (RB位置车辆数据表)
-- ============================================
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
COMMENT ON COLUMN rb_position_data.id IS '主键ID';
COMMENT ON COLUMN rb_position_data.plc IS '所属PLC设备名称';
COMMENT ON COLUMN rb_position_data.tag IS 'WebSocket订阅Tag,唯一标识采集点';
COMMENT ON COLUMN rb_position_data.rb_index IS 'Robot位置索引(标识物理位置)';
COMMENT ON COLUMN rb_position_data.remark IS '采集点物理位置备注';
COMMENT ON COLUMN rb_position_data.vehicle_id IS '车身唯一标识ID (0-13位)';
COMMENT ON COLUMN rb_position_data.body_type IS '车身类型代码 (14-18位), 关联vehicle_body_types表';
COMMENT ON COLUMN rb_position_data.color_code IS '颜色代码 (19-22位), 关联vehicle_color_codes表';
COMMENT ON COLUMN rb_position_data.platform_code IS '车型平台代码 (23-25位), 关联vehicle_platforms表';
COMMENT ON COLUMN rb_position_data.black_roof_flag IS '黑色车顶标志位 (26位)';
COMMENT ON COLUMN rb_position_data.rework_flag IS '返工车标志位 (27位)';
COMMENT ON COLUMN rb_position_data.reserved_1 IS '预留字段1 (28位)';
COMMENT ON COLUMN rb_position_data.reserved_2 IS '预留字段2 (29位)';
COMMENT ON COLUMN rb_position_data.raw_data IS '原始30字符完整数据';
COMMENT ON COLUMN rb_position_data.position_created_at IS '位置创建时间';
COMMENT ON COLUMN rb_position_data.vehicle_updated_at IS '车辆数据最后更新时间';

-- 创建索引
CREATE INDEX idx_rb_position_plc ON rb_position_data(plc);
CREATE INDEX idx_rb_position_vehicle_id ON rb_position_data(vehicle_id);
CREATE INDEX idx_rb_position_body_type ON rb_position_data(body_type);
CREATE INDEX idx_rb_position_vehicle_updated ON rb_position_data(vehicle_updated_at);


-- ============================================
-- 2. 辅助表: vehicle_body_types (车身类型字典表)
-- ============================================
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
COMMENT ON COLUMN vehicle_body_types.body_type IS '车身类型代码, 如 VS21J';
COMMENT ON COLUMN vehicle_body_types.type_name IS '车型名称, 如 "奥迪A4L"';
COMMENT ON COLUMN vehicle_body_types.is_defined IS '是否预定义 (TRUE: 已知, FALSE: 自动发现)';

CREATE INDEX idx_body_types_is_defined ON vehicle_body_types(is_defined);


-- ============================================
-- 3. 辅助表: vehicle_color_codes (颜色代码字典表)
-- ============================================
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
COMMENT ON COLUMN vehicle_color_codes.color_code IS '颜色代码, 如 2LA1';
COMMENT ON COLUMN vehicle_color_codes.color_name IS '颜色名称, 如 "珍珠白"';

CREATE INDEX idx_color_codes_is_defined ON vehicle_color_codes(is_defined);


-- ============================================
-- 4. 辅助表: vehicle_platforms (车型平台字典表)
-- ============================================
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
COMMENT ON COLUMN vehicle_platforms.platform_code IS '平台代码, 如 MLB';
COMMENT ON COLUMN vehicle_platforms.platform_name IS '平台名称, 如 "MLB Evo"';

CREATE INDEX idx_platforms_is_defined ON vehicle_platforms(is_defined);


-- ============================================
-- 创建 updated_at 自动更新触发器函数
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为字典表添加触发器
CREATE TRIGGER update_vehicle_body_types_updated_at
    BEFORE UPDATE ON vehicle_body_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicle_color_codes_updated_at
    BEFORE UPDATE ON vehicle_color_codes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicle_platforms_updated_at
    BEFORE UPDATE ON vehicle_platforms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 创建完成提示
-- ============================================
SELECT 'PostgreSQL tables created successfully!' AS status;
