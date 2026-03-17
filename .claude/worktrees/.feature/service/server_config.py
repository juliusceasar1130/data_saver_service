#!/usr/bin/env python3
"""
修改时间：2025年9月1日14点05分
修改内容：WebSocket服务器配置文件，支持动态修改参数

WebSocket服务器配置 - 支持后续修改
"""

# 服务器配置
SERVER_CONFIG = {
    # 网络配置
    "host": "0.0.0.0",          # 监听地址（0.0.0.0表示监听所有网卡）
    "port": 8088,               # 监听端口（可修改）
    "path": "/ws/emosweb",      # WebSocket路径
    
    # 数据推送配置
    "push_interval_min": 2,     # 最小推送间隔（秒）
    "push_interval_max": 5,     # 最大推送间隔（秒）
    
    # 数据模拟配置
    "enable_mock_data": True,   # 是否启用数据模拟
    "mock_data_variety": True,  # 是否生成多样化模拟数据
    
    # 调试配置
    "debug_mode": True,         # 是否显示调试信息
    "show_heartbeat": True,     # 是否显示心跳信息
}

# 设备配置 - 模拟数据的设备列表
DEVICE_CONFIG = {
    "L3FUB2": [
        ".L3FUB2_1A_1A005TC_1A005RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B025RB_1B025RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B030RB_1B030RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B035RB_1B035RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B040RB_1B040RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B045RB_1B045RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B055TC_1B055RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B065RB_1B065RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1C_16AS_1C060EH_1C060RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1C_16AS_1C100EL_1C100RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D110RB_1D110RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D115RB_1D115RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D120RB_1D120RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D125RB_1D125RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID",
        ".L3FUB2_1E_1E135RB_1E135RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1E_1E140RB_1E140RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1E_1E145RB_1E145RB.ILO.SD.I1030_RBDataSkidNo",
    ],
    "L3FKT1": [
        ".L3FKT1_1B_1B030TT_1B030RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1B_1B040LT_1B040RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1C_1C050LT_1C050RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1C_1C055RB_1C055RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1D_1D060LT_1D060RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1D_1DAS_1D325EL_1D325RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1D_1D080LT_1D080RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1E_1E090LT_1E090RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1E_1E095RB_1E095RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1AAS_1F105SL_1F105RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F120LT_1F120RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F125TT_1F125RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F155LT_1F155RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F160LT_1F160RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G175RB_1G175RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G180RB_1G180RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1BAS_1G185KT_1G185RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G190RB_1G190RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G195RB_1G195RB.IL.SD.I1030_RBDataSkidNo",
    ]
}

def get_config():
    """获取服务器配置"""
    return SERVER_CONFIG

def get_device_config():
    """获取设备配置"""
    return DEVICE_CONFIG

def update_config(**kwargs):
    """动态更新配置"""
    for key, value in kwargs.items():
        if key in SERVER_CONFIG:
            SERVER_CONFIG[key] = value
            print(f"✅ 配置已更新: {key} = {value}")
        else:
            print(f"❌ 未知配置项: {key}")

# 使用示例：
# from server_config import update_config
# update_config(port=8089, push_interval_min=1)
