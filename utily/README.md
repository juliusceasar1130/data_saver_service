# 设备配置同步工具 (sync_skid_no.py)

该工具用于在设备配置重构/同步时，方便地将旧版或带数据的 JSON 文件中的 `DataSkidNo` 字段数据，按 `tag` 对应的键值精确还原到目标 JSON 的 `tag_skidNo` 字段上。

---

## 核心特性
1. **基于标识符精确匹配**: 读取源文件后生成缓存字典，确保无论源与目标配置顺序是否变化都可以正确映射。
2. **零格式破坏**: 该程序不再通过 `json.loads` 到 `json.dumps` 循环处理目标文件（这通常会丢失缩进、重排结构），而是利用严格的字符串行正则遍历匹配完成替换，**完美保留原 JSON 文件的视觉格式和非关联键值的默认态（如 `""` 模板）**。
3. **安全保存机制**: 提供原位更新与导出新副本的双重模式。

## 先决条件
- Python 3.6+ 环境
- JSON 文档字段需采用单行结构格式（如普通的 prettier/格式化后样式）

## 使用说明

打开终端并进入到此文件夹（或在任意目录引用此脚本），运行以下命令：

### 1. 就地更新 (覆盖目标文件)
如果确认进行直接覆盖（推荐搭配 Git 使用）：
```bash
python sync_skid_no.py -s ../deviceConfig_org.json -t ../deviceConfig.json
```
注意：使用此命令，工具将直接读取 `deviceConfig.json` 并在更新完内容后重新覆盖写回该文件。

### 2. 另存副本更新 (保留原文件)
如果你希望在测试时生成一个全新的文件而不是覆盖原文件，可以使用 `-o` 或 `--output` 指令：
```bash
python sync_skid_no.py -s ../deviceConfig_org.json -t ../deviceConfig.json -o ../deviceConfig_updated.json
```

### 命令参数详解
可以通过 `--help` 获取完整帮助。
```bash
python sync_skid_no.py -h
```
- `-s, --source` ： 源文件路径（带正确 `DataSkidNo` 的配置）。
- `-t, --target` ： 目标文件路径（需要写入 `tag_skidNo` 的配置）。
- `-o, --output` ：（可选）输出结果的文件名路径。当未被指定时，结果直接覆盖 target 路径。
