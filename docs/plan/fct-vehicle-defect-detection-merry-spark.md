# 新建 `fct.fct_vehicle_defect_enriched` 物化视图方案

> 最后更新：2026-05-12 20:51 Asia/Shanghai（根据评审建议优化：去除 trim()、补充 UNIQUE INDEX、明确刷新位置、补充验证 SQL、补充血缘遗漏项）

## 1. 背景

### 1.1 现有数据对象

| 对象 | 性质 | 覆盖范围 | 粒度 | 车身属性来源 |
|------|------|---------|------|-------------|
| `dim.carbody_registry` | 维度表（权威车辆档案） | **全集**：所有过站车身（含未检测、待检测） | 1 车 1 行 | MDS_DATA 7 字段（PLC/MDS 系统权威写入） |
| `ods.history_station_defect_summary` | ODS 事实表 | **子集**：仅检测成功的记录 | 1 次检测 1 行 | defect 检测系统独立识别（model、type_name、black_roof、color_code） |
| `fct.fct_vehicle_defect_detection` | 物化视图（现状） | 同缺陷表子集 | 1 次检测 1 行 | = defect 侧，仅做了字段重命名（无 JOIN、无聚合） |
| `mart.mart_vehicle_quality_360` | 物化视图（现状） | 同缺陷表子集 | N 行/车（多次检测） | defect 侧 + 当前位置（fct_vehicle_position_current）+ 字典表 |

### 1.2 现有架构的问题

1. **`fct_vehicle_defect_detection` 实质上是 `history_station_defect_summary` 的轻量重命名**，无 JOIN、无聚合、无新信息，作为 fct 层的价值有限。
2. **车身属性来源不可靠**：defect 系统的 `model`、`type_name`、`color_code` 来自检测系统的独立识别，与 PLC/MDS 系统（`carbody_registry`）可能口径不一致。carbody 侧应为权威来源。
3. **缺少车身维度字段**：defect 侧没有 `body_type`（车身类型代码）、`platform_code`（平台代码）、`rework_flag`（返工标志）等 carbody 侧已有的字段。
4. **无法看到"未检测/检测失败"的车身**：`history_station_defect_summary` 只记录成功检测，经过检测站但失败的车辆不存在于当前链路中。

### 1.3 `dim.carbody_registry` 的关键特性

- 每车一行（PK: `vehicle_id`），包含完整过站档案
- MDS_DATA 提取的 7 个字段：`body_type`、`platform_code`、`color_code`、`black_roof_flag`、`rework_flag`、`reserved_1`、`reserved_2`
- 首/末过站信息：`first_seen_at`、`last_seen_at`、`first_rw_station`、`last_rw_station`、`station_pass_count`
- 由 `meta.refresh_carbody()` 增量 UPSERT 维护（独立于 `refresh_analytics_all()`）

## 2. 需求

- 以 `dim.carbody_registry` 为驱动表（权威车身维度）
- LEFT JOIN 缺陷检测记录（`ods.history_station_defect_summary`）
- **事件粒度**：一辆车有 N 次检测 → N 行，每行携带完整的 carbody 档案属性
- 无检测记录的车身保留 1 行，缺陷字段为 NULL（可识别漏检）
- 保持 `fct_vehicle_defect_detection` 和 `mart_vehicle_quality_360` **不做任何修改**
- 为 LLM 提供灵活的分析能力：可向上聚合（车型平均缺陷走势）、可向下钻取（某台车历次检测明细）、可覆盖分析（哪些车没有缺陷记录）

## 3. 方案

### 3.1 新建物化视图 `fct.fct_vehicle_defect_enriched`

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS fct.fct_vehicle_defect_enriched AS
SELECT
  -- ===== carbody 权威车身维度（驱动表）=====
  cvp.vehicle_id,
  cvp.body_type,              -- MDS_DATA 45-49 位
  cvp.platform_code,          -- MDS_DATA 51-53 位
  cvp.color_code,             -- MDS_DATA 59-62 位（carbody 权威，defect 侧用 COALESCE 兜底）
  cvp.black_roof_flag,        -- MDS_DATA 137 位（'1'/'0' 标准编码）
  cvp.rework_flag,            -- MDS_DATA 139 位
  cvp.reserved_1,             -- MDS_DATA 138 位
  cvp.reserved_2,             -- MDS_DATA 140 位
  -- carbody 过站档案
  cvp.first_seen_at,
  cvp.last_seen_at,
  cvp.first_rw_station,
  cvp.last_rw_station,
  cvp.first_body_type,
  cvp.last_body_type,
  cvp.station_pass_count,

  -- ===== 缺陷检测事件（可为 NULL）=====
  d.history_id,
  d.model                     AS defect_model,
  d.type_name                 AS defect_type_name,
  d.black_roof                AS defect_black_roof,
  d.color_code                AS defect_color_code,     -- defect 侧原始值（保留用于对比）
  d.date_time                 AS detect_time,
  d.tunnel,
  d.cycle,
  d.station_1_defect_count,
  d.station_2_defect_count,
  d.station_3_defect_count,
  d.station_4_defect_count,
  d.station_5_defect_count,
  d.total_defect_count,

  -- ===== 检测覆盖标记 =====
  CASE WHEN d.history_id IS NOT NULL THEN TRUE ELSE FALSE END AS has_defect_record

