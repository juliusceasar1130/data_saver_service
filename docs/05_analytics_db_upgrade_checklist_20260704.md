# Analytics DB 服务器升级备忘清单 (2026-07-04)

本清单用于记录 2026-07-04 数据库升级中所有结构发生变动的表、物化视图及存储过程，供后期更新服务器生产数据库时参考和一键执行。

---

## 1. 变更对象一览表

| 模式与名称 (Schema & Object) | 类型 (Type) | 变更类型 (Action) | 具体变更要点说明 |
| :--- | :--- | :--- | :--- |
| **`dim.dim_vehicle_profile`** | 物理表 (Table) | 重建 (DROP & CREATE) | **结构升级**：新增 9 个字段（重工标志 `is_rework`、缺陷关联标志 `has_defect_record`、物理过站读写站时间/编码/过站次数及 MDS 备用列），并新增 2 个优化查询索引。 |
| **`mart.mart_vehicle_quality_360`** | 物化视图 (Mat View) | 重建 (DROP & CREATE) | **逻辑升级**：驱动表由纯缺陷事实表改为以车身为中心的 `fct.fct_vehicle_defect_enriched`。新增支持了“在产未检车辆”及“漏检车辆”的呈现；重构了配套的唯一索引。 |
| **`meta.refresh_analytics_all()`** | 存储过程 (Procedure) | 覆盖 (CREATE OR REPLACE) | **数据流重构**：刷新管线数据装载部分引入了车身历史 `latest_carbody` CTE。并集车辆主键从 2 源扩展到 3 源并集，在画像表和 360 度集市视图装载时使用 `COALESCE` 级联填充属性。 |
| **`docs/03_analytics_db_comments.sql`** | 注释脚本 (SQL Script) | 全量运行 (Re-run) | **元数据规范**：追加了上述表和视图新增 15 个字段的列级注释，并在全局范围内将“过读写站”等历史表述全部规整对齐为“过站读写站”。 |

---

## 2. 服务器更新一键执行脚本 (Upgrade Script)

请在连接到服务器的 `analytics_db` 数据库后，使用 `root` 权限一键复制运行以下 SQL：

