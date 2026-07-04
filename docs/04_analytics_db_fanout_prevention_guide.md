# 分析库大模型关联去重与防错指南 (Fan-out Prevention Guide)

修改时间：2026-07-04 Asia/Shanghai

## 一、 现象 (Symptom)

在自然语言转 SQL (Text-to-SQL) 的大模型 (Agent) 应用场景中，当大模型被问及关于**“车辆数量”、“在线车数分布”或“生产合格率”**等“以车为单位”的统计问题时，大模型生成的 SQL 往往会输出明显**虚高或翻倍**的统计数值。

例如：原本某个区域只有 10 辆产品车，大模型统计出来的结果可能会是 15 辆甚至更多。

---

## 二、 原因 (Cause)

该现象的根本原因在于数仓中维度层与事实明细层之间的**一对多关系（粒度差异）**，在没有正确去重的情况下关联导致了**“扇出效应 (Fan-out Effect)”**。

具体表/视图表现如下：
1. **`dim.dim_vehicle_profile` (维度层)**：以车辆为核心，粒度是 **一车一行 (1 行 = 1 辆物理车)**。
2. **`mart.mart_vehicle_quality_360` (集市明细层)** & **`fct.fct_vehicle_defect_enriched` (事实富集层)**：
   - 这两个视图的设计粒度是 **一次缺陷检测事件 (1 行 = 1 个缺陷记录)**，而非“一辆车”。
   - 如果一辆产品车检出了 3 个不同的缺陷，那么它在这两个视图中就会拥有 3 行记录。
   - 当大模型使用 `LEFT JOIN` 将 `dim_vehicle_profile` 与这两个缺陷明细表基于 `vehicle_id` 关联时，原本维表中的 1 行记录会被展开（复制）为 3 行。如果直接执行 `COUNT(vehicle_id)` 或 `COUNT(*)`，就会将该车重复计算 3 次。

---

## 三、 分析 (Analysis)

### 1. 大模型典型易错 SQL 示例
当大模型被提问：*“目前各个工艺区域分别有多少辆正式产品车？”*

大模型为了同时获取车辆所在的区域 and 质量状态，可能会错误地编写如下查询：
```sql
-- ❌ 错误写法：直接关联缺陷明细表，导致车辆计数翻倍
SELECT 
    p.current_process_area, 
    COUNT(p.vehicle_id) as vehicle_count
FROM dim.dim_vehicle_profile p
LEFT JOIN mart.mart_vehicle_quality_360 q ON p.vehicle_id = q.vehicle_id
GROUP BY p.current_process_area;
```
**结果**：多缺陷的车辆在 `mart_vehicle_quality_360` 中存在多条记录，导致 `COUNT(p.vehicle_id)` 统计出的车数远远超出实际在线车数。

### 2. 正确的 SQL 处理范式
大模型在必须关联缺陷明细表时，应该采用以下两种防错写法之一：

#### 范式 A：使用 `DISTINCT` 显式去重
```sql
--  正确写法 A：使用 COUNT(DISTINCT) 消除多行展开的影响
SELECT 
    p.current_process_area, 
    COUNT(DISTINCT p.vehicle_id) as vehicle_count
FROM dim.dim_vehicle_profile p
LEFT JOIN mart.mart_vehicle_quality_360 q ON p.vehicle_id = q.vehicle_id
GROUP BY p.current_process_area;
```

#### 范式 B：使用子查询（CTE）预先聚合（推荐）
```sql
--  正确写法 B：通过子查询将明细表预先聚合成一车一行，再与主表做 1:1 关联
WITH vehicle_defect_summary AS (
    SELECT 
        vehicle_id, 
        COUNT(*) as defect_count
    FROM mart.mart_vehicle_quality_360
    WHERE vehicle_id IS NOT NULL
    GROUP BY vehicle_id
)
SELECT 
    p.current_process_area,
    COUNT(p.vehicle_id) as real_vehicle_count,
    SUM(COALESCE(d.defect_count, 0)) as total_defect_count
FROM dim.dim_vehicle_profile p
LEFT JOIN vehicle_defect_summary d ON p.vehicle_id = d.vehicle_id
GROUP BY p.current_process_area;
```

---

## 四、 推荐方案 (Recommendations)

为了彻底解决此问题，推荐从**数据库元数据（防错提示）**、**Agent 规则注入（行为约束）**以及**数仓结构设计（物理规避）**三个维度协同进行优化：

