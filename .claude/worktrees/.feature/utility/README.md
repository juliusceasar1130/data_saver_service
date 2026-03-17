# 工具集使用说明

**修改时间**: 2025年9月10日  
**修改内容**: 创建可复用的滚床编号提取工具

## 工具列表

### 1. 滚床编号提取工具 (rb-index-extractor.cjs)

**功能**: 从设备配置JSON文件中提取滚床编号，添加factor字段，并替换标签内容。

### 2. Skid信息编号提取工具 (skid-info-extractor.cjs)

**功能**: 从设备配置JSON文件中提取Skid编号，添加factor字段，保持原tag字段不变。

#### 使用方法

```bash
# 基本用法（使用默认路径）
node utility/skid-info-extractor.cjs

# 指定输入输出文件
node utility/skid-info-extractor.cjs 输入文件.json 输出文件.json

# 显示帮助信息
node utility/skid-info-extractor.cjs --help

# 实际使用示例
node utility/skid-info-extractor.cjs src/config/deviceConfig.json src/config/deviceConfig_skid_info.json

# 快速转换（使用批处理）
utility/quick-skid-convert.bat
```

#### 转换规则

该工具支持三种Skid编号提取模式：

1. **ST[n]模式**（数组索引模式）
   ```
   输入: .L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo
   输出: 保持原tag不变
   RBindex: "1H200OCFF1.ST[1]"
   ```

2. **普通RB模式**（简单滚床标识）
   ```
   输入: .L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo
   输出: 保持原tag不变
   RBindex: "1A010RB"
   ```

3. **复杂命名RB模式**（带设备类型的滚床标识）
   ```
   输入: .L3FUB2_1G_15AS_1G175EL_1G175RB.IL.SD.I1030_RBDataSkidNo
   输出: 保持原tag不变
   RBindex: "1G175RB"
   ```

#### 字段变更

- **tag字段**: 保持原有内容不变（与滚床编号提取工具的区别）
- **新增factor字段**: 所有记录设置为 `"4"`
- **新增RBindex字段**: 根据上述规则提取的Skid编号

#### 输出文件

工具会生成以下文件：
1. **转换后的JSON配置文件** - 包含所有转换后的设备配置
2. **Skid信息提取统计报告.md** - 详细的转换统计和示例

---

## 滚床编号提取工具详细说明

#### 使用方法

```bash
# 基本用法（使用默认路径）
node utility/rb-index-extractor.cjs

# 指定输入输出文件
node utility/rb-index-extractor.cjs 输入文件.json 输出文件.json

# 显示帮助信息
node utility/rb-index-extractor.cjs --help

# 实际使用示例
node utility/rb-index-extractor.cjs src/config/deviceConfig.json src/config/deviceConfigWithRB.json
```

#### 转换规则

该工具支持三种滚床编号提取模式：

1. **ST[n]模式**（数组索引模式）
   ```
   输入: .L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo
   输出: .L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.M1003_BodyID
   RBindex: "1H200OCFF1.ST[1]"
   ```

2. **普通RB模式**（简单滚床标识）
   ```
   输入: .L3FKT1_1B_1B030TT_1B030RB.IL.SD.I1030_RBDataSkidNo
   输出: .L3FKT1_1B_1B030TT_1B030RB.IL.SD.M1003_BodyID
   RBindex: "1B030RB"
   ```

3. **复杂命名RB模式**（带设备类型的滚床标识）
   ```
   输入: .L3FKT1_1F_1AAS_1F105SL_1F105RB.IL.SD.I1030_RBDataSkidNo
   输出: .L3FKT1_1F_1AAS_1F105SL_1F105RB.IL.SD.M1003_BodyID
   RBindex: "1F105RB"
   ```

#### 字段变更

- **tag字段**: `I1030_RBDataSkidNo` → `M1003_BodyID`
- **新增factor字段**: 所有记录设置为 `"4"`
- **新增RBindex字段**: 根据上述规则提取的滚床编号

#### 输出文件

工具会生成以下文件：
1. **转换后的JSON配置文件** - 包含所有转换后的设备配置
2. **转换统计报告.md** - 详细的转换统计和示例

#### 配置参数

工具的默认配置可以在脚本顶部的 `DEFAULT_CONFIG` 对象中修改：

```javascript
const DEFAULT_CONFIG = {
    inputFile: './src/config/deviceConfig.json',      // 默认输入文件
    outputFile: './src/config/deviceConfigWithRB.json', // 默认输出文件
    factorValue: "4",                                 // factor字段的值
    sourceTag: 'I1030_RBDataSkidNo',                 // 要替换的原始标签
    targetTag: 'M1003_BodyID'                        // 替换后的新标签
};
```

#### 错误处理

- 输入文件不存在时会显示错误信息
- JSON格式错误会显示解析错误
- 无法识别的滚床编号模式会显示警告
- 处理失败的记录会保持原样并记录到统计报告中

#### 日志输出

工具运行时会显示详细的处理信息：
- 📁 文件路径信息
- 🔄 处理进度
- ⚠️ 警告信息
- ✅ 成功统计
- ❌ 错误统计
- 📊 统计报告位置

## 扩展开发

### 添加新的提取模式

如需支持新的滚床编号模式，可以修改 `extractRBindex` 函数：

```javascript
function extractRBindex(tag) {
    // 在这里添加新的模式识别逻辑
    
    // 新模式示例
    const newPattern = /你的正则表达式/;
    const newMatch = tag.match(newPattern);
    if (newMatch) {
        return '提取的结果';
    }
    
    // 保留现有的模式...
}
```

### 作为模块使用

该工具也可以作为Node.js模块使用：

```javascript
const { extractRBindex, transformConfig } = require('./utility/rb-index-extractor.cjs');

// 单独使用提取函数
const rbIndex = extractRBindex('.L3FKT1_1B_1B030TT_1B030RB.IL.SD.M1003_BodyID');
console.log(rbIndex); // "1B030RB"

// 使用转换函数
transformConfig('input.json', 'output.json');
```

## 版本历史

- **v2.1.0** (2025-09-10): 新增Skid信息编号提取工具，支持保持原tag不变的转换模式
- **v2.0.0** (2025-09-10): 创建可复用滚床编号提取工具版本，支持命令行参数、统计报告、错误处理
- **v1.0.0** (2025-09-10): 初始版本，基本转换功能

## 技术支持

如有问题或需要扩展功能，请参考代码注释或联系开发人员。
