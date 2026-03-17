# Skid信息编号提取统计报告 v2.2.0

**转换时间**: 2025/9/15 08:49:46
**输入文件**: D:\Python\websoket\utility\deviceConfig_模版.json
**输出文件**: D:\Python\websoket\utility\deviceConfig_111.json
**工具版本**: v2.2.0 (基于模版优化)

## 转换结果

- **总记录数**: 106
- **成功转换**: 106
- **失败记录**: 0
- **转换成功率**: 100.00%

## 匹配模式统计

- **ST[n]模式**: 0 (0.0%)
- **普通RB模式**: 81 (76.4%)
- **TC/TT模式**: 15 (14.2%)
- **EL/SL模式**: 5 (4.7%)
- **复杂RB模式**: 5 (4.7%)
- **LT+RB模式**: 0 (0.0%)
- **LT模式**: 0 (0.0%)
- **ST+RB模式**: 0 (0.0%)
- **后备模式**: 0 (0.0%)
- **未匹配**: 0 (0.0%)

## 置信度分析

- **高置信度**: 101
- **中等置信度**: 5
- **低置信度**: 0
- **无置信度**: 0

## 设备分组

- **L3F19**: 64条记录
- **L3F24**: 42条记录

## 转换示例

### 示例 1
- **原始tag**: `.L3F19_1A_1A005RB_1A005RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A005RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 2
- **原始tag**: `.L3F19_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A010RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 3
- **原始tag**: `.L3F19_1A_1A015RB_1A015RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A015RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 4
- **原始tag**: `.L3F19_1A_1A020RB_1A020RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A020RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 5
- **原始tag**: `.L3F19_1A_1A040RB_1A040RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1A040RB`
- **匹配类型**: SIMPLE_RB_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 6
- **原始tag**: `.L3F19_1B_1B100TC_1B100RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1B100RB`
- **匹配类型**: TC_TT_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 7
- **原始tag**: `.L3F19_1C_1C135LT_1C135RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1C135RB`
- **匹配类型**: COMPLEX_RB_PATTERN
- **置信度**: MEDIUM
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`

### 示例 8
- **原始tag**: `.L3F19_1F_16AS_1F230EL_1F230RB.IL.SD.I1030_RBDataSkidNo`
- **RBindex**: `1F230RB`
- **匹配类型**: EL_SL_PATTERN
- **置信度**: HIGH
- **factor**: `{"norm":"5","e5":"3"}`
- **weight**: `0`
- **area**: `1`
- **sequence**: `0`


## 字段变更说明（基于模版优化）

- **tag字段**: 保持原有内容不变
- **新增factor字段**: 所有记录设置为 {"norm":"5","e5":"3"} (基于模版配置)
- **新增RBindex字段**: 根据skid信息提取规则生成
- **新增weight字段**: 所有记录设置为 0
- **新增area字段**: 所有记录设置为 1 (区域标识)
- **新增sequence字段**: 所有记录设置为 0 (区域内序号)
- **metadata结构**: 采用模版标准结构

## 质量报告

✅ 所有记录转换成功，无错误记录

## v2版本改进

- ✅ 更新factor字段默认值为模版配置
- ✅ 采用模版metadata结构标准
- ✅ 增强TC/TT、EL/SL、ST+RB等模式识别
- ✅ 优化匹配优先级和准确性
- ✅ 改进统计报告和错误处理
- ✅ 新增area字段，用于标识设备所属区域
- ✅ 新增sequence字段，用于标识设备在区域内的序号

---
*由Skid信息编号提取工具 v2.2.0 (基于模版优化) 自动生成*