### 方案一：数据库中文注释级元数据注入 (低成本、快速见效)
大模型在生成 SQL 前方必定会读取表结构定义、字段及注释。我们可以将粒度与去重警示信息显式注入到 PostgreSQL 的表级与列级注释中：
- 执行以下 SQL，将警示信息直接写入数据库：
  ```sql
  -- 表级/视图级注入警示
  COMMENT ON VIEW mart.mart_vehicle_quality_360 IS 
  '完整车辆缺陷检测历史明细视图。粒度：一个缺陷事件一行。同一个 vehicle_id 会存在多条记录。若要统计车数或进行车级关联，必须使用 COUNT(DISTINCT vehicle_id) 或先进行 GROUP BY 聚合，以防出现多行展开导致车数虚高。';

  COMMENT ON VIEW fct.fct_vehicle_defect_enriched IS 
  '车身中心缺陷富集分析宽表。粒度：一个缺陷对齐事件一行。同一 vehicle_id 存在多条记录。统计车辆数量时请务必使用 DISTINCT 去重。';

  -- 列级/字段级注入警示
  COMMENT ON COLUMN ods.history_station_defect_summary.serial_number IS 
  '车身唯一识别码 (等同于 vehicle_id 和 BODY_ID，跨源一一对应)。本表为一车多缺陷明细，统计车数时须 DISTINCT！';

  COMMENT ON COLUMN fct.fct_vehicle_defect_enriched.vehicle_id IS 
  '车身唯一识别码 (主键前部)。本表为一车多缺陷明细，统计车数时须 DISTINCT！';

  COMMENT ON COLUMN mart.mart_vehicle_quality_360.vehicle_id IS 
  '车身唯一识别码。本表为一车多缺陷明细，统计车数时须 DISTINCT！';
  ```

### 方案二：面向 Agent 知识库与 Prompt 的规则约束 (行为约束)
在项目的 Agent 协作规范（如 `AGENTS.md`）或大模型的 System Prompt 中，追加如下强制防错规则：
> **【数据关联去重安全规则】**：在分析数仓中，`mart.mart_vehicle_quality_360` 与 `fct.fct_vehicle_defect_enriched` 均属于**明细事件层表**（粒度是一缺陷事件一行，同一车号存在多条记录）。
> 1. 凡是涉及“**有多少辆车**”、“**车辆分布**”、“**车辆合格率**”等车辆数量级的统计，如果关联了上述两个表，**必须**使用 `COUNT(DISTINCT vehicle_id)`。
> 2. 严禁在未做 `DISTINCT` 或未在子查询中进行 `GROUP BY` 预聚合的情况下，将维表与这两个明细表直接 `LEFT JOIN` 进行普通 `COUNT` 统计。

### 方案三：数仓结构优化——提供“一车一行”质量汇总物化视图 (根本性规避，推荐)
从源头上为大模型分流，设计并提供一个专门以 `vehicle_id` 为唯一主键的**汇总级质量物化视图**（例如 `mart.mart_vehicle_quality_summary_360`）。
- **设计结构**：
  ```sql
  CREATE MATERIALIZED VIEW mart.mart_vehicle_quality_summary_360 AS
  SELECT 
      p.vehicle_id,
      p.current_position_id,
      p.current_process_area,
      p.current_full_rb_code,
      p.current_position_updated_at,
      COALESCE(q.total_defect_count, 0) AS total_defect_count,
      CASE 
          WHEN COALESCE(q.total_defect_count, 0) = 0 THEN '合格'
          ELSE '不合格'
      END AS quality_status
  FROM dim.dim_vehicle_profile p
  LEFT JOIN (
      SELECT 
          vehicle_id, 
          COUNT(*) AS total_defect_count
      FROM ods.history_station_defect_summary
      WHERE vehicle_id IS NOT NULL
      GROUP BY vehicle_id
  ) q ON p.vehicle_id = q.vehicle_id;

  -- 建立唯一索引以支持高频检索
  CREATE UNIQUE INDEX idx_mart_vehicle_quality_summary_360_vid 
  ON mart.mart_vehicle_quality_summary_360 (vehicle_id);
  ```
- **使用规则引导**：
  当大模型需要回答“**各区域合格车数**”或“**车辆数分布**”时，直接引导它查询/关联此汇总视图，从而从结构上物理屏蔽了“一对多”的扇出错误风险。
