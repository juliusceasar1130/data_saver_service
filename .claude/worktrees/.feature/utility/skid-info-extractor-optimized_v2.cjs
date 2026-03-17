/*
 * 修改时间：2025年9月12日14点05分
 * 修改内容：Skid信息编号提取工具 v2.2.0 - 增加区域和序号字段优化版本
 * 
 * 版本升级功能：
 * 1. 更新factor字段默认值为 {"norm":"5","e5":"3"}（基于模版配置）
 * 2. 采用模版metadata结构标准
 * 3. 优化提取逻辑和错误处理机制
 * 4. 增强统计报告功能
 * 5. 改进代码结构和文档说明
 * 6. 新增area字段（区域标识，默认值：1）
 * 7. 新增sequence字段（区域内序号，默认值：0）
 * 
 * 使用方法：
 * node utility/skid-info-extractor-optimized_v2.cjs [输入文件] [输出文件]
 * 
 * 示例：
 * node utility/skid-info-extractor-optimized_v2.cjs src/config/deviceConfig.json src/config/deviceConfig_skid_info_v2.json
 */

const fs = require('fs');
const path = require('path');

// 默认配置 - 基于模版更新
const DEFAULT_CONFIG = {
    inputFile: './src/config/deviceConfig.json',
    outputFile: './src/config/deviceConfig_skid_info_v2.json',
    factorValue: {"norm":"5","e5":"3"}, // 更新为模版中的值
    weightValue: 0,
    areaValue: 1, // 区域标识默认值
    sequenceValue: 0, // 区域内序号默认值
    enableDebug: false,
    version: "2.2.0"
};

// 模版metadata结构
const TEMPLATE_METADATA = {
    "totalDevices": "配置文件中设备总数",
    "deviceTypes": "系统支持的设备类型列表",
    "configSchema": {
        "id": "设备唯一标识符",
        "type": "消息通信类型",
        "plc": "PLC控制器标识",
        "tag": "数据点位路径"
    },
    "dataFields": {
        "factor": "雪橇数量计算系数",
        "RBindex": "滚床编号，提取自tag路径",
        "weight": "权重值，用于特殊计算逻辑",
        "area": "区域标识，用于标识设备所属区域",
        "sequence": "区域内序号，表示在特定区域内的位置序号"
    },
    "calculations": {
        "skidCount": "见文档"
    }
};

/**
 * 调试日志输出
 * @param {string} message - 日志信息
 * @param {string} level - 日志级别 (info, warn, error)
 */
function debugLog(message, level = 'info') {
    if (DEFAULT_CONFIG.enableDebug) {
        const timestamp = new Date().toLocaleTimeString('zh-CN');
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
    }
}

/**
 * 显示使用帮助
 */
function showHelp() {
    console.log(`
Skid信息编号提取工具 v${DEFAULT_CONFIG.version} (基于模版优化)
=====================================================

用法：
  node utility/skid-info-extractor-optimized_v2.cjs [输入文件] [输出文件] [选项]

参数：
  输入文件    源设备配置JSON文件路径 (默认: ${DEFAULT_CONFIG.inputFile})
  输出文件    输出设备配置JSON文件路径 (默认: ${DEFAULT_CONFIG.outputFile})

选项：
  --debug     启用调试模式，显示详细处理过程
  --help      显示此帮助信息

示例：
  # 使用默认路径
  node utility/skid-info-extractor-optimized_v2.cjs
  
  # 指定输入输出文件
  node utility/skid-info-extractor-optimized_v2.cjs input.json output.json
  
  # 启用调试模式
  node utility/skid-info-extractor-optimized_v2.cjs input.json output.json --debug

提取规则（增强版）：
  情况1: ST[n]模式 (OCFF/ROFG类型)
    原始: .L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo
    RBindex: 1H200OCFF1.ST[1]
    
  情况2: 普通RB模式  
    原始: .L3F19_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo
    RBindex: 1A010RB
    
  情况3: 复杂命名RB模式
    原始: .L3F19_1G_15AS_1G175EL_1G175RB.IL.SD.I1030_RBDataSkidNo  
    RBindex: 1G175RB
    
  情况4: 特殊LT/TT/TC模式处理
    原始: .L3F19_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo
    RBindex: 1F110LT
    
  情况5: EL/SL模式处理
    原始: .L3F19_1H_18AS_1H330EL_1H330RB.IL.SD.I1030_RBDataSkidNo
    RBindex: 1H330RB

字段变更（基于模版优化）：
  - tag字段: 保持原有内容不变
  - 新增factor字段: 设置为 {"norm":"5","e5":"3"} (基于模版)
  - 新增RBindex字段: 根据规则提取skid编号
  - 新增weight字段: 设置为 ${DEFAULT_CONFIG.weightValue}
  - 新增area字段: 设置为 ${DEFAULT_CONFIG.areaValue} (区域标识)
  - 新增sequence字段: 设置为 ${DEFAULT_CONFIG.sequenceValue} (区域内序号)
  - metadata结构: 采用模版标准结构
`);
}

