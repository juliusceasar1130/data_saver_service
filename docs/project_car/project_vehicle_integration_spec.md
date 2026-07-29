# 项目车数据集成与 Analytics DB 匹配技术规格书 (Technical Specification)

修改时间：2026-07-28 16:30 Asia/Shanghai

主要修改内容：
- 取消旧版模糊降级兼容，严格采用 13 位复合 PIN (`LEFT(cr.vehicle_id, 13) = pvo.composite_pin_no`) 进行项目车编号精确匹配。
- 补齐 ODS 贴源表 `ods.ods_fis_project_vehicle_orders` 的主键约束 (`PRIMARY KEY (project_vehicle_no)`) 规范与存储过程 UPSERT 同步逻辑。
- 对齐存储过程 `meta.refresh_carbody_dim()` 与 `meta.refresh_analytics_all()` 的最新刷新流程。

---

## 1. 架构目标与解耦原则 (Architecture Goals & Principles)

### 1.1 业务背景
FIS (Factory Information System) 解析自动化服务负责扫描并抽取 Word 格式生产通知单中的项目车明细（包含项目阶段、Block、6位代码、外色内饰、KOM、KNR、PIN、项目车编号等）。为实现生产现场物理车身过站、滚床追踪、质量缺陷与项目车属性的联动分析，需要将 FIS 提取的数据与 `analytics_db` 数仓进行高效打通。

### 1.2 架构解耦原则
1. **源库与数仓解耦**：FIS 属于**业务数据采集源**，拥有独立的数据库 `project_vehicle_db`。`analytics_db` 属于**分析数仓**，不允许 FIS 服务直接侵入写数仓核心表。
2. **维表极简设计 (Minimal Schema Extension)**：`analytics_db` 中的 `dim.carbody_registry`（物理车身首末过站表）与 `dim.dim_vehicle_profile`（全厂 360 车辆主画像表）仅扩充核心关联主键 **`project_vehicle_no`**（项目车编号）。其余项目属性（如项目阶段、Block 编号、6 位代码等）通过 `project_vehicle_no` 随时与源表 `project_vehicle_orders` JOIN 关联查询，避免数据冗余。

---

## 2. 数据库设计规范 (Database & Schema Specification)

### 2.1 FIS 独立业务库：`project_vehicle_db`

- **数据库名**：`project_vehicle_db`
- **数据表名**：`project_vehicle_orders`
- **业务主键**：`project_vehicle_no`

```sql
-- 在 project_vehicle_db 中创建项目车生产订单明细表
CREATE TABLE IF NOT EXISTS project_vehicle_orders (
    project_vehicle_no VARCHAR(64) PRIMARY KEY,       -- 项目车编号 (主键，如 PP2-EREV-VFF-56)
    file_name          VARCHAR(255) NOT NULL,         -- 来源 Word 文件名
    project_stage      VARCHAR(32),                   -- 项目阶段 (如 VFF)
    block_no           INT,                            -- Block 编号
    code_6bit          VARCHAR(16),                   -- 6位代码 (如 VA24CQ)
    color_interior     VARCHAR(64),                  -- 外色内饰代码
    kom_no             VARCHAR(32),                  -- KOM 订货号
    knr_no             VARCHAR(32),                  -- KNR 生产流水号
    pin_no             VARCHAR(32),                  -- PIN 识别码 (如 1234567)
    pin_prefix         VARCHAR(16),                  -- PIN 前缀 (如 782026)
    composite_pin_no   VARCHAR(64),                  -- 合成 PIN 识别码 (13位 = 前缀 + pin_no)
    created_at         TIMESTAMPTZ DEFAULT NOW(),    -- 首次入库时间
    updated_at         TIMESTAMPTZ DEFAULT NOW()     -- 最后更新时间
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_pvo_file_name        ON project_vehicle_orders(file_name);
CREATE INDEX IF NOT EXISTS idx_pvo_pin_no           ON project_vehicle_orders(pin_no);
CREATE INDEX IF NOT EXISTS idx_pvo_knr_no           ON project_vehicle_orders(knr_no);
CREATE INDEX IF NOT EXISTS idx_pvo_composite_pin_no ON project_vehicle_orders(composite_pin_no);
```

