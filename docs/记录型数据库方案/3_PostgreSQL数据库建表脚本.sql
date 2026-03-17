-- ============================================================
-- PostgreSQL 数据库建表脚本
-- 用于车辆数据管理系统
-- ============================================================

-- 1. 主表：vehicle_data (车身数据表)
CREATE TABLE vehicle_data (
    id BIGSERIAL PRIMARY KEY,
    
    vehicle_id VARCHAR(14) UNIQUE NOT NULL,
    
    body_type VARCHAR(5) NOT NULL,
    
    color_code VARCHAR(4) NOT NULL,
    
    platform_code VARCHAR(3) NOT NULL,
    
    black_roof_flag CHAR(1) NOT NULL,
    
    rework_flag CHAR(1) NOT NULL,
    
    reserved_1 CHAR(1),
    
    reserved_2 CHAR(1),
    
    raw_data VARCHAR(30) NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加索引
CREATE INDEX idx_body_type ON vehicle_data(body_type);
CREATE INDEX idx_color_code ON vehicle_data(color_code);
CREATE INDEX idx_platform_code ON vehicle_data(platform_code);
CREATE INDEX idx_black_roof_flag ON vehicle_data(black_roof_flag);
CREATE INDEX idx_rework_flag ON vehicle_data(rework_flag);
CREATE INDEX idx_created_at ON vehicle_data(created_at);

-- 添加表注释
COMMENT ON TABLE vehicle_data IS '车辆数据主表，存储从WebSocket接收的车辆信息，每条记录代表一辆车的完整信息';

-- 添加字段注释
COMMENT ON COLUMN vehicle_data.id IS '主键，自增ID';
COMMENT ON COLUMN vehicle_data.vehicle_id IS '车身唯一标识ID，从30字符数据的第0-13位提取，用于唯一标识每辆车';
COMMENT ON COLUMN vehicle_data.body_type IS '车身类型代码，从30字符数据的第14-18位提取，标识车型种类（如奥迪A4L、Q5L等），关联vehicle_body_types表';
COMMENT ON COLUMN vehicle_data.color_code IS '车身颜色代码，从30字符数据的第19-22位提取，标识车身颜色（如珍珠白、极地黑等），关联vehicle_color_codes表';
COMMENT ON COLUMN vehicle_data.platform_code IS '车型平台代码，从30字符数据的第23-25位提取，标识底盘平台（如MLB、MQB等），关联vehicle_platforms表';
COMMENT ON COLUMN vehicle_data.black_roof_flag IS '黑色车顶标志位，从30字符数据的第26位提取，1=有黑色车顶，0=无黑色车顶';
COMMENT ON COLUMN vehicle_data.rework_flag IS '返工车标志位，从30字符数据的第27位提取，0=正常车辆（一次喷涂），1=返工车，2=黑顶的第二次喷涂';
COMMENT ON COLUMN vehicle_data.reserved_1 IS '预留字段1，从30字符数据的第28位提取，暂未使用';
COMMENT ON COLUMN vehicle_data.reserved_2 IS '预留字段2，从30字符数据的第29位提取，暂未使用';
COMMENT ON COLUMN vehicle_data.raw_data IS '原始30字符完整数据，用于数据追溯和调试';
COMMENT ON COLUMN vehicle_data.created_at IS '记录创建时间，数据入库时间';
COMMENT ON COLUMN vehicle_data.updated_at IS '记录最后更新时间';

-- 创建触发器函数用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 vehicle_data 表创建触发器
CREATE TRIGGER update_vehicle_data_updated_at
    BEFORE UPDATE ON vehicle_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 2. 辅助表：vehicle_body_types (车身类型字典表)
-- ============================================================
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

-- 添加索引
CREATE INDEX idx_body_types_is_defined ON vehicle_body_types(is_defined);

-- 添加表注释
COMMENT ON TABLE vehicle_body_types IS '车身类型字典表，存储车型代码与车型名称的映射关系，用于将代码转换为可读的车型名称';

-- 添加字段注释
COMMENT ON COLUMN vehicle_body_types.id IS '主键，自增ID';
COMMENT ON COLUMN vehicle_body_types.body_type IS '车身类型代码，如VS21J、MK32A等，与vehicle_data.body_type对应';
COMMENT ON COLUMN vehicle_body_types.type_name IS '车型名称，如"奥迪A4L"、"奥迪Q5L"等，便于人类阅读';
COMMENT ON COLUMN vehicle_body_types.description IS '车型详细描述，包含车型的详细信息';
COMMENT ON COLUMN vehicle_body_types.is_defined IS '是否已定义，TRUE=预先定义的已知车型，FALSE=系统自动发现的未知车型';
COMMENT ON COLUMN vehicle_body_types.first_seen IS '首次出现时间，记录该车型代码第一次在系统中出现的时间';
COMMENT ON COLUMN vehicle_body_types.created_at IS '记录创建时间';
COMMENT ON COLUMN vehicle_body_types.updated_at IS '记录最后更新时间';

-- 创建触发器
CREATE TRIGGER update_vehicle_body_types_updated_at
    BEFORE UPDATE ON vehicle_body_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 3. 辅助表：vehicle_color_codes (颜色代码字典表)
-- ============================================================
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

-- 添加索引
CREATE INDEX idx_color_codes_is_defined ON vehicle_color_codes(is_defined);

-- 添加表注释
COMMENT ON TABLE vehicle_color_codes IS '颜色代码字典表，存储颜色代码与颜色名称的映射关系，支持按颜色名称查询车辆';

-- 添加字段注释
COMMENT ON COLUMN vehicle_color_codes.id IS '主键，自增ID';
COMMENT ON COLUMN vehicle_color_codes.color_code IS '颜色代码，如2LA1、3MB2等，与vehicle_data.color_code对应';
COMMENT ON COLUMN vehicle_color_codes.color_name IS '颜色名称，如"珍珠白"、"极地黑"等，便于人类阅读和查询';
COMMENT ON COLUMN vehicle_color_codes.color_description IS '颜色详细描述，如"珍珠白金属漆"等';
COMMENT ON COLUMN vehicle_color_codes.is_defined IS '是否已定义，TRUE=预先定义的已知颜色，FALSE=系统自动发现的未知颜色';
COMMENT ON COLUMN vehicle_color_codes.first_seen IS '首次出现时间，记录该颜色代码第一次在系统中出现的时间';
COMMENT ON COLUMN vehicle_color_codes.created_at IS '记录创建时间';
COMMENT ON COLUMN vehicle_color_codes.updated_at IS '记录最后更新时间';

-- 创建触发器
CREATE TRIGGER update_vehicle_color_codes_updated_at
    BEFORE UPDATE ON vehicle_color_codes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 4. 辅助表：vehicle_platforms (车型平台字典表)
-- ============================================================
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

-- 添加索引
CREATE INDEX idx_platforms_is_defined ON vehicle_platforms(is_defined);

-- 添加表注释
COMMENT ON TABLE vehicle_platforms IS '车型平台字典表，存储平台代码与平台名称的映射关系，用于按平台统计和查询车辆';

-- 添加字段注释
COMMENT ON COLUMN vehicle_platforms.id IS '主键，自增ID';
COMMENT ON COLUMN vehicle_platforms.platform_code IS '平台代码，如MLB、MQB等，与vehicle_data.platform_code对应';
COMMENT ON COLUMN vehicle_platforms.platform_name IS '平台名称，如"MLB Evo"、"MQB"等，便于人类阅读';
COMMENT ON COLUMN vehicle_platforms.description IS '平台详细描述，如"大众MLB Evo纵置发动机模块化平台"';
COMMENT ON COLUMN vehicle_platforms.is_defined IS '是否已定义，TRUE=预先定义的已知平台，FALSE=系统自动发现的未知平台';
COMMENT ON COLUMN vehicle_platforms.first_seen IS '首次出现时间，记录该平台代码第一次在系统中出现的时间';
COMMENT ON COLUMN vehicle_platforms.created_at IS '记录创建时间';
COMMENT ON COLUMN vehicle_platforms.updated_at IS '记录最后更新时间';

-- 创建触发器
CREATE TRIGGER update_vehicle_platforms_updated_at
    BEFORE UPDATE ON vehicle_platforms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 5. 初始化数据示例（可选）
-- ============================================================

-- 预填充已知车身类型（示例数据，需要根据实际情况修改）
INSERT INTO vehicle_body_types (body_type, type_name, description, is_defined) VALUES
('VS21J', '奥迪A4L', '奥迪A4L轿车', TRUE),
('MK32A', '奥迪Q5L', '奥迪Q5L SUV', TRUE),
('BN45T', '奥迪A6L', '奥迪A6L行政轿车', TRUE);

-- 预填充已知颜色代码
INSERT INTO vehicle_color_codes (color_code, color_name, color_description, is_defined) VALUES
('2LA1', '珍珠白', '珍珠白金属漆', TRUE),
('3MB2', '极地黑', '极地黑金属漆', TRUE),
('4NC3', '天云灰', '天云灰金属漆', TRUE);

-- 预填充已知平台代码
INSERT INTO vehicle_platforms (platform_code, platform_name, description, is_defined) VALUES
('MLB', 'MLB Evo', '大众MLB Evo纵置发动机模块化平台', TRUE),
('MQB', 'MQB', '大众MQB模块化横置平台', TRUE),
('PPE', 'PPE', '保时捷-奥迪纯电平台', TRUE);
