# history_station_defect_summary 固定窗口保留方案

修改时间：2026-04-15 15:10 Asia/Shanghai

主要修改内容：
- 新增 `history_station_defect_summary` 固定窗口表方案
- 约束窗口为参数化模式，支持最近 `N` 条、最近 `N` 个月或两者同时生效
- 说明该方案与当前增量刷新脚本的 watermark、replay window、UPSERT 机制如何兼容

## 1. 目标

当前 `defect_database/refresh_history_station_defect_summary.py` 已经实现：

- 基于 `history_id` watermark 的增量刷新
- replay window 回放
- `INSERT ... ON CONFLICT(history_id) DO UPDATE`

本次新增目标不是把它改回全量，而是把本地目标表：

- `defect_db.public.history_station_defect_summary`

从“长期累计表”收敛成“固定窗口表”。

你的业务期望是：

- 只保留最近 `60000` 条
- 或只保留最近 `3` 个月
- 窗口规则必须参数化，后续可以切换

## 2. 结论

建议采用：

- 增量写入
- 成功刷新后再执行窗口清理

而不是：

- 每次全量重建窗口

原因：

- 当前脚本的增量机制已经成熟
- 固定窗口只需要在“写入新数据后”再裁剪旧数据
- 不需要破坏现有的 watermark、回放窗口和 UPSERT 逻辑

一句话方案：

- `history_station_defect_summary` 继续增量维护
- 每次 `--refresh` 成功收尾后，再按参数化窗口删除超出范围的旧记录

## 3. 推荐参数设计

建议新增以下环境变量：

### 3.1 主开关

- `DEFECT_SUMMARY_RETENTION_MODE`

可选值：

- `off`
  - 不做窗口清理，保持当前长期累计模式
- `max_rows`
  - 只按最近 `N` 条保留
- `max_months`
  - 只按最近 `N` 个月保留
- `both`
  - 两条规则同时生效，保留更严格的交集窗口

### 3.2 行数窗口

- `DEFECT_SUMMARY_RETENTION_MAX_ROWS`
  - 默认建议：`60000`

### 3.3 时间窗口

- `DEFECT_SUMMARY_RETENTION_MAX_MONTHS`
  - 默认建议：`3`

### 3.4 清理批次大小

- `DEFECT_SUMMARY_RETENTION_DELETE_BATCH_SIZE`
  - 默认建议：`5000`

用途：

- 避免单次删除过多记录导致事务时间过长
- 方便在大窗口缩容时分批清理

## 4. 推荐默认值

如果你现在的核心目标是：

- 把刷新成本稳定控制在一个上限
- 又不太关心更长周期的历史

我建议第一阶段默认使用：

- `DEFECT_SUMMARY_RETENTION_MODE=max_rows`
- `DEFECT_SUMMARY_RETENTION_MAX_ROWS=60000`

原因：

- 行数上限最稳定
- 随着产量变化，时间窗口的数据量会波动，行数窗口更适合做性能上限控制
- 当前脚本本来就围绕 `history_id` 递增和 replay window 运作，按“最近 `history_id`”保留更自然

如果后续你更在意业务口径，例如：

- 只看最近 `3` 个月质量数据

再切换为：

- `DEFECT_SUMMARY_RETENTION_MODE=max_months`
- `DEFECT_SUMMARY_RETENTION_MAX_MONTHS=3`

如果两者都想限制，可以用：

- `DEFECT_SUMMARY_RETENTION_MODE=both`

## 5. 窗口定义

### 5.1 最近 `N` 条

“最近 `N` 条”建议按以下定义：

- 按 `history_id` 从大到小排序
- 保留最新的 `N` 个 `history_id`

不要按：

- `date_time` 单独排序

原因：

- 当前增量主游标是 `history_id`
- replay window 和 UPSERT 也围绕 `history_id`
- 用 `history_id` 定义“最近”更贴近脚本现有一致性机制

### 5.2 最近 `N` 个月

“最近 `N` 个月”建议按以下定义：

- `date_time >= now() - interval 'N months'`

这是更符合业务时间语义的定义。

## 6. 与当前刷新脚本的兼容方式

### 6.1 保持 watermark 不回退

当前状态表：

- `history_station_defect_summary_refresh_state`

中的：

- `last_success_history_id`

仍然必须保留为“已经成功处理到哪里”的主游标。

即使窗口清理删除了更早的汇总行，也不要回退 watermark。

原因：

- watermark 表示“处理进度”
- 窗口表表示“当前保留范围”
- 这两个概念不能混用

### 6.2 replay window 继续保留

当前 replay window 用来处理：

- `history` 与 `history_detail` 迟到不同步

这个机制仍然保留，不需要因为引入窗口表而移除。

原因：

- replay 负责修正最近一段数据
- retention 负责删除太旧的数据
- 两者职责不同

### 6.3 清理动作只放在整轮刷新成功之后

推荐执行顺序：

1. 读取当前 watermark
2. 按批次拉取新增 + replay window 数据
3. UPSERT 到 `history_station_defect_summary`
4. 推进 state 和 batch log
5. 当本轮 `--refresh` 全部成功完成后，再执行 retention cleanup
6. 记录本次 cleanup 结果

