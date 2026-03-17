# Skid信息编号提取统计报告 v2.1.0

**转换时间**: 2025/9/12 14:31:28
**输入文件**: utility/deviceConfig_模版.json
**输出文件**: utility/deviceConfig_skid_info_v2.json
**工具版本**: v2.1.0 (基于模版优化)

## 转换结果

- **总记录数**: 100
- **成功转换**: 100
- **失败记录**: 0
- **转换成功率**: 100.00%

## 匹配模式统计

- **ST[n]模式**: 15 (15.0%)
- **普通RB模式**: 64 (64.0%)
- **TC/TT模式**: 4 (4.0%)
- **EL/SL模式**: 4 (4.0%)
- **复杂RB模式**: 12 (12.0%)
- **LT+RB模式**: 0 (0.0%)
- **LT模式**: 1 (1.0%)
- **ST+RB模式**: 0 (0.0%)
- **后备模式**: 0 (0.0%)
- **未匹配**: 0 (0.0%)

## 置信度分析

- **高置信度**: 87
- **中等置信度**: 13
- **低置信度**: 0
- **无置信度**: 0

## 设备分组

- **L3FUB2**: 50条记录
- **L3FKT1**: 50条记录

## 转换示例

### 示例 1
- **原始tag**: `.L3FUB2_1A_1A005TC_1A005RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A005RB`
- **匹配类型**: TC_TT_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 2
- **原始tag**: `.L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A010RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 3
- **原始tag**: `.L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo`
- **RBindex**: `1B020RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 4
- **原始tag**: `.L3FUB2_1B_1B025RB_1B025RB.ILO.SD.I1030_RBDataSkidNo`
- **RBindex**: `1B025RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 5
- **原始tag**: `.L3FUB2_1B_1B030RB_1B030RB.ILO.SD.I1030_RBDataSkidNo`
- **RBindex**: `1B030RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 6
- **原始tag**: `.L3FUB2_1C_16AS_1C060EH_1C060RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1C060RB`
- **匹配类型**: COMPLEX_RB_PATTERN
- **置信度**: MEDIUM
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 7
- **原始tag**: `.L3FUB2_1C_16AS_1C100EL_1C100RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1C100RB`
- **匹配类型**: EL_SL_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`

### 示例 8
- **原始tag**: `.L3FKT1_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1F110LT`
- **匹配类型**: LT_PATTERN
- **置信度**: MEDIUM
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`


## 字段变更说明（基于模版优化）

- **tag字段**: 保持原有内容不变
- **新增factor字段**: 所有记录设置为 {"norm":"5","e5":"3"} (基于模版配置)
- **新增RBindex字段**: 根据skid信息提取规则生成
- **新增weight字段**: 所有记录设置为 0
- **metadata结构**: 采用模版标准结构

## 质量报告

✅ 所有记录转换成功，无错误记录

## v2版本改进

- ✅ 更新factor字段默认值为模版配置
- ✅ 采用模版metadata结构标准
- ✅ 增强TC/TT、EL/SL、ST+RB等模式识别
- ✅ 优化匹配优先级和准确性
- ✅ 改进统计报告和错误处理

---
*由Skid信息编号提取工具 v2.1.0 (基于模版优化) 自动生成*
