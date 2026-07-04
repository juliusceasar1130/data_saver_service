import json, os

dir_path = r'F:\000_dev\Python\workplace\savedatabase-postgresql_v2\utily\PTED'
files = [
    'deviceConfig_l3f01.json',
    'deviceConfig_l3f02.json',
    'deviceConfig_l3f03.json',
    'deviceConfig_l3f04.json',
    'deviceConfig_l3f21.json',
    'deviceConfig_l3f23.json',
    'deviceConfig_l3fkt1.json',
    'deviceConfig_l3fkt2.json',
]

# 读取第一个文件作为模板
merged = None
total_count = 0

for fname in files:
    fpath = os.path.join(dir_path, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if merged is None:
        merged = data
    else:
        # 合并 config 字典
        for plc_key, entries in data['config'].items():
            if plc_key in merged['config']:
                merged['config'][plc_key].extend(entries)
            else:
                merged['config'][plc_key] = entries

# 更新 metadata
plc_list = sorted(merged['config'].keys())
merged['metadata']['deviceTypes'] = plc_list
merged['metadata']['totalDevices'] = sum(len(v) for v in merged['config'].values())

# 写出到合并后的文件
output_path = os.path.join(dir_path, 'deviceConfig_merged.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f'合并完成！共 {len(plc_list)} 个 PLC，{merged["metadata"]["totalDevices"]} 条记录')
print(f'PLC 列表: {plc_list}')
print(f'输出文件: {output_path}')
