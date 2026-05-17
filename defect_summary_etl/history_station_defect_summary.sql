-- 更新时间：2026-05-17 11:20 Asia/Shanghai
-- 主要内容：
-- 1. 将本地 history_station_defect_summary 汇总表与水位表中的 date_time / last_success_date_time 字段类型由 TIMESTAMP 变更为 TIMESTAMPTZ
-- 2. 统一带时区时间格式，规避 LLM 与多表时间关联时的时区暗坑与隐式类型转换，保障索引和逻辑安全
-- 3. 保持幂等建表、索引定义以及 model_attribute_map 初始化逻辑不变

BEGIN;

-- 强锁当前会话为上海时区，保障手动导入时时间字段在一致的时区语境下被初始化
SET TIME ZONE 'Asia/Shanghai';

CREATE TABLE IF NOT EXISTS model_attribute_map (
    model INTEGER PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    black_roof VARCHAR(100)
);

COMMENT ON TABLE model_attribute_map IS
'车型属性映射表。根据 history.model 映射出 type_name 和 black_roof，用于汇总表生成与 LLM 字段理解。';

COMMENT ON COLUMN model_attribute_map.model IS
'history.model 的车型编码，作为映射主键。';

COMMENT ON COLUMN model_attribute_map.type_name IS
'由 model 映射得到的车型名称，如 A7、Tiguan。';

COMMENT ON COLUMN model_attribute_map.black_roof IS
'由 model 映射得到的黑车顶标记。可为空；例如 黑车顶。';

-- 将 defect_database/defect_database_from_agent/model_map.json 中的映射同步到这里维护。
INSERT INTO model_attribute_map (model, type_name, black_roof)
VALUES
    (4, 'TiguanL', NULL),
    (7, 'A7', NULL),
    (19, 'Tiguan Pro', NULL),
    (20, 'A5', NULL),
    (21, 'A5', NULL),
    (22, 'A5', '黑车顶'),
    (23, 'E5', NULL),
    (25, 'TiguanL', '黑车顶'),
    (26, 'Tiguan Pro', '黑车顶'),
    (27, 'E7', NULL),
    (28, 'TiguanL PHEV', NULL),
    (77, 'A7', '黑车顶')
ON CONFLICT (model) DO UPDATE
SET
    type_name = EXCLUDED.type_name,
    black_roof = EXCLUDED.black_roof;