```sql
-- ===================================================================
-- STEP 1: 销毁旧依赖对象 (仅销毁有结构变动的对象)
-- ===================================================================
DROP MATERIALIZED VIEW IF EXISTS mart.mart_vehicle_quality_360;
DROP TABLE IF EXISTS dim.dim_vehicle_profile;

-- ===================================================================
-- STEP 2: 重建升级后的 dim_vehicle_profile 表
-- ===================================================================
CREATE TABLE IF NOT EXISTS dim.dim_vehicle_profile (
  vehicle_id VARCHAR(255) PRIMARY KEY,              -- 车辆唯一识别码
  body_type VARCHAR(5),                              -- 车型代码（优先滚床，其次车身）
  tracking_type_name VARCHAR(100),                   -- 车型中文名（由 body_type 关联字典翻译）
  defect_model INTEGER,                              -- 最新缺陷检测型号
  defect_type_name VARCHAR(100),                     -- 最新缺陷检测类型名
  platform_code VARCHAR(10),                         -- 平台代码
  platform_name VARCHAR(50),                         -- 平台中文名
  color_code VARCHAR(255),                           -- 颜色代码（优先滚床，其次缺陷，再次车身）
  color_name VARCHAR(50),                            -- 颜色中文名
  is_black_roof BOOLEAN,                             -- 是否双色车顶（滚床黑顶或缺陷包含“黑”或车身黑顶）
  is_rework BOOLEAN,                                 -- 是否重工车（根据车身重工标记 rework_flag 计算）
  has_defect_record BOOLEAN,                         -- 是否存在缺陷检测记录
  black_roof_raw_tracking VARCHAR(32),               -- 滚床原始黑车顶标记
  black_roof_raw_defect VARCHAR(100),                -- 缺陷系统原始黑车顶标记
  tracking_last_seen_at TIMESTAMPTZ,                 -- 滚床系统最后看到时间
  defect_last_seen_at TIMESTAMPTZ,                   -- 缺陷系统最后检测时间
  
  -- ===== 物理车身过站汇总属性 (源自 dim.carbody_registry) =====
  carbody_first_seen_at TIMESTAMPTZ,                 -- 首次过站读写站时间
  carbody_last_seen_at TIMESTAMPTZ,                  -- 末次过站读写站时间
  carbody_first_rw_station VARCHAR(64),              -- 首次过站读写站编码
  carbody_last_rw_station VARCHAR(64),               -- 末次过站读写站编码
  carbody_station_pass_count INTEGER,                -- 累计过站读写站总频次
  carbody_reserved_1 VARCHAR(1),                     -- 车身 MDS 备用字段 1
  carbody_reserved_2 VARCHAR(1),                     -- 车身 MDS 备用字段 2
  
  current_position_id BIGINT,                        -- 当前最新占位位置 ID
  current_carrier_id VARCHAR(50),                    -- 当前最新载体卡号
  current_carrier_type VARCHAR(20),                  -- 当前最新载体类型
  current_process_area VARCHAR(50),                  -- 当前最新工艺区域
  current_full_rb_code VARCHAR(255),                 -- 当前最新位置全编码
  current_position_updated_at TIMESTAMPTZ,           -- 当前位置最后更新时间
  etl_loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()   -- 画像数据装载时间
);

-- 重建表索引
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_type_name ON dim.dim_vehicle_profile(defect_type_name, tracking_type_name);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_color_code ON dim.dim_vehicle_profile(color_code);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_platform_code ON dim.dim_vehicle_profile(platform_code);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_current_carrier_id ON dim.dim_vehicle_profile(current_carrier_id);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_current_process_area ON dim.dim_vehicle_profile(current_process_area);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_is_rework ON dim.dim_vehicle_profile(is_rework);
CREATE INDEX IF NOT EXISTS idx_dim_vehicle_profile_has_defect ON dim.dim_vehicle_profile(has_defect_record);

-- ===================================================================
-- STEP 3: 重建升级后的 mart_vehicle_quality_360 物化视图 (改用车身富集表驱动)
-- ===================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mart_vehicle_quality_360 AS
SELECT
  e.history_id,
  e.vehicle_id,
  e.detect_time,
  e.defect_model,
  e.defect_type_name,
  e.defect_black_roof,
  e.defect_color_code,
  e.tunnel,
  e.cycle,
  e.station_1_defect_count,
  e.station_2_defect_count,
  e.station_3_defect_count,
  e.station_4_defect_count,
  e.station_5_defect_count,
  e.total_defect_count,
  e.has_defect_record,

  e.body_type,
  bt.type_name AS tracking_type_name,
  e.color_code AS tracking_color_code,
  cc.color_name AS tracking_color_name,
  e.platform_code,
  vp.platform_name,
  e.black_roof_flag,
  e.rework_flag,
  e.first_seen_at AS carbody_first_seen_at,
  e.last_seen_at AS carbody_last_seen_at,
  e.first_rw_station AS carbody_first_rw_station,
  e.last_rw_station AS carbody_last_rw_station,
  e.station_pass_count AS carbody_station_pass_count,

  p.process_area,
  p.plc,
  p.rb_index,
  p.full_rb_code,
  p.carrier_id,
  p.carrier_type,
  ct.type_name_cn AS carrier_type_name_cn,
  p.position_created_at,
  p.vehicle_updated_at
FROM fct.fct_vehicle_defect_enriched e
LEFT JOIN fct.fct_vehicle_position_current p ON p.vehicle_id = e.vehicle_id
LEFT JOIN ods.carrier_types ct ON ct.type_code = p.carrier_type
LEFT JOIN ods.vehicle_body_types bt ON bt.body_type = e.body_type
LEFT JOIN ods.vehicle_color_codes cc ON cc.color_code = e.color_code
LEFT JOIN ods.vehicle_platforms vp ON vp.platform_code = e.platform_code
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_unique ON mart.mart_vehicle_quality_360(vehicle_id, COALESCE(history_id, -1));
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_vehicle_id ON mart.mart_vehicle_quality_360(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_detect_time ON mart.mart_vehicle_quality_360(detect_time);
CREATE INDEX IF NOT EXISTS idx_mart_vehicle_quality_360_process_area ON mart.mart_vehicle_quality_360(process_area);

-- ===================================================================
-- STEP 4: 覆盖一键刷新存储过程 (详情见 00 架构手册 7.1 节)
-- ===================================================================
-- （由于 meta.refresh_analytics_all 代码过长，请从 00 手册 L1262 复制并在此处运行）

-- ===================================================================
-- STEP 5: 注入新字段元数据注释 (详情见 03 注释脚本)
-- ===================================================================
-- （请直接在此处粘贴并运行 docs/03_analytics_db_comments.sql 脚本的全部内容）

-- ===================================================================
-- STEP 6: 触发数据全量装载 (耗时 1-2 秒)
-- ===================================================================
CALL meta.refresh_analytics_all();
```

---

## 3. 服务器升级后的校验命令 (Smoke Tests)

服务器升级并刷新后，在数据库中执行以下查询以验证升级完整度：

```sql
-- 验证 1：查看是否存在“未检测且已下线”的历史车辆，有结果则说明三源合并已生效，未遗漏漏检车
SELECT vehicle_id, tracking_type_name, carbody_first_rw_station, carbody_last_rw_station, carbody_station_pass_count 
FROM dim.dim_vehicle_profile 
WHERE has_defect_record = FALSE AND current_position_id IS NULL 
LIMIT 5;

-- 验证 2：检查 360 画像质量视图中是否包含未检测的漏检车，且 has_defect_record 为 false
SELECT vehicle_id, detect_time, has_defect_record, total_defect_count 
FROM mart.mart_vehicle_quality_360 
WHERE has_defect_record = FALSE 
LIMIT 5;

-- 验证 3：验证元数据注释是否已注入
SELECT 
    col_description(a.attrelid, a.attnum) AS column_comment
FROM pg_class c
JOIN pg_attribute a ON a.attrelid = c.oid
WHERE c.relname = 'dim_vehicle_profile' AND a.attname = 'is_rework';
```
