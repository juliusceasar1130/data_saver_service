#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
转换 deviceConfig.json 文件格式
优化时间: 2026-05-22
主要修改内容:
  1. 将 DataSkidNo 字段重命名为 tag_carrier_id
  2. 添加 remark 字段（支持自定义，默认空字符串）
  3. 添加 process_area 字段（支持自定义，默认"待填充"）
  4. 添加 carrier_type 字段（支持自定义，默认"Topcoat Skid"）
  5. 移除 factor, weight, area, sequence 字段
  6. 按照指定键顺序对齐: id, type, plc, tag, RBindex, remark, process_area, carrier_type, tag_carrier_id
  7. 移除顶层多余的 factor 字段，保留 description, version, lastModified, config, metadata 等核心段落
  8. 对齐 metadata 描述内容至 deviceConfig_sample.json 的标准
  9. 支持通用命令行参数和批量文件转换，增强复用性
"""

import os
import json
import argparse
from collections import OrderedDict
from datetime import datetime

def convert_config(
    input_file: str, 
    output_file: str, 
    process_area: str = "待填充", 
    carrier_type: str = "Topcoat Skid",
    remark: str = "",
    version: str = "2.4.0",
    last_modified: str = None
):
    """转换单个设备参数配置文件的格式"""
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        return False

    print(f"正在转换: {input_file} -> {output_file} ...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 转换 config 字典中的每个设备条目
    new_config = {}
    device_types = set()
    total_devices = 0

    for config_key, devices in data.get('config', {}).items():
        new_devices = []
        for device in devices:
            # 记录设备 plc 类型
            plc_type = device.get("plc", "")
            if plc_type:
                device_types.add(plc_type)
            
            # 按照 sample 样式的指定顺序创建设备字典
            new_device = OrderedDict([
                ("id", device.get("id", "")),
                ("type", device.get("type", "advise")),
                ("plc", plc_type),
                ("tag", device.get("tag", "")),
                ("RBindex", device.get("RBindex", "")),
                ("remark", remark),
                ("process_area", process_area),
                ("carrier_type", carrier_type),
                ("tag_carrier_id", device.get("DataSkidNo", device.get("tagSkidNo", device.get("tag_carrier_id", ""))))
            ])
            new_devices.append(new_device)
            total_devices += 1

        new_config[config_key] = new_devices

    # 2. 自动生成 lastModified 日期
    if last_modified is None:
        last_modified = datetime.now().strftime("%Y年%m月%d日")

    # 3. 构建新的完整数据结构，严格对齐 sample 样式
    new_data = OrderedDict([
        ("description", data.get("description", "设备参数配置文件")),
        ("version", version),
        ("lastModified", last_modified),
        ("config", new_config),
        ("metadata", OrderedDict([
            ("totalDevices", total_devices),
            ("deviceTypes", sorted(list(device_types))),
            ("configSchema", OrderedDict([
                ("id", "设备唯一标识符"),
                ("type", "消息通信类型"),
                ("plc", "PLC控制器标识"),
                ("tag", "车身信息数据点位路径唯一标识符"),
                ("RBindex", "滚床索引"),
                ("remark", "备注说明"),
                ("tag_carrier_id", "雪橇信息数据点位路径唯一标识符"),
                ("carrier_type", "载具类型"),
                ("process_area", "工艺段名称")
            ]))
        ]))
    ])

    # 4. 写入新文件或就地覆盖
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"  转换完成！共处理 {total_devices} 个设备，PLC类型: {sorted(list(device_types))}")
    return True

def main():
    parser = argparse.ArgumentParser(description="通用设备配置文件转换工具 (对齐 deviceConfig_sample.json 样式)")
    parser.add_argument("--input", "-i", nargs="+", help="输入 JSON 文件路径，支持多个文件批量处理")
    parser.add_argument("--output", "-o", nargs="+", help="输出 JSON 文件路径（可选，如果不指定则就地覆盖输入文件）")
    parser.add_argument("--process-area", "-p", default="待填充", help="填充的 process_area 字段内容，默认：'待填充'")
    parser.add_argument("--carrier-type", "-c", default="Topcoat Skid", help="填充的 carrier_type 字段内容，默认：'Topcoat Skid'")
    parser.add_argument("--remark", "-r", default="", help="填充的 remark 字段内容，默认为空字符串")
    parser.add_argument("--version-str", "-v", default="2.4.0", help="顶层 version 版本号，默认：'2.4.0'")
    parser.add_argument("--last-modified", "-m", help="顶层 lastModified 修改日期，如果不指定则为当前日期，例如：'2026年03月18日'")

    args = parser.parse_args()

    # 如果是通过命令行运行，但没有提供参数，则在当前脚本默认批量转换 deviceConfig1.json, 2.json, 3.json
    if not args.input:
        # 默认处理项目中的 deviceConfig1.json, deviceConfig2.json, deviceConfig3.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_files = [
            os.path.join(base_dir, "deviceConfig1.json"),
            os.path.join(base_dir, "deviceConfig2.json"),
            os.path.join(base_dir, "deviceConfig3.json")
        ]
        print("未指定输入文件，将执行默认批量转换：deviceConfig1.json, deviceConfig2.json, deviceConfig3.json")
        for filepath in default_files:
            convert_config(
                input_file=filepath,
                output_file=filepath, # 就地覆盖
                process_area="待填充",
                carrier_type="Topcoat Skid",
                remark="",
                version="2.4.0",
                last_modified=args.last_modified
            )
    else:
        # 处理命令行指定的输入/输出文件
        inputs = args.input
        outputs = args.output if args.output else inputs
        
        if len(outputs) != len(inputs):
            print("错误: 输入文件数量与输出文件数量不一致！")
            return

        for infile, outfile in zip(inputs, outputs):
            convert_config(
                input_file=infile,
                output_file=outfile,
                process_area=args.process_area,
                carrier_type=args.carrier_type,
                remark=args.remark,
                version=args.version_str,
                last_modified=args.last_modified
            )

if __name__ == "__main__":
    main()
