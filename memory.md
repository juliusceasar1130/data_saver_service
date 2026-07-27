# Project Memory

## 说明

该文件用于保存项目级长期记忆（long-term memory），包括协作偏好、术语、背景、固定流程与注意事项。

使用原则：

- 只追加，不随意覆盖既有内容
- 如信息已失效，应追加“失效说明”或“更新说明”，不要直接删除原记录
- 需要修改代码、文档、流程时，优先同时参考 `AGENTS.md` 与本文件

## 当前长期约定

### 回复与沟通

- 默认使用中文回复
- 对重要专业术语补充英文，便于跨语言理解
- 输出结论时尽量直接、明确、可执行

### 修改约定

- 修改文件时应注明修改时间
- 需要说明主要修改内容
- 若不适合将修改记录写入源码文件，则在交付回复中说明

### 工作方式

- 优先理解现有代码与文档，再做修改
- 尽量避免不必要的大范围重构
- 不删除已有约定，新增内容采用追加整合方式

### 搜索约定

- 网页内容搜索可以使用 Web Fetch 或 tavily

## 项目背景

### 仓库

- 工作目录：`F:\000_dev\Python\workplace\savedatabase-postgresql_v2`

### 已知文档入口

- 根目录 `AGENTS.md`：项目协作规则

## 术语与偏好补充区

后续可在这里持续追加，例如：

- 常用业务术语
- 模块边界说明
- 常见命令
- 测试入口
- 提交规范

## 变更记录

### 2026-07-27 21:20 Asia/Shanghai

主要修改内容：

- 制定项目车数据集成与 `analytics_db` 匹配技术规格书 [project_vehicle_integration_spec.md](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/docs/project_car/project_vehicle_integration_spec.md)。
- 约定 FIS 项目车采集服务采用独立源数据库 `project_vehicle_db` 及数据表 `project_vehicle_orders`，实现与数仓解耦。
- 约定 `analytics_db` 维度表（`dim.carbody_registry` 与 `dim.dim_vehicle_profile`）仅扩充极简核心字段 `project_vehicle_no`。
- 约定数据匹配采用 14位 `vehicle_id` 包含 `pin_no` 条件：`POSITION(pvo.pin_no IN cr.vehicle_id) > 0`。

### 2026-07-03 20:20 Asia/Shanghai

主要修改内容：

- 针对本地 PostgreSQL 数据库 `analytics_db` 开展了结构与设计文档的 100% 比对确认，并起草了全量中文元数据注释注入脚本。
- 新增了数据库元数据注释部署脚本 [03_analytics_db_comments.sql](file:///f:/000_dev/Python/workplace/savedatabase-postgresql_v2/docs/03_analytics_db_comments.sql)。
- 完成了向 ODS/DIM/FCT/MART/META 共 5 个 Schema 注入数据库中文注释。由于 PostgreSQL 10.23 的物化视图限制，对物化视图进行了极简兼容性调整（仅为其本身进行表级注释注入，去除了由于 relkind 限制导致的列注释报错）。
- 梳理了车身唯一识别码（vehicle_id / serial_number / BODY_ID）及载具类型（carrier_type / type_code）的跨源一一对应业务等价性。
- 全局规范并统一了 Skid/Carrier 的中文术语为“雪橇/吊架”，精简了时间戳与主键的语义注释。

### 2026-05-22 15:28 Asia/Shanghai

主要修改内容：

- 使用通用设备参数配置文件转换脚本 `utily/convert_device_config_v2.py` 对蜡腔/烘房原始配置文件 `deviceConfig——wax.json` 进行了转换，并在 `utily/wax/` 目录下生成了标准的 `deviceConfig.wax.json`。
- 本次转换完美兼容了原配置中的 `"tagSkidNo"` 键，并无损地映射为标准的 `"tag_carrier_id"` 载具点位字段。
- 字段内容均按要求做好了规范化填充（如 `process_area` 默认 `"待填充"`, `carrier_type` 默认 `"Topcoat Skid"`, `remark` 默认 `""`），并移除冗余字段，使每个设备项各字段完美对齐 `deviceConfig_sample.json` 规范。
- 编写校验脚本 `validate_wax_config.py`，经 100% 深度校验，PLC控制器种类（11个）、设备总数（571个）、字段顺序及载具 ID 提取率成功达到 100%。

### 2026-05-22 10:22 Asia/Shanghai

主要修改内容：

- 深度合并分色线大配置文件 `deviceConfig.color.json` 至主配置文件 `deviceConfig.json` 中。
- 自动备份原文件为 `deviceConfig.json.bak`。
- 基于 `tag` 点位路径唯一标识符完成了重叠 PLC 设备的冲突去重和安全增量合并。
- 主配置文件总设备数成功扩充至 673 个，涵盖 9 个 PLC 控制器。
- 编写多套自动化验证测试脚本完成对各新旧文件的细粒度结构和键值顺序 100% 对齐校验，并已全部确认无损通过。

### 2026-05-22 10:05 Asia/Shanghai

主要修改内容：

- 优化通用设备配置文件转换脚本 `utily/convert_device_config_v2.py` 并对 L1/L2/L3 三个分色线设备参数配置文件（`deviceConfig1.json`、`deviceConfig2.json`、`deviceConfig3.json`）就地进行了转换和字段标准化对齐。
- 新增分色线设备参数配置文件合并脚本 `utily/merge_device_configs.py`，全自动将分色线各 PLC 配置合并输出为统一大配置文件 `xxxx.color.json` 和标准的 `deviceConfig.color.json`。
- 编写多套自动化验证测试脚本完成对各新旧文件的细粒度结构和键值顺序 100% 对齐校验，并已全部确认无损通过。

### 2026-03-23 00:00 Asia/Shanghai

主要修改内容：

- 新增项目级 `memory.md`
- 记录当前协作偏好、修改约定、搜索约定与文档入口
- 作为后续项目长期记忆的统一追加位置


## 可用技能

对代码优化和新增功能，你可以使用OpenSpec的技能进行开发
proposal / design / tasks / archive

## 依赖管理

新增代码涉及第三方包的话，请更新requirements.txt