---

### 2.2 `analytics_db` ODS 贴源表与维表极简扩展

```sql
-- 1. 数仓 ODS 物理贴源表与主键声明
CREATE TABLE IF NOT EXISTS ods.ods_fis_project_vehicle_orders (
    LIKE src_project_vehicle.project_vehicle_orders INCLUDING ALL
);
ALTER TABLE ods.ods_fis_project_vehicle_orders ADD PRIMARY KEY (project_vehicle_no);

-- 2. 物理车身首末过站聚合维表
ALTER TABLE dim.carbody_registry 
  ADD COLUMN IF NOT EXISTS project_vehicle_no VARCHAR(64);

-- 3. 全厂 360 车辆主画像表
ALTER TABLE dim.dim_vehicle_profile 
  ADD COLUMN IF NOT EXISTS project_vehicle_no VARCHAR(64);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_dim_carbody_pvn ON dim.carbody_registry(project_vehicle_no);
CREATE INDEX IF NOT EXISTS idx_dim_vp_pvn      ON dim.dim_vehicle_profile(project_vehicle_no);
```

---

## 3. 数据匹配与刷新逻辑 (Data Matching & Refresh ETL)

### 3.1 匹配关联规则
- **匹配桥梁**：物理车身 14 位车身号 `dim.carbody_registry.vehicle_id` 前 13 位与 FIS 项目车明细中的 `ods.ods_fis_project_vehicle_orders.composite_pin_no`（13 位合成 PIN）精确相等。
- **匹配条件 SQL**：`LEFT(cr.vehicle_id, 13) = pvo.composite_pin_no`

### 3.2 刷新存储过程匹配逻辑 (`meta.refresh_carbody_dim`)

在 `analytics_db` 的 `meta.refresh_carbody_dim()` 存储过程中，使用纯粹基于 13 位复合 PIN 的精确关联匹配逻辑（取消模糊匹配）：

```sql
-- 匹配更新项目车编号 (基于 13 位 composite_pin_no 精确匹配)
UPDATE dim.carbody_registry cr
SET project_vehicle_no = pvo.project_vehicle_no
FROM ods.ods_fis_project_vehicle_orders pvo
WHERE pvo.composite_pin_no IS NOT NULL 
  AND pvo.composite_pin_no <> '' 
  AND LEFT(cr.vehicle_id, 13) = pvo.composite_pin_no
  AND (cr.project_vehicle_no IS NULL OR cr.project_vehicle_no <> pvo.project_vehicle_no);
```

---

## 4. 链路集成与查询示例 (Lineage & Query Example)

### 4.1 数据链路总览

```text
[Word 生产通知单]
       │ (python-docx / FIS ETL)
       ▼
[project_vehicle_db.project_vehicle_orders]  (业务源库，含 composite_pin_no)
       │ (postgres_fdw 挂载至 src_project_vehicle 模式)
       ▼
[analytics_db.src_project_vehicle.project_vehicle_orders] (FDW 外表视图)
       │ (UPSERT 同步落盘)
       ▼
[analytics_db.ods.ods_fis_project_vehicle_orders]  (数仓 ODS 本地贴源表)
       │ (meta.refresh_carbody_dim 比对 vehicle_id 前13位)
       ▼
[analytics_db.dim.carbody_registry] (打上 project_vehicle_no)
       │ (meta.refresh_analytics_all 组装)
       ▼
[analytics_db.dim.dim_vehicle_profile] (全厂 360 画像表)
```

### 4.2 典型联合分析 SQL
通过 `project_vehicle_no` 关联查询完整项目属性：

```sql
SELECT 
    vp.vehicle_id,
    vp.project_vehicle_no,
    pvo.project_stage,
    pvo.block_no,
    pvo.code_6bit,
    vp.current_process_area,
    vp.carbody_last_seen_at
FROM dim.dim_vehicle_profile vp
LEFT JOIN ods.ods_fis_project_vehicle_orders pvo 
       ON vp.project_vehicle_no = pvo.project_vehicle_no
WHERE vp.project_vehicle_no IS NOT NULL;
```
