# Analytics DB 数据血缘关系

修改时间：2026-07-23 Asia/Shanghai

主要修改内容：
- 更新 `dim.carbody_registry` 与 `dim.dim_vehicle_profile` 的生成逻辑，追加 `retention_checkpoint_station` 和 `retention_checkpoint_pass_at` 滞留监控检查点字段。

历史修改时间：2026-05-11 Asia/Shanghai

## 概述

```
rollerbed_tracking_db ─FDW→ src_rb ──→ ods ──→ dim ──→ fct ──→ mart
                           │                      │        │        │
defect_db ──────────FDW→ src_defect ──→ ods ──────┤────────┤        │
                           │                      │        │        │
carbody_history ────FDW→ src_carbody ──→ ods ──→ dim      │        │
                           │                      │        │        │
meta ──────────────────────────────────────────────────────┴────────┘
                           (刷新水位 + 执行日志)
```

## 一、SRC 层（FDW 外部表，只读）

| schema | 外部表 | 源库 | 备注 |
|--------|--------|------|------|
| `src_rb` | `rb_position_data` | `rollerbed_tracking_db` | 98 个 RB 位置实时状态 |
| `src_rb` | `process_areas` | `rollerbed_tracking_db` | 工艺区域字典 |
| `src_rb` | `carrier_types` | `rollerbed_tracking_db` | 载体类型字典 |
| `src_rb` | `vehicle_body_types` | `rollerbed_tracking_db` | 车身类型字典 |
| `src_rb` | `vehicle_color_codes` | `rollerbed_tracking_db` | 颜色代码字典 |
| `src_rb` | `vehicle_platforms` | `rollerbed_tracking_db` | 平台代码字典 |
| `src_defect` | `history_station_defect_summary` | `defect_db` | 缺陷检测汇总 |
| `src_carbody` | `carbody_history` | `carbody_history` | 车身过站历史 |

**无下游引用对象** — 均被同名 ODS 表消费。

---

## 二、ODS 层（本地缓存表）

| 表名 | 数据来源 | 刷新方式 |
|------|----------|----------|
| `ods.rb_position_data` | `src_rb.rb_position_data` | 全量 TRUNCATE+INSERT |
| `ods.process_areas` | `src_rb.process_areas` | 全量 TRUNCATE+INSERT |
| `ods.carrier_types` | `src_rb.carrier_types` | 全量 TRUNCATE+INSERT |
| `ods.vehicle_body_types` | `src_rb.vehicle_body_types` | 全量 TRUNCATE+INSERT |
| `ods.vehicle_color_codes` | `src_rb.vehicle_color_codes` | 全量 TRUNCATE+INSERT |
| `ods.vehicle_platforms` | `src_rb.vehicle_platforms` | 全量 TRUNCATE+INSERT |
| `ods.history_station_defect_summary` | `src_defect.history_station_defect_summary` | 全量 TRUNCATE+INSERT |
| `ods.carbody_history` | `src_carbody.carbody_history` | 增量 INSERT（基于 `max("ID")` 水位） |

### 被哪些对象引用

| ODS 表 | 被下游引用 |
|--------|-----------|
| `ods.rb_position_data` | → `fct.fct_position_current_all`（直接 SELECT） |
| `ods.process_areas` | **无**（dim.dim_process_area 也引用了它，但 dim 本身的处理不涉及这个） |
| `ods.carrier_types` | → `mart.mart_vehicle_quality_360`（LEFT JOIN）<br>→ `mart.mart_abnormal_vehicle_current`（LEFT JOIN）<br>→ `mart.mart_position_current_overview`（LEFT JOIN） |
| `ods.vehicle_body_types` | → `dim.dim_vehicle_profile`（LEFT JOIN）<br>→ `mart.mart_vehicle_quality_360`（LEFT JOIN）<br>→ `mart.mart_abnormal_vehicle_current`（LEFT JOIN）<br>→ `mart.mart_position_current_overview`（LEFT JOIN） |
| `ods.vehicle_color_codes` | → `dim.dim_vehicle_profile`（LEFT JOIN）<br>→ `mart.mart_vehicle_quality_360`（LEFT JOIN）<br>→ `mart.mart_abnormal_vehicle_current`（LEFT JOIN）<br>→ `mart.mart_position_current_overview`（LEFT JOIN） |
| `ods.vehicle_platforms` | → `dim.dim_vehicle_profile`（LEFT JOIN）<br>→ `mart.mart_vehicle_quality_360`（LEFT JOIN）<br>→ `mart.mart_abnormal_vehicle_current`（LEFT JOIN）<br>→ `mart.mart_position_current_overview`（LEFT JOIN） |
| `ods.history_station_defect_summary` | → `dim.dim_vehicle_profile`（latest_defect CTE）<br>→ `fct.fct_vehicle_defect_detection`（直接 SELECT）<br>→ `fct.fct_vehicle_defect_enriched`（LEFT JOIN） |
| `ods.carbody_history` | → `dim.carbody_registry`（增量 UPSERT 聚合） |

