import json

# 读取原始 deviceConfig.json
with open(r'F:\000_dev\Python\workplace\savedatabase-postgresql_v2\deviceConfig.json', 'r', encoding='utf-8') as f:
    orig = json.load(f)

# 读取 PTED 合并文件
with open(r'F:\000_dev\Python\workplace\savedatabase-postgresql_v2\utily\PTED\deviceConfig_merged.json', 'r', encoding='utf-8') as f:
    pted = json.load(f)

# 追加 config
pted_plcs_added = []
for plc, entries in pted['config'].items():
    if plc in orig['config']:
        print(f'  {plc}: 已存在 (原始 {len(orig["config"][plc])} 条)，跳过')
    else:
        orig['config'][plc] = entries
        pted_plcs_added.append(plc)
        print(f'  {plc}: 追加 {len(entries)} 条')

# 更新 metadata
plc_list = sorted(orig['config'].keys())
orig['metadata']['deviceTypes'] = plc_list
orig['metadata']['totalDevices'] = sum(len(v) for v in orig['config'].values())

# 写回
with open(r'F:\000_dev\Python\workplace\savedatabase-postgresql_v2\deviceConfig.json', 'w', encoding='utf-8') as f:
    json.dump(orig, f, ensure_ascii=False, indent=2)

print(f'\n追加完成！新增 {len(pted_plcs_added)} 个 PLC')
print(f'新增 PLC: {pted_plcs_added}')
print(f'更新后总计: {orig["metadata"]["totalDevices"]} 条 / {len(plc_list)} 个 PLC')