不建议：

- 每个 batch 后都清理一次

原因：

- 逻辑更复杂
- 清理次数会变多
- 对小批次增量没有必要

## 7. 推荐实现位置

建议在 `refresh_history_station_defect_summary.py` 中增加：

### 7.1 扩展 `RuntimeSettings`

新增字段：

- `retention_mode`
- `retention_max_rows`
- `retention_max_months`
- `retention_delete_batch_size`

### 7.2 新增清理函数

建议新增函数：

- `cleanup_summary_retention_window(...)`

按模式分派：

- `cleanup_by_max_rows(...)`
- `cleanup_by_max_months(...)`
- `cleanup_by_both(...)`

### 7.3 在 `run_refresh()` 收尾阶段调用

在全部 batch 成功、释放锁之前执行一次 cleanup。

## 8. 推荐 SQL 思路

### 8.1 最近 `N` 条

思路：

1. 找出最新 `N` 条中的最小 `history_id`
2. 删除比它更小的记录

示意 SQL：

```sql
WITH keep_boundary AS (
    SELECT MIN(history_id) AS min_keep_history_id
    FROM (
        SELECT history_id
        FROM public.history_station_defect_summary
        ORDER BY history_id DESC
        LIMIT %(max_rows)s
    ) t
)
DELETE FROM public.history_station_defect_summary
WHERE history_id < (SELECT min_keep_history_id FROM keep_boundary)
```

### 8.2 最近 `N` 个月

示意 SQL：

```sql
DELETE FROM public.history_station_defect_summary
WHERE date_time < %(cutoff_time)s
```

### 8.3 `both` 模式

建议逻辑：

- 如果超出最近 `N` 条，删
- 如果超出最近 `N` 个月，删

也就是保留：

- 最近 `N` 条
- 且最近 `N` 个月

对应的是更严格的交集窗口。

## 9. 对日志和状态的建议

建议在现有日志体系上补两项：

### 9.1 cleanup 日志

可新增一条非 batch 日志，记录：

- retention mode
- deleted_count
- row_count_before
- row_count_after
- oldest_history_id_after
- oldest_date_time_after

### 9.2 print-status 补充窗口信息

在 `--print-status` 中新增输出：

- retention_mode
- retention_max_rows
- retention_max_months
- current_min_history_id
- current_max_history_id
- current_min_date_time
- current_max_date_time

## 10. 需要特别注意的风险

### 10.1 `from_summary` 的语义会变弱

当前 `--init-state` 的 `from_summary` 模式会读取：

- `history_station_defect_summary` 的 `MAX(history_id)`

如果这张表已经变成窗口表，它的 `MAX(history_id)` 仍然可靠，但它已经不再代表“完整历史都在表里”。

这不是 bug，但要在文档里说明：

- state table 才是长期进度真相
- summary table 只是当前保留窗口

### 10.2 下游 `analytics_db` 将只看到窗口内历史

如果 `analytics_db` 继续从：

- `defect_db.public.history_station_defect_summary`

取数，那么：

- `ods.history_station_defect_summary`
- `fct.fct_vehicle_defect_detection`
- `mart.mart_vehicle_quality_360`

也都会只保留窗口内数据。

这需要接受一个前提：

- 质量分析口径将从“全历史”变成“窗口历史”

### 10.3 `both` 模式可能比预期更严格

例如：

- 最近 `60000` 条覆盖了 `5` 个月
- 最近 `3` 个月其实只有 `30000` 条

那 `both` 最终只会保留 `30000` 条左右。

因此 `both` 适合作为“硬约束模式”，不适合默认上来就启用。

## 11. 推荐实施顺序

### 第一阶段

先落地：

- `DEFECT_SUMMARY_RETENTION_MODE`
- `DEFECT_SUMMARY_RETENTION_MAX_ROWS`
- `max_rows` 清理逻辑
- cleanup 日志

推荐默认值：

```env
DEFECT_SUMMARY_RETENTION_MODE=max_rows
DEFECT_SUMMARY_RETENTION_MAX_ROWS=60000
DEFECT_SUMMARY_RETENTION_DELETE_BATCH_SIZE=5000
```

### 第二阶段

再补：

- `DEFECT_SUMMARY_RETENTION_MAX_MONTHS`
- `max_months` 模式
- `both` 模式

### 第三阶段

最后再决定是否同步改造 `analytics_db`：

- 接受窗口历史
- 或拆成“完整缺陷库 + 窗口分析库”双层口径

## 12. 最终建议

基于你当前的业务要求，我建议：

1. 继续保留现有增量刷新主流程
2. 把 `history_station_defect_summary` 明确改造成窗口表
3. 第一阶段优先使用 `max_rows=60000`
4. `3` 个月窗口作为第二种可切换模式保留
5. cleanup 在整轮刷新成功后执行一次，不放在每个 batch 后面

这样做的好处是：

- 不破坏当前增量刷新逻辑
- 窗口规则参数化
- 性能上限可控
- 业务口径也足够清楚
