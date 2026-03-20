#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
转换 deviceConfig_l2_fcc.json 文件格式
时间: 2026-03-20
主要修改内容:
  1. 将 DataSkidNo 字段重命名为 tag_carrier_id
  2. 添加 remark 字段（空字符串）
  3. 添加 process_area 字段（固定为 "L2面漆喷房和烘房"）
  4. 添加 carrier_type 字段（固定为 "Topcoat Skid"）
  5. 移除 factor, weight, area, sequence 字段
  6. 按照指定键顺序对齐: id, type, plc, tag, RBindex, remark, process_area, carrier_type, tag_carrier_id
"""

import json
from collections import OrderedDict

def convert_config(input_file: str, output_file: str):
    """转换设备配置文件格式"""

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 新的配置结构
    new_config = {}

    for plc_name, devices in data.get('config', {}).items():
        new_devices = []

        for device in devices:
            # 按照指定顺序创建新的设备字典
            new_device = OrderedDict([
                ("id", device.get("id", "")),
                ("type", device.get("type", "advise")),
                ("plc", device.get("plc", "")),
                ("tag", device.get("tag", "")),
                ("RBindex", device.get("RBindex", "")),
                ("remark", ""),
                ("process_area", "L2面漆喷房和烘房"),
                ("carrier_type", "Topcoat Skid"),
                ("tag_carrier_id", device.get("DataSkidNo", ""))
            ])
            new_devices.append(new_device)

        new_config[plc_name] = new_devices

    # 构建新的完整数据结构
    new_data = {
        "description": data.get("description", ""),
        "version": "2.0.0",
        "lastModified": "2026-03-20",
        "config": new_config,
        "metadata": {
            "totalDevices": sum(len(devices) for devices in new_config.values()),
            "deviceTypes": list(new_config.keys()),
            "configSchema": {
                "id": "设备唯一标识符",
                "type": "消息通信类型",
                "plc": "PLC控制器标识",
                "tag": "数据点位路径",
                "RBindex": "滚床编号，提取自tag路径",
                "remark": "备注信息",
                "process_area": "工艺区域",
                "carrier_type": "载具类型",
                "tag_carrier_id": "滑撬号码标签路径"
            }
        }
    }

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"转换完成！共处理 {new_data['metadata']['totalDevices']} 个设备")
    print(f"输出文件: {output_file}")

if __name__ == "__main__":
    input_file = "../deviceConfig1.json"
    output_file = "../deviceConfig2.json"
    convert_config(input_file, output_file)