/**
 * 提取Skid编号(RBindex) - v2增强版
 * @param {string} tag - 设备标签
 * @returns {Object} 包含提取结果和匹配类型的对象
 */
function extractSkidIndex(tag) {
    debugLog(`正在处理标签: ${tag}`);
    
    // 情况1: ST[n]模式 - OCFF和ROFG类型
    // 匹配模式: .L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo
    // 提取: 1H200OCFF1.ST[1]
    const stPattern = /[._]([^._]*(?:OCFF\d+|ROFG\d+))\.ST\[(\d+)\]/i;
    const stMatch = tag.match(stPattern);
    if (stMatch) {
        const result = `${stMatch[1]}.ST[${stMatch[2]}]`;
        debugLog(`ST模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'ST_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 情况2: 普通RB模式 - 严格匹配
    // 匹配模式: .L3F19_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo
    // 提取: 1A010RB
    const simpleRbPattern = /_([^_]*RB)_\1(?:\.|$)/i;
    const simpleRbMatch = tag.match(simpleRbPattern);
    if (simpleRbMatch) {
        const result = simpleRbMatch[1];
        debugLog(`普通RB模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'SIMPLE_RB_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 情况3: TC/TT模式优先处理
    // 匹配模式: .L3F19_1D_1D280TC_1D280RB.IL.SD.I1030_RBDataSkidNo
    // 优先提取: 1D280RB（而不是1D280TC）
    const tcTtPattern = /_([^_]*(?:TC|TT))_([^_]*RB)(?:\.|$)/i;
    const tcTtMatch = tag.match(tcTtPattern);
    if (tcTtMatch) {
        const result = tcTtMatch[2]; // 取RB部分
        debugLog(`TC/TT模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'TC_TT_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 情况4: EL/SL模式处理
    // 匹配模式: .L3F19_1H_18AS_1H330EL_1H330RB.IL.SD.I1030_RBDataSkidNo
    // 提取: 1H330RB
    const elSlPattern = /_([^_]*(?:EL|SL))_([^_]*RB)(?:\.|$)/i;
    const elSlMatch = tag.match(elSlPattern);
    if (elSlMatch) {
        const result = elSlMatch[2]; // 取RB部分
        debugLog(`EL/SL模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'EL_SL_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 情况5: 复杂命名RB模式
    // 匹配模式: .L3F19_1G_15AS_1G175EL_1G175RB.IL.SD.I1030_RBDataSkidNo
    // 提取: 1G175RB
    const complexRbPattern = /_([^_]*RB)(?:\.|$)/i;
    const complexRbMatch = tag.match(complexRbPattern);
    if (complexRbMatch) {
        const result = complexRbMatch[1];
        debugLog(`复杂RB模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'COMPLEX_RB_PATTERN',
            confidence: 'MEDIUM'
        };
    }

    // 情况6: LT模式处理
    // 匹配模式: .L3F19_1C_1C135LT_1C135RB.IL.SD.I1030_RBDataSkidNo
    // 优先提取: 1C135RB（如果存在），否则提取1C135LT
    const ltWithRbPattern = /_([^_]*LT)_([^_]*RB)(?:\.|$)/i;
    const ltWithRbMatch = tag.match(ltWithRbPattern);
    if (ltWithRbMatch) {
        const result = ltWithRbMatch[2]; // 优先取RB部分
        debugLog(`LT+RB模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'LT_WITH_RB_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 单独LT模式
    const ltPattern = /_([^_]*LT)(?:\.|$)/i;
    const ltMatch = tag.match(ltPattern);
    if (ltMatch) {
        const result = ltMatch[1];
        debugLog(`LT模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'LT_PATTERN',
            confidence: 'MEDIUM'
        };
    }

    // 情况7: ST模式处理（非OCFF/ROFG）
    // 匹配模式: .L3F19_1O_1BAS_1O515ST_1O515RB.IL.SD.I1030_RBDataSkidNo
    // 优先提取: 1O515RB
    const stWithRbPattern = /_([^_]*ST)_([^_]*RB)(?:\.|$)/i;
    const stWithRbMatch = tag.match(stWithRbPattern);
    if (stWithRbMatch) {
        const result = stWithRbMatch[2]; // 优先取RB部分
        debugLog(`ST+RB模式匹配成功: ${result}`, 'info');
        return {
            rbIndex: result,
            matchType: 'ST_WITH_RB_PATTERN',
            confidence: 'HIGH'
        };
    }

    // 情况8: 通用后备模式 - 提取最后一个有意义的标识符
    const parts = tag.split('_');
    for (let i = parts.length - 1; i >= 0; i--) {
        const part = parts[i];
        if (part.includes('.')) {
            const beforeDot = part.split('.')[0];
            if (beforeDot.length > 0 && /^[A-Z0-9]+$/i.test(beforeDot)) {
                debugLog(`后备模式匹配: ${beforeDot}`, 'warn');
                return {
                    rbIndex: beforeDot,
                    matchType: 'FALLBACK_PATTERN',
                    confidence: 'LOW'
                };
            }
        }
    }

    // 如果都没匹配到，返回空字符串
    console.warn(`⚠️  无法提取Skid编号: ${tag}`);
    return {
        rbIndex: '',
        matchType: 'NO_MATCH',
        confidence: 'NONE'
    };
}

/**
 * 生成转换统计报告 - v2增强版
 * @param {Object} stats - 统计数据
 */
function generateReport(stats) {
    const reportContent = `# Skid信息编号提取统计报告 v${DEFAULT_CONFIG.version}

**转换时间**: ${new Date().toLocaleString('zh-CN')}
**输入文件**: ${stats.inputFile}
**输出文件**: ${stats.outputFile}
**工具版本**: v${DEFAULT_CONFIG.version} (基于模版优化)

## 转换结果

- **总记录数**: ${stats.totalRecords}
- **成功转换**: ${stats.successCount}
- **失败记录**: ${stats.failureCount}
- **转换成功率**: ${((stats.successCount / stats.totalRecords) * 100).toFixed(2)}%

## 匹配模式统计

- **ST[n]模式**: ${stats.stPatternCount} (${((stats.stPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **普通RB模式**: ${stats.simpleRbPatternCount} (${((stats.simpleRbPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **TC/TT模式**: ${stats.tcTtPatternCount} (${((stats.tcTtPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **EL/SL模式**: ${stats.elSlPatternCount} (${((stats.elSlPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **复杂RB模式**: ${stats.complexRbPatternCount} (${((stats.complexRbPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **LT+RB模式**: ${stats.ltWithRbPatternCount} (${((stats.ltWithRbPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **LT模式**: ${stats.ltPatternCount} (${((stats.ltPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **ST+RB模式**: ${stats.stWithRbPatternCount} (${((stats.stWithRbPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **后备模式**: ${stats.fallbackPatternCount} (${((stats.fallbackPatternCount / stats.totalRecords) * 100).toFixed(1)}%)
- **未匹配**: ${stats.noMatchCount} (${((stats.noMatchCount / stats.totalRecords) * 100).toFixed(1)}%)

## 置信度分析

- **高置信度**: ${stats.highConfidenceCount}
- **中等置信度**: ${stats.mediumConfidenceCount}
- **低置信度**: ${stats.lowConfidenceCount}
- **无置信度**: ${stats.noConfidenceCount}

## 设备分组

${Object.entries(stats.deviceGroups).map(([plc, count]) => `- **${plc}**: ${count}条记录`).join('\n')}

## 转换示例

${stats.examples.map((example, index) => `### 示例 ${index + 1}
- **原始tag**: \`${example.originalTag}\`
- **RBindex**: \`${example.rbIndex}\`
- **匹配类型**: ${example.matchType}
- **置信度**: ${example.confidence}
- **factor**: \`${example.factor}\`
- **weight**: \`${example.weight}\`
- **area**: \`${example.area}\`
- **sequence**: \`${example.sequence}\`
`).join('\n')}

## 字段变更说明（基于模版优化）

- **tag字段**: 保持原有内容不变
- **新增factor字段**: 所有记录设置为 {"norm":"5","e5":"3"} (基于模版配置)
- **新增RBindex字段**: 根据skid信息提取规则生成
- **新增weight字段**: 所有记录设置为 ${DEFAULT_CONFIG.weightValue}
- **新增area字段**: 所有记录设置为 ${DEFAULT_CONFIG.areaValue} (区域标识)
- **新增sequence字段**: 所有记录设置为 ${DEFAULT_CONFIG.sequenceValue} (区域内序号)
- **metadata结构**: 采用模版标准结构

## 质量报告

${stats.failureCount === 0 ? '✅ 所有记录转换成功，无错误记录' : `⚠️ ${stats.failureCount} 条记录转换失败，请检查原始数据`}

## v2版本改进

- ✅ 更新factor字段默认值为模版配置
- ✅ 采用模版metadata结构标准
- ✅ 增强TC/TT、EL/SL、ST+RB等模式识别
- ✅ 优化匹配优先级和准确性
- ✅ 改进统计报告和错误处理
- ✅ 新增area字段，用于标识设备所属区域
- ✅ 新增sequence字段，用于标识设备在区域内的序号

---
*由Skid信息编号提取工具 v${DEFAULT_CONFIG.version} (基于模版优化) 自动生成*
`;

    const reportPath = path.join(path.dirname(stats.outputFile), `Skid信息提取统计报告_v${DEFAULT_CONFIG.version}.md`);
    fs.writeFileSync(reportPath, reportContent, 'utf8');
    console.log(`📊 转换报告已生成: ${reportPath}`);
}

/**
 * 主转换函数 - v2增强版
 * @param {string} inputPath - 输入文件路径
 * @param {string} outputPath - 输出文件路径
 */
function transformConfig(inputPath, outputPath) {
    const startTime = Date.now();
    
    try {
        // 验证输入文件
        if (!fs.existsSync(inputPath)) {
            throw new Error(`输入文件不存在: ${inputPath}`);
        }

        console.log(`🔄 开始Skid信息提取 v${DEFAULT_CONFIG.version} (基于模版优化)...`);
        console.log(`📁 输入文件: ${inputPath}`);
        console.log(`📁 输出文件: ${outputPath}`);

        // 读取原配置文件
        const configData = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
        
        // 初始化统计数据
        const stats = {
            inputFile: inputPath,
            outputFile: outputPath,
            totalRecords: 0,
            successCount: 0,
            failureCount: 0,
            stPatternCount: 0,
            simpleRbPatternCount: 0,
            tcTtPatternCount: 0,
            elSlPatternCount: 0,
            complexRbPatternCount: 0,
            ltWithRbPatternCount: 0,
            ltPatternCount: 0,
            stWithRbPatternCount: 0,
            fallbackPatternCount: 0,
            noMatchCount: 0,
            highConfidenceCount: 0,
            mediumConfidenceCount: 0,
            lowConfidenceCount: 0,
            noConfidenceCount: 0,
            deviceGroups: {},
            examples: []
        };

        // 创建新的配置对象（基于模版结构）
        const newConfig = {
            description: "设备参数配置文件 - WebSocket工业数据采集系统 (Skid信息提取v2.2.0)",
            version: DEFAULT_CONFIG.version,
            lastModified: "2025年9月12日14点05分",
            factor: DEFAULT_CONFIG.factorValue, // 添加全局factor字段
            config: {}
        };

        // 处理每个PLC的配置
        for (const [plcName, devices] of Object.entries(configData.config)) {
            if (!Array.isArray(devices)) {
                console.warn(`⚠️  跳过非数组配置: ${plcName}`);
                continue;
            }

            stats.deviceGroups[plcName] = devices.length;
            
            newConfig.config[plcName] = devices.map((device, index) => {
                try {
                    stats.totalRecords++;
                    
                    // 保持tag字段不变
                    const tag = device.tag;
                    
                    // 提取Skid编号 (使用v2增强版函数)
                    const extractResult = extractSkidIndex(tag);
                    const { rbIndex, matchType, confidence } = extractResult;
                    
                    // 统计模式类型
                    switch (matchType) {
                        case 'ST_PATTERN':
                            stats.stPatternCount++;
                            break;
                        case 'SIMPLE_RB_PATTERN':
                            stats.simpleRbPatternCount++;
                            break;
                        case 'TC_TT_PATTERN':
                            stats.tcTtPatternCount++;
                            break;
                        case 'EL_SL_PATTERN':
                            stats.elSlPatternCount++;
                            break;
                        case 'COMPLEX_RB_PATTERN':
                            stats.complexRbPatternCount++;
                            break;
                        case 'LT_WITH_RB_PATTERN':
                            stats.ltWithRbPatternCount++;
                            break;
                        case 'LT_PATTERN':
                            stats.ltPatternCount++;
                            break;
                        case 'ST_WITH_RB_PATTERN':
                            stats.stWithRbPatternCount++;
                            break;
                        case 'FALLBACK_PATTERN':
                            stats.fallbackPatternCount++;
                            break;
                        case 'NO_MATCH':
                            stats.noMatchCount++;
                            break;
                    }

                    // 统计置信度
                    switch (confidence) {
                        case 'HIGH':
                            stats.highConfidenceCount++;
                            break;
                        case 'MEDIUM':
                            stats.mediumConfidenceCount++;
                            break;
                        case 'LOW':
                            stats.lowConfidenceCount++;
                            break;
                        case 'NONE':
                            stats.noConfidenceCount++;
                            break;
                    }

                    // 收集示例（前8个不同类型的）
                    if (stats.examples.length < 8) {
                        const hasThisType = stats.examples.some(ex => ex.matchType === matchType);
                        if (!hasThisType || stats.examples.length < 5) {
                            stats.examples.push({
                                originalTag: device.tag,
                                rbIndex: rbIndex,
                                matchType: matchType,
                                confidence: confidence,
                                factor: JSON.stringify(DEFAULT_CONFIG.factorValue),
                                weight: DEFAULT_CONFIG.weightValue,
                                area: DEFAULT_CONFIG.areaValue,
                                sequence: DEFAULT_CONFIG.sequenceValue
                            });
                        }
                    }

                    stats.successCount++;

                    // 返回增强的设备对象（基于模版结构）
                    return {
                        id: device.id || "",
                        type: device.type || "advise",
                        plc: device.plc || plcName,
                        tag: device.tag,
                        factor: DEFAULT_CONFIG.factorValue,
                        RBindex: rbIndex,
                        weight: DEFAULT_CONFIG.weightValue,
                        area: DEFAULT_CONFIG.areaValue,
                        sequence: DEFAULT_CONFIG.sequenceValue
                    };
                } catch (error) {
                    console.error(`❌ 处理记录失败 [${plcName}][${index}]:`, error.message);
                    debugLog(`错误详情: ${error.stack}`, 'error');
                    stats.failureCount++;
                    return device; // 返回原始记录
                }
            });
        }

        // 添加模版metadata结构
        newConfig.metadata = {
            ...TEMPLATE_METADATA,
            totalDevices: stats.totalRecords,
            deviceTypes: Object.keys(stats.deviceGroups),
            transformInfo: {
                originalFile: path.basename(inputPath),
                transformDate: new Date().toLocaleString('zh-CN'),
                toolVersion: `v${DEFAULT_CONFIG.version}`,
                totalRecords: stats.totalRecords,
                successCount: stats.successCount,
                failureCount: stats.failureCount,
                successRate: `${((stats.successCount / stats.totalRecords) * 100).toFixed(2)}%`,
                processingTime: `${Date.now() - startTime}ms`,
                changes: [
                    "保持tag字段原有内容不变",
                    `为每条记录添加factor字段，值为{"norm":"5","e5":"3"} (基于模版)`,
                    "为每条记录添加RBindex字段，提取Skid编号",
                    `为每条记录添加weight字段，值为${DEFAULT_CONFIG.weightValue}`,
                    `为每条记录添加area字段，值为${DEFAULT_CONFIG.areaValue} (区域标识)`,
                    `为每条记录添加sequence字段，值为${DEFAULT_CONFIG.sequenceValue} (区域内序号)`,
                    "采用模版metadata结构标准"
                ],
                extractionStats: {
                    stPattern: stats.stPatternCount,
                    simpleRbPattern: stats.simpleRbPatternCount,
                    tcTtPattern: stats.tcTtPatternCount,
                    elSlPattern: stats.elSlPatternCount,
                    complexRbPattern: stats.complexRbPatternCount,
                    ltWithRbPattern: stats.ltWithRbPatternCount,
                    ltPattern: stats.ltPatternCount,
                    stWithRbPattern: stats.stWithRbPatternCount,
                    fallbackPattern: stats.fallbackPatternCount,
                    noMatch: stats.noMatchCount
                }
            }
        };

        // 确保输出目录存在
        const outputDir = path.dirname(outputPath);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
            console.log(`📁 创建输出目录: ${outputDir}`);
        }

        // 保存新配置文件
        fs.writeFileSync(outputPath, JSON.stringify(newConfig, null, 2), 'utf8');
        
        const endTime = Date.now();
        
        console.log(`\n✅ Skid信息提取完成！v${DEFAULT_CONFIG.version} (基于模版优化)`);
        console.log(`📁 新配置文件: ${outputPath}`);
        console.log(`📊 处理记录数: ${stats.totalRecords}`);
        console.log(`✅ 成功转换: ${stats.successCount}`);
        console.log(`❌ 失败记录: ${stats.failureCount}`);
        console.log(`📈 成功率: ${((stats.successCount / stats.totalRecords) * 100).toFixed(2)}%`);
        console.log(`⏱️  处理时间: ${endTime - startTime}ms`);
        
        // 生成详细报告
        generateReport(stats);

        return true;

    } catch (error) {
        console.error('❌ 转换过程中出现错误:', error.message);
        console.error('💡 请检查输入文件格式是否正确');
        debugLog(`错误堆栈: ${error.stack}`, 'error');
        return false;
    }
}

// 主程序入口
function main() {
    const args = process.argv.slice(2);
    
    // 检查调试选项
    if (args.includes('--debug')) {
        DEFAULT_CONFIG.enableDebug = true;
        // 移除 --debug 参数
        const debugIndex = args.indexOf('--debug');
        args.splice(debugIndex, 1);
    }
    
    // 显示帮助
    if (args.includes('--help') || args.includes('-h')) {
        showHelp();
        return;
    }

    // 获取输入输出文件路径
    const inputFile = args[0] || DEFAULT_CONFIG.inputFile;
    const outputFile = args[1] || DEFAULT_CONFIG.outputFile;

    console.log(`🚀 Skid信息编号提取工具 v${DEFAULT_CONFIG.version} (基于模版优化)`);
    console.log('========================================================\n');

    if (DEFAULT_CONFIG.enableDebug) {
        console.log('🐛 调试模式已启用');
    }

    // 执行转换
    const success = transformConfig(inputFile, outputFile);
    
    if (success) {
        console.log('\n🎉 任务完成！');
        process.exit(0);
    } else {
        console.log('\n💥 任务失败！');
        process.exit(1);
    }
}

// 如果直接运行此脚本，执行主函数
if (require.main === module) {
    main();
}

// 导出函数供其他模块使用
module.exports = {
    extractSkidIndex,
    transformConfig,
    DEFAULT_CONFIG,
    TEMPLATE_METADATA
};