---

## 三、DIM 层（维度表）

| 表名 | 数据来源 | 刷新方式 |
|------|----------|----------|
| `dim.dim_process_area` | `ods.process_areas` | 全量 INSERT（refresh_analytics_all 中重建） |
| `dim.dim_vehicle_profile` | `fct.fct_vehicle_position_current`（tracking 侧）<br>+ `ods.history_station_defect_summary`（defect 侧）<br>+ `dim.carbody_registry`（carbody 侧）<br>→ `vehicle_union` = tracking ∪ defect ∪ carbody → COALESCE 合并 | 全量 TRUNCATE+INSERT |
| `dim.carbody_registry` | `ods.carbody_history`（增量批次聚合） | 增量 UPSERT（ON CONFLICT DO UPDATE） |

### dim.dim_vehicle_profile 的合并逻辑

```
vehicle_union (tracking ∪ defect ∪ carbody)
    │
    ├── latest_tracking CTE ← fct.fct_vehicle_position_current
    │     vehicle_id, body_type, color_code, platform_code,
    │     black_roof_flag, position_id, carrier_id, process_area
    │
    ├── latest_defect CTE ← ods.history_station_defect_summary
    │     vehicle_id, model, type_name, black_roof, defect_last_seen_at
    │     (DISTINCT ON trim(serial_number) ORDER BY date_time DESC)
    │
    └── latest_carbody CTE ← dim.carbody_registry
          vehicle_id, body_type, platform_code, color_code, black_roof_flag, rework_flag,
          first_seen_at, last_seen_at, first_rw_station, last_rw_station, station_pass_count,
          retention_checkpoint_station, retention_checkpoint_pass_at
    
    → LEFT JOIN tracking + LEFT JOIN defect + LEFT JOIN carbody
    → COALESCE(t.color_code, d.defect_color_code, c.color_code) AS color_code
    → CASE is_black_roof: tracking '1/Y/T' OR defect ILIKE '%黑%' OR carbody '1/Y/T'
    → 透传 retention_checkpoint_station 与 retention_checkpoint_pass_at
    → LEFT JOIN ods.vehicle_body_types / vehicle_color_codes / vehicle_platforms
      做代码→名称翻译
```

### 被哪些对象引用

| DIM 表 | 被下游引用 |
|--------|-----------|
| `dim.dim_process_area` | → `mart.mart_abnormal_vehicle_current`（LEFT JOIN）<br>→ `mart.mart_position_current_overview`（LEFT JOIN） |
| `dim.dim_vehicle_profile` | **无人引用**（独立冗余查询表） |
| `dim.carbody_registry` | → `fct.fct_vehicle_defect_enriched`（LEFT JOIN 驱动表） |

---

## 四、FCT 层（物化视图）

| 物化视图 | 数据来源 | 过滤条件 |
|----------|----------|----------|
| `fct.fct_position_current_all` | `ods.rb_position_data` | `carrier_id <> '0'` |
| `fct.fct_vehicle_position_current` | `fct.fct_position_current_all` | `entity_type = 'product_vehicle'` AND `vehicle_id LIKE '782026%'` |
| `fct.fct_vehicle_defect_detection` | `ods.history_station_defect_summary` | `serial_number IS NOT NULL` |
| `fct.fct_vehicle_defect_enriched` | `dim.carbody_registry` (驱动)<br>+ `ods.history_station_defect_summary` | 无过滤（LEFT JOIN 保留全量车身） |
| `fct.fct_abnormal_vehicle_current` | `fct.fct_position_current_all` | `entity_type = 'abnormal_vehicle'` |