CREATE TABLE IF NOT EXISTS history_station_defect_summary (
    history_id INTEGER PRIMARY KEY,
    model INTEGER NOT NULL,
    type_name VARCHAR(100),
    black_roof VARCHAR(100),
    serial_number VARCHAR(255),
    date_time TIMESTAMPTZ NOT NULL,
    color_code VARCHAR(255),
    tunnel INTEGER,
    cycle INTEGER,
    station_1_defect_count INTEGER NOT NULL DEFAULT 0,
    station_2_defect_count INTEGER NOT NULL DEFAULT 0,
    station_3_defect_count INTEGER NOT NULL DEFAULT 0,
    station_4_defect_count INTEGER NOT NULL DEFAULT 0,
    station_5_defect_count INTEGER NOT NULL DEFAULT 0,
    total_defect_count INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE history_station_defect_summary IS
'缺陷检测汇总表。每个 history_id 对应一次检测记录，按 station=1~5 且 diameter>0 统计缺陷数量，并补充车型与黑车顶属性，供统计分析与 LLM 理解使用。';

COMMENT ON COLUMN history_station_defect_summary.history_id IS
'检测编号，主键，对应 history.history_id。一次检测生成一个唯一 history_id。';

COMMENT ON COLUMN history_station_defect_summary.model IS
'车型编码，对应 history.model。';

COMMENT ON COLUMN history_station_defect_summary.type_name IS
'由 model_attribute_map 根据 model 映射得到的车型名称。';

COMMENT ON COLUMN history_station_defect_summary.black_roof IS
'由 model_attribute_map 根据 model 映射得到的黑车顶标记。';

COMMENT ON COLUMN history_station_defect_summary.serial_number IS
'检测对象编号，对应 history.serial_number。';

COMMENT ON COLUMN history_station_defect_summary.date_time IS
'检测时间，对应 history.date_time。';

COMMENT ON COLUMN history_station_defect_summary.color_code IS
'颜色代码，对应 history.color_code。';

COMMENT ON COLUMN history_station_defect_summary.tunnel IS
'检测通道，对应 history.tunnel。';

COMMENT ON COLUMN history_station_defect_summary.cycle IS
'检测循环号，对应 history."CYCLE"。在汇总表中统一命名为小写 cycle，便于 SQL 使用与 LLM 理解。';

COMMENT ON COLUMN history_station_defect_summary.station_1_defect_count IS
'当前 history_id 下，history_detail 中 station=1 且 diameter>0 的记录数量。';

COMMENT ON COLUMN history_station_defect_summary.station_2_defect_count IS
'当前 history_id 下，history_detail 中 station=2 且 diameter>0 的记录数量。';

COMMENT ON COLUMN history_station_defect_summary.station_3_defect_count IS
'当前 history_id 下，history_detail 中 station=3 且 diameter>0 的记录数量。';

COMMENT ON COLUMN history_station_defect_summary.station_4_defect_count IS
'当前 history_id 下，history_detail 中 station=4 且 diameter>0 的记录数量。';

COMMENT ON COLUMN history_station_defect_summary.station_5_defect_count IS
'当前 history_id 下，history_detail 中 station=5 且 diameter>0 的记录数量。';

COMMENT ON COLUMN history_station_defect_summary.total_defect_count IS
'当前 history_id 下，station=1~5 且 diameter>0 的缺陷记录总数，等于 station_1_defect_count 到 station_5_defect_count 之和。';

CREATE INDEX IF NOT EXISTS idx_history_station_defect_summary_date_time
ON history_station_defect_summary(date_time);

CREATE INDEX IF NOT EXISTS idx_history_station_defect_summary_serial_number
ON history_station_defect_summary(serial_number);

CREATE TABLE IF NOT EXISTS history_station_defect_summary_refresh_state (
    job_name TEXT PRIMARY KEY,
    last_success_history_id INTEGER NOT NULL DEFAULT 0,
    last_success_date_time TIMESTAMPTZ NULL,
    last_run_started_at TIMESTAMPTZ NULL,
    last_run_finished_at TIMESTAMPTZ NULL,
    last_status TEXT NULL,
    last_message TEXT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE history_station_defect_summary_refresh_state IS
'history_station_defect_summary 增量刷新状态表。记录最近一次成功水位、执行时间与结果。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.job_name IS
'刷新任务名称，默认 refresh_history_station_defect_summary。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_success_history_id IS
'最近一次成功刷新时已完成的最大 history_id。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_success_date_time IS
'最近一次成功刷新对应的审计时间，便于排查。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_run_started_at IS
'最近一次执行开始时间。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_run_finished_at IS
'最近一次执行结束时间。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_status IS
'最近一次执行状态，例如 initialized / success / skipped / failed / noop。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.last_message IS
'最近一次执行的补充说明。';

COMMENT ON COLUMN history_station_defect_summary_refresh_state.updated_at IS
'状态行最后更新时间。';

CREATE TABLE IF NOT EXISTS history_station_defect_summary_refresh_log (
    id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    source_db_host TEXT NULL,
    source_db_name TEXT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ NULL,
    status TEXT NOT NULL,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    upserted_count INTEGER NOT NULL DEFAULT 0,
    batch_min_history_id INTEGER NULL,
    batch_max_history_id INTEGER NULL,
    watermark_before INTEGER NULL,
    watermark_after INTEGER NULL,
    message TEXT NULL
);

COMMENT ON TABLE history_station_defect_summary_refresh_log IS
'history_station_defect_summary 增量刷新日志表。按批次记录执行状态、候选量与水位变化。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.job_name IS
'刷新任务名称，默认 refresh_history_station_defect_summary。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.source_db_host IS
'源库主机地址。仅用于排查当前数据来源。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.source_db_name IS
'源库数据库名称。仅用于排查当前数据来源。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.started_at IS
'本次刷新开始时间。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.finished_at IS
'本次刷新结束时间。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.status IS
'本次刷新状态，例如 initialized / success / skipped / failed / noop。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.candidate_count IS
'本次批次候选 history_id 数量。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.upserted_count IS
'本次批次实际写入或更新的汇总行数。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.batch_min_history_id IS
'本次批次最小 history_id。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.batch_max_history_id IS
'本次批次最大 history_id。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.watermark_before IS
'本次批次执行前的成功水位。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.watermark_after IS
'本次批次执行后的成功水位。';

COMMENT ON COLUMN history_station_defect_summary_refresh_log.message IS
'本次批次的补充说明。';

-- 说明：
-- 1. 本文件仅负责初始化 defect_db 本地对象，不再执行全量刷新。
-- 2. 增量刷新请使用 defect_database/refresh_history_station_defect_summary.py。
-- 3. 如果源库也由本地 defect_db 承担，可考虑在源库补充以下索引提升性能：
--    CREATE INDEX IF NOT EXISTS idx_history_detail_history_id ON history_detail(history_id);
--    CREATE INDEX IF NOT EXISTS idx_history_detail_history_id_station_diameter
--    ON history_detail(history_id, station) WHERE diameter > 0;

COMMIT;