FROM dim.carbody_registry cvp
LEFT JOIN ods.history_station_defect_summary d
  ON cvp.vehicle_id = d.serial_number
  AND d.serial_number <> ''
WITH NO DATA;

-- 注：serial_number 字段假定已在数据入库时完成清洗（无前后空格），
--     如实际存在脏数据需提前在 ODS 入库环节做 trim 处理，而非在 JOIN 时。
```

### 3.2 关键设计决策

| 决策 | 说明 |
|------|------|
| **驱动表 = carbody** | 以权威车身维度为中心，而非以缺陷事件为中心 |
| **JOIN 条件过滤在 ON 中而非 WHERE** | `AND d.serial_number <> ''` 放 ON 条件中，确保无检测记录的车身不被过滤掉 |
| **不使用 trim()** | serial_number 应在 ODS 入库时完成清洗，JOIN 层避免使用函数以防索引失效 |
| **颜色代码双字段保留** | `cvp.color_code`（carbody 权威）+ `d.color_code AS defect_color_code`（defect 侧原始值），供 LLM 自行判断或对比 |
| **黑顶标志双字段保留** | 同上原因，carbody 侧是 '1'/'0' 标准编码，defect 侧可能是文本描述 |
| **has_defect_record 标记** | 方便直接回答"哪些车没有检测记录" |
| **不包含位置信息** | 按用户要求，暂不涉及检测时位置匹配 |

### 3.3 索引

```sql
CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_vehicle_id
ON fct.fct_vehicle_defect_enriched(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_detect_time
ON fct.fct_vehicle_defect_enriched(detect_time);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_body_type
ON fct.fct_vehicle_defect_enriched(body_type);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_history_id
ON fct.fct_vehicle_defect_enriched(history_id);

CREATE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_has_defect
ON fct.fct_vehicle_defect_enriched(has_defect_record);

-- UNIQUE INDEX：支持 REFRESH MATERIALIZED VIEW CONCURRENTLY（刷新期间不阻塞读查询）
-- has_defect_record=TRUE 时 history_id 唯一；FALSE 时 history_id 为 NULL，以 -1 代入
CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_vehicle_defect_enriched_unique
ON fct.fct_vehicle_defect_enriched(vehicle_id, COALESCE(history_id, -1));
```

### 3.4 刷新集成

该物化视图依赖两个独立刷新过程：
- `meta.refresh_analytics_all()` — 提供 `ods.history_station_defect_summary`
- `meta.refresh_carbody()` — 提供 `dim.carbody_registry`

**刷新方式**：在 `meta.refresh_analytics_all()` 中，精确插入位置为：
- **在** `REFRESH MATERIALIZED VIEW mart.mart_position_current_overview;` 之后
- **在** `INSERT INTO meta.refresh_watermark` 之前

```sql
-- 插入位置示意（refresh_analytics_all 过程内部）
REFRESH MATERIALIZED VIEW mart.mart_position_current_overview;  -- 已有行
REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched;      -- 新增行
INSERT INTO meta.refresh_watermark ...;                          -- 已有行
```

> **说明**：如果后续补充了 UNIQUE INDEX（见 3.3），建议改用 `REFRESH MATERIALIZED VIEW CONCURRENTLY fct.fct_vehicle_defect_enriched;` 以避免刷新期间的排他锁阻塞查询。

**时序依赖**：`refresh_carbody()` 应在此次 `refresh_analytics_all()` 之前完成一次执行。现有调度频率（carbody 每 5 分钟、analytics 每 15-30 分钟）满足此条件。

## 4. 典型 LLM 查询示例

```sql
-- Q: 7820260100492 这台车有几个缺陷？
SELECT vehicle_id, count(*) AS detection_count,
       sum(total_defect_count) AS total_defects
FROM fct.fct_vehicle_defect_enriched
WHERE vehicle_id = '7820260100492'
  AND has_defect_record
GROUP BY vehicle_id;

-- Q: 车型 4FB2E 每月平均缺陷走势？
SELECT date_trunc('month', detect_time) AS month,
       body_type,
       avg(total_defect_count)::numeric(10,2) AS avg_defects,
       count(*) AS detection_count
FROM fct.fct_vehicle_defect_enriched
WHERE has_defect_record
  AND body_type = '4FB2E'
GROUP BY month, body_type
ORDER BY month;

-- Q: 哪些车没有缺陷检测记录？
SELECT vehicle_id, body_type, first_seen_at, last_seen_at
FROM fct.fct_vehicle_defect_enriched
WHERE NOT has_defect_record
ORDER BY first_seen_at DESC;

-- Q: 最近一次检测明细（按车型）
SELECT vehicle_id, body_type, detect_time,
       total_defect_count, station_1_defect_count, station_2_defect_count
FROM fct.fct_vehicle_defect_enriched
WHERE has_defect_record
  AND body_type = '4FB2E'
ORDER BY detect_time DESC
LIMIT 10;
```

## 5. 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `defect_database/database_refactor/analytics_db_architecture.md` | 1) 6.5 节新增 DDL（物化视图 + 索引，含 UNIQUE INDEX）<br>2) 第 2 节 schema 列表补充 `fct.fct_vehicle_defect_enriched`<br>3) 第 7 节 `refresh_analytics_all()` 精确插入位置（mart 刷新之后、watermark 写入之前）<br>4) 9.2 验证 SQL 补充 count 检查 + 属性一致性检查<br>5) 6.6 授权补充新视图<br>6) 更新 changelog 修订记录 |
| `defect_database/database_refactor/analytics_db_data_lineage.md` | 1) 四、FCT 层表格新增 `fct_vehicle_defect_enriched`<br>2) 七、完整依赖图补充新视图节点<br>3) 八、刷新影响范围补充新视图<br>4) **第二节 ODS 层**：`ods.history_station_defect_summary` 被引用关系追加 `→ fct.fct_vehicle_defect_enriched`<br>5) **第三节 DIM 层**：`dim.carbody_registry` 从"无人引用"改为"→ `fct.fct_vehicle_defect_enriched`（LEFT JOIN 驱动表）"<br>6) **第九节关键发现**：第 2 点更新，`dim.carbody_registry` 不再是"无人引用" |

## 6. 验证方法

### 6.1 基础验证
```sql
-- 行数应 >= dim.carbody_registry（至少 1 行/车）
SELECT count(*) FROM fct.fct_vehicle_defect_enriched;

-- has_defect_record 分布
SELECT has_defect_record, count(*) FROM fct.fct_vehicle_defect_enriched
GROUP BY has_defect_record;

-- 验证无检测记录的车身（缺陷字段应为 NULL）
SELECT * FROM fct.fct_vehicle_defect_enriched
WHERE NOT has_defect_record LIMIT 10;

-- 验证有多次检测的车身（应有多行，carbody 属性一致）
SELECT vehicle_id, count(*) FROM fct.fct_vehicle_defect_enriched
WHERE has_defect_record
GROUP BY vehicle_id HAVING count(*) > 1 LIMIT 10;
```

### 6.2 对比验证
```sql
-- fct_vehicle_defect_detection 行数（现状，未修改）应与 enriched 中 has_defect_record=true 的行数一致
SELECT (SELECT count(*) FROM fct.fct_vehicle_defect_detection) AS old_count,
       (SELECT count(*) FROM fct.fct_vehicle_defect_enriched WHERE has_defect_record) AS new_count;
```

### 6.3 属性一致性验证
```sql
-- 验证：同一车身的多行检测记录中，carbody 权威属性应完全一致
-- 期望结果：0 行（carbody 侧每车一行，属性不应因 JOIN 产生分裂）
SELECT vehicle_id,
       count(DISTINCT body_type)  AS body_type_cnt,
       count(DISTINCT color_code) AS color_code_cnt
FROM fct.fct_vehicle_defect_enriched
WHERE has_defect_record
GROUP BY vehicle_id
HAVING count(DISTINCT body_type) > 1
    OR count(DISTINCT color_code) > 1;
```
