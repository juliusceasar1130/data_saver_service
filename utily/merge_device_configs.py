#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
合并分色线配置文件（deviceConfig1.json, deviceConfig2.json, deviceConfig3.json）
时间: 2026-05-22
主要内容:
  1. 读取三个分色线设备参数配置文件
  2. 提取 config 部分的 PLC 配置并合并为一个大字典
  3. 重新计算 metadata 中的 totalDevices 和 deviceTypes
  4. 整合顶级元数据描述信息
  5. 格式化输出为规范化 JSON 文件，包括指定的 xxxx.color.json 和标准的 deviceConfig.color.json
"""

import os
import json

def merge_configs(input_files, output_files, description="设备参数配置文件 - 分色线全区域合并版本 (L1/L2/L3分色线)"):
    print("开始合并设备参数配置文件...")
    merged_config = {}
    
    # 按照设备字段的标准顺序重新构建设备字典，以确保格式 100% 对齐规范
    field_order = [
        "id", "type", "plc", "tag", "RBindex", "remark", "process_area", "carrier_type", "tag_carrier_id"
    ]
    
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"[ERROR] 输入文件不存在: {file_path}")
            return False
            
        print(f"读取文件: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        config_data = data.get("config", {})
        for plc, devices in config_data.items():
            ordered_devices = []
            for dev in devices:
                # 按照严格排序重新构建字典
                ordered_dev = {key: dev.get(key, "") for key in field_order}
                ordered_devices.append(ordered_dev)
            
            merged_config[plc] = ordered_devices
            print(f"  已合并 PLC: {plc}，设备数: {len(ordered_devices)}")
            
    # 计算总数与PLC类型列表
    total_devices = sum(len(devices) for devices in merged_config.values())
    device_types = list(merged_config.keys())
    
    # 构建最终合并的对象
    merged_data = {
        "description": description,
        "version": "2.4.0",
        "lastModified": "2026年05月22日",
        "config": merged_config,
        "metadata": {
            "totalDevices": total_devices,
            "deviceTypes": device_types,
            "configSchema": {
                "id": "设备唯一标识符",
                "type": "消息通信类型",
                "plc": "PLC控制器标识",
                "tag": "车身信息数据点位路径唯一标识符",
                "RBindex": "滚床索引",
                "remark": "备注说明",
                "tag_carrier_id": "雪橇信息数据点位路径唯一标识符",
                "carrier_type": "载具类型",
                "process_area": "工艺段名称"
            }
        }
    }
    
    # 输出合并后的文件
    for out_file in output_files:
        print(f"正在保存合并结果至: {out_file}")
        # 创建父目录（如果不存在）
        os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
    print(f"合并任务全部成功！总共合并了 {len(input_files)} 个文件，包含 {len(device_types)} 个 PLC，共计 {total_devices} 个设备。")
    return True

if __name__ == "__main__":
    # 定义基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    inputs = [
        os.path.join(base_dir, "deviceConfig1.json"),
        os.path.join(base_dir, "deviceConfig2.json"),
        os.path.join(base_dir, "deviceConfig3.json")
    ]
    
    outputs = [
        os.path.join(base_dir, "deviceConfig.color.json"),
        os.path.join(base_dir, "xxxx.color.json")
    ]
    
    merge_configs(inputs, outputs)