### 被哪些对象引用

| FCT 物化视图 | 被下游引用 |
|-------------|-----------|
| `fct.fct_position_current_all` | → `fct.fct_vehicle_position_current`（WHERE product_vehicle）<br>→ `fct.fct_abnormal_vehicle_current`（WHERE abnormal_vehicle）<br>→ `mart.mart_position_current_overview`（LEFT JOIN）<br>→ `dim.dim_vehicle_profile`（latest_tracking CTE 间接，通过 fct_vehicle_position_current） |
| `fct.fct_vehicle_position_current` | → `dim.dim_vehicle_profile`（latest_tracking CTE）<br>→ `mart.mart_vehicle_quality_360`（LEFT JOIN p.vehicle_id = d.vehicle_id） |
| `fct.fct_vehicle_defect_detection` | → `mart.mart_vehicle_quality_360`（FROM 主表） |
| `fct.fct_abnormal_vehicle_current` | → `mart.mart_abnormal_vehicle_current`（FROM 主表）<br>→ `mart.mart_position_current_overview`（LEFT JOIN a.position_id = p.position_id） |

---

## 五、MART 层（物化视图 — 终端查询入口）

| 物化视图 | 数据来源 |
|----------|----------|
| `mart.mart_vehicle_quality_360` | `fct.fct_vehicle_defect_enriched` e (包含缺陷与车身履历/滞留检查点)<br>LEFT JOIN `fct.fct_vehicle_position_current` p<br>LEFT JOIN `ods.carrier_types`<br>LEFT JOIN `ods.vehicle_body_types`<br>LEFT JOIN `ods.vehicle_color_codes`<br>LEFT JOIN `ods.vehicle_platforms` |
| `mart.mart_abnormal_vehicle_current` | `fct.fct_abnormal_vehicle_current` a<br>LEFT JOIN `dim.dim_process_area`<br>LEFT JOIN `ods.carrier_types`<br>LEFT JOIN `ods.vehicle_body_types`<br>LEFT JOIN `ods.vehicle_color_codes`<br>LEFT JOIN `ods.vehicle_platforms` |
| `mart.mart_position_current_overview` | `fct.fct_position_current_all` p<br>LEFT JOIN `fct.fct_abnormal_vehicle_current` a<br>LEFT JOIN `dim.dim_process_area`<br>LEFT JOIN `ods.carrier_types`<br>LEFT JOIN `ods.vehicle_body_types`<br>LEFT JOIN `ods.vehicle_color_codes`<br>LEFT JOIN `ods.vehicle_platforms` |

**MART 层无下游引用** — 终端分析入口，直接供 SQL Agent 查询。

---

## 六、META 层（ETL 元数据）

| 表名 | 用途 | 被谁写入 |
|------|------|----------|
| `meta.sync_job_log` | 刷新执行日志 | `meta.refresh_analytics_all()` / `meta.refresh_carbody()` |
| `meta.refresh_watermark` | 增量刷新水位 | `meta.refresh_analytics_all()` / `meta.refresh_carbody()` |

---

## 七、完整依赖图（缩进 = 依赖深度）

