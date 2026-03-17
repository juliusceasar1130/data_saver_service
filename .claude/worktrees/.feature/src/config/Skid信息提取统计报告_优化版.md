# Skid信息编号提取统计报告 (优化版)

**转换时间**: 2025/9/12 08:30:02
**输入文件**: D:\Python\websoket\src\config\deviceConfig_org_skid.json
**输出文件**: src/config/deviceConfig_skid_info1111.json
**工具版本**: v2.0.0

## 转换结果

- **总记录数**: 100
- **成功转换**: 100
- **失败记录**: 0
- **转换成功率**: 100.00%

## 匹配模式统计

- **ST[n]模式**: 15 (15.0%)
- **普通RB模式**: 64 (64.0%)
- **复杂RB模式**: 20 (20.0%)
- **LT模式**: 1 (1.0%)
- **后备模式**: 0 (0.0%)
- **未匹配**: 0 (0.0%)

## 置信度分析

- **高置信度**: 79
- **中等置信度**: 21
- **低置信度**: 0
- **无置信度**: 0

## 设备分组

- **L3FUB2**: 50条记录
- **L3FKT1**: 50条记录

## 转换示例

### 示例 1
- **原始tag**: `.L3FUB2_1A_1A005TC_1A005RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A005RB`
- **匹配类型**: COMPLEX_RB_PATTERN
- **置信度**: MEDIUM
- **factor**: `{"norm":"4","e5":"3"}`
- **weight**: `0`

### 示例 2
- **原始tag**: `.L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A010RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"4","e5":"3"}`
- **weight**: `0`

### 示例 3
- **原始tag**: `.L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo`
- **RBindex**: `1B020RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"4","e5":"3"}`
- **weight**: `0`

### 示例 4
- **原始tag**: `.L3FKT1_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1F110LT`
- **匹配类型**: LT_PATTERN
- **置信度**: MEDIUM
- **factor**: `{"norm":"4","e5":"3"}`
- **weight**: `0`

### 示例 5
- **原始tag**: `.L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1H200OCFF1.ST[1]`
- **匹配类型**: ST_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"4","e5":"3"}`
- **weight**: `0`


## 字段变更说明

- **tag字段**: 保持原有内容不变
- **新增factor字段**: 所有记录设置为 {"norm":"4","e5":"3"}
- **新增RBindex字段**: 根据skid信息提取规则生成
- **新增weight字段**: 所有记录设置为 0

## 质量报告

✅ 所有记录转换成功，无错误记录

---
*由Skid信息编号提取工具 (优化版) v2.0.0 自动生成*