```
rollerbed_tracking_db (外部数据库)
└── src_rb.rb_position_data
    └── ods.rb_position_data ───────→ fct.fct_position_current_all
        ├──→ fct.fct_vehicle_position_current ──────────────────────
        │    ├──→ dim.dim_vehicle_profile (latest_tracking CTE)     │
        │    └──→ mart.mart_vehicle_quality_360                     │
        ├──→ fct.fct_abnormal_vehicle_current ──────────────────────┤
        │    ├──→ mart.mart_abnormal_vehicle_current                 │
        │    └──→ mart.mart_position_current_overview               │
        └──→ mart.mart_position_current_overview                    │
                                                                    │
src_rb.process_areas ─→ ods.process_areas ─→ dim.dim_process_area ──┤
    └──→ mart.mart_abnormal_vehicle_current                          │
    └──→ mart.mart_position_current_overview                        │
                                                                    │
src_rb.carrier_types ─→ ods.carrier_types ──────────────────────────┤
    └──→ mart.mart_vehicle_quality_360                               │
    └──→ mart.mart_abnormal_vehicle_current                         │
    └──→ mart.mart_position_current_overview                        │
                                                                    │
src_rb.vehicle_body_types ─→ ods.vehicle_body_types ────────────────┤
    ├──→ dim.dim_vehicle_profile                                    │
    └──→ mart.mart_vehicle_quality_360                               │
    └──→ mart.mart_abnormal_vehicle_current                         │
    └──→ mart.mart_position_current_overview                        │
                                                                    │
src_rb.vehicle_color_codes ─→ ods.vehicle_color_codes ──────────────┤
    ├──→ dim.dim_vehicle_profile                                    │
    └──→ mart.mart_vehicle_quality_360                               │
    └──→ mart.mart_abnormal_vehicle_current                         │
    └──→ mart.mart_position_current_overview                        │
                                                                    │
src_rb.vehicle_platforms ─→ ods.vehicle_platforms ──────────────────┤
    ├──→ dim.dim_vehicle_profile                                    │
    └──→ mart.mart_vehicle_quality_360                               │
    └──→ mart.mart_abnormal_vehicle_current                         │
    └──→ mart.mart_position_current_overview                        │
                                                                    │
defect_db (外部数据库)                                               │
└── src_defect.history_station_defect_summary ──────────────────────┤
    └── ods.history_station_defect_summary                          │
        ├──→ dim.dim_vehicle_profile (latest_defect CTE)           │
        ├──→ fct.fct_vehicle_defect_detection ──────────────────────┤
        │    └──→ mart.mart_vehicle_quality_360                    │
        └──→ fct.fct_vehicle_defect_enriched                       │
                                                                    │
carbody_history (外部数据库)                                         │
└── src_carbody.carbody_history                                      │
    └── ods.carbody_history (增量) ──────────────────────────────────│
         └── dim.carbody_registry (增量 UPSERT) ─────────────┤
              └──→ fct.fct_vehicle_defect_enriched (LEFT JOIN 驱动)  │
```

---

## 八、刷新过程的影响范围

### `meta.refresh_analytics_all()` — 全量刷新

```
TRUNCATE → INSERT INTO ods.* (7 张表)
    ├── REFRESH MATERIALIZED VIEW fct.fct_position_current_all
    │   ├── REFRESH MATERIALIZED VIEW fct.fct_vehicle_position_current
    │   │   └── INSERT INTO dim.dim_vehicle_profile (latest_tracking CTE)
    │   ├── REFRESH MATERIALIZED VIEW fct.fct_abnormal_vehicle_current
    │   │   ├── REFRESH MATERIALIZED VIEW mart.mart_abnormal_vehicle_current
    │   │   └── REFRESH MATERIALIZED VIEW mart.mart_position_current_overview
    │   └── REFRESH MATERIALIZED VIEW mart.mart_position_current_overview
    ├── REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_detection
    │   └── REFRESH MATERIALIZED VIEW mart.mart_vehicle_quality_360
    ├── REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched
    ├── INSERT INTO dim.dim_process_area
    └── INSERT INTO dim.dim_vehicle_profile (vehicle_union = latest_tracking ∪ latest_defect)
```

### `meta.refresh_carbody()` — 增量刷新

```
ods.carbody_history 增量 INSERT（WHERE "ID" > v_last_id）
    └── dim.carbody_registry 增量 UPSERT（ON CONFLICT DO UPDATE）
```

---

## 九、关键发现

1. **`dim.dim_vehicle_profile` 无人引用** — 它是一个冗余聚合的便捷查询表，下游 fct/mart 不依赖它。修改它不影响其他对象。

2. **`dim.carbody_registry` 被 `fct.fct_vehicle_defect_enriched` 引用** — 它不再是孤立表，而是作为全量分析宽表的驱动表，将车身档案与缺陷事件关联。

3. **FCT 是中间枢纽** — `fct_position_current_all` 是引用最密集的物化视图，被 3 个下游对象依赖，修改其结构会影响：
   - `fct.fct_vehicle_position_current`
   - `fct.fct_abnormal_vehicle_current`
   - `mart.mart_position_current_overview`

4. **MART 是终端** — 所有 mart 物化视图无下游依赖，可以直接修改或新增。

5. **字典表广泛引用** — `ods.vehicle_body_types`、`ods.vehicle_color_codes`、`ods.vehicle_platforms` 被多个 mart view 引用，修改其结构需谨慎。
