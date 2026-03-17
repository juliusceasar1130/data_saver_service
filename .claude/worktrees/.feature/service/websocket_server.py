#!/usr/bin/env python3
"""
修改时间：2025年9月1日14点05分
修改内容：创建WebSocket服务器主程序，支持设备订阅和数据推送

简洁的WebSocket服务器 - 工业数据采集系统演示
- 端口：8088（可配置）
- 路径：/ws/emosweb
- 功能：设备订阅、数据模拟推送、心跳保活
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List
import logging

# 配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8088
WEBSOCKET_PATH = "/ws/emosweb"
DATA_PUSH_MIN_INTERVAL = 2  # 最小推送间隔（秒）
DATA_PUSH_MAX_INTERVAL = 5  # 最大推送间隔（秒）

# 全局变量
connected_clients: Dict[websockets.WebSocketServerProtocol, Set[str]] = {}  # 客户端及其订阅的设备
device_subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}  # 设备及其订阅的客户端

# 模拟数据配置 - 从前端配置文件提取的设备信息
DEVICE_CONFIG = {
    "L3FUB2": [
        ".L3FUB2_1A_1A005TC_1A005RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B025RB_1B025RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1B_1B030RB_1B030RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D110RB_1D110RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D115RB_1D115RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D120RB_1D120RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D125RB_1D125RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"
    ],
    "L3FKT1": [
        ".L3FKT1_1B_1B030TT_1B030RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1B_1B040LT_1B040RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1C_1C050LT_1C050RB.ILO.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1C_1C055RB_1C055RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1D_1D060LT_1D060RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F120LT_1F120RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1F_1F125TT_1F125RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G175RB_1G175RB.IL.SD.I1030_RBDataSkidNo",
        ".L3FKT1_1G_1G180RB_1G180RB.IL.SD.I1030_RBDataSkidNo"
    ]
}


def generate_mock_data(plc: str, tag: str) -> str:
    """生成模拟数据"""
    # 根据不同的点位类型生成不同的模拟数据
    if "BodyID" in tag:
        # 车身ID - 生成类似真实格式的字符串
        return f"{random.randint(100000, 999999)}{random.choice(['N', 'S'])}{random.randint(10, 99)}Y{random.randint(1, 9)}T{random.randint(1, 9)}TMQ{random.choice(['A', 'B', 'C'])}{random.randint(100, 999)}-"
    elif "SkidNo" in tag:
        # 滑橇编号 - 生成数字
        return str(random.randint(1000, 9999))
    elif "TT" in tag:
        # 温度传感器 - 生成温度值
        return f"{random.uniform(15.0, 35.0):.1f}"
    elif "LT" in tag:
        # 液位传感器 - 生成液位值
        return f"{random.uniform(0.0, 100.0):.1f}"
    else:
        # 其他类型 - 生成随机数值
        return str(random.randint(1, 1000))


def create_data_message(plc: str, tag: str) -> dict:
    """创建数据推送消息"""
    # 获取当前时间（东八区）
    now = datetime.now(timezone(timedelta(hours=8)))
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+08:00"
    
    return {
        "type": "dataChange",
        "id": "",
        "tag": f"{plc}{tag}",  # 格式：L3FUB2.L3FUB2_xxx
        "ts": timestamp,
        "value": generate_mock_data(plc, tag),
        "quality": 192,  # OPC质量值：192表示好质量
        "source": "PythonSimulator",
        "userRights": 0
    }


async def handle_client_message(websocket, message_data: dict):
    """处理客户端消息"""
    try:
        message_type = message_data.get("type", "")
        
        if message_type == "advise":
            # 处理设备订阅请求
            plc = message_data.get("plc", "")
            tag = message_data.get("tag", "")
            
            if plc and tag:
                device_key = f"{plc}{tag}"
                
                # 添加到客户端订阅列表
                if websocket not in connected_clients:
                    connected_clients[websocket] = set()
                connected_clients[websocket].add(device_key)
                
                # 添加到设备订阅列表
                if device_key not in device_subscriptions:
                    device_subscriptions[device_key] = set()
                device_subscriptions[device_key].add(websocket)
                
                print(f"✅ 客户端订阅设备: {device_key}")
                
        elif message_type == "info" and message_data.get("info") == "alive":
            # 处理心跳消息
            print(f"💓 收到客户端心跳: {websocket.remote_address}")
            
    except Exception as e:
        print(f"❌ 处理客户端消息失败: {e}")


async def handle_websocket(websocket, path):
    """处理WebSocket连接"""
    client_address = websocket.remote_address
    
    # 检查WebSocket路径是否匹配
    if path != WEBSOCKET_PATH:
        print(f"❌ 无效的WebSocket路径: {path}, 期望: {WEBSOCKET_PATH}")
        await websocket.close(code=1008, reason="Invalid path")
        return
    
    print(f"🔗 新客户端连接: {client_address}")
    
    # 初始化客户端连接
    connected_clients[websocket] = set()
    
    try:
        async for message in websocket:
            try:
                message_data = json.loads(message)
                print(f"📨 收到消息: {message_data}")
                await handle_client_message(websocket, message_data)
            except json.JSONDecodeError:
                print(f"❌ 无效的JSON消息: {message}")
            except Exception as e:
                print(f"❌ 处理消息失败: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 客户端断开连接: {client_address}")
    except Exception as e:
        print(f"❌ WebSocket连接错误: {e}")
    finally:
        # 清理客户端连接和订阅
        cleanup_client_connection(websocket)


def cleanup_client_connection(websocket):
    """清理客户端连接和相关订阅"""
    if websocket in connected_clients:
        # 从设备订阅中移除此客户端
        subscribed_devices = connected_clients[websocket]
        for device_key in subscribed_devices:
            if device_key in device_subscriptions:
                device_subscriptions[device_key].discard(websocket)
                if not device_subscriptions[device_key]:
                    del device_subscriptions[device_key]
        
        # 移除客户端连接记录
        del connected_clients[websocket]
        print(f"🧹 已清理客户端连接和订阅")


async def data_push_worker():
    """数据推送工作线程"""
    print("🚀 数据推送工作线程已启动")
    
    while True:
        try:
            if device_subscriptions:
                # 随机选择一个有订阅的设备推送数据
                device_keys = list(device_subscriptions.keys())
                device_key = random.choice(device_keys)
                
                # 解析设备信息
                # device_key格式: "L3FUB2.L3FUB2_xxx" 
                if "." in device_key:
                    plc = device_key.split(".")[0]
                    tag = "." + ".".join(device_key.split(".")[1:])
                    
                    # 创建数据消息
                    data_message = create_data_message(plc, tag)
                    message_json = json.dumps(data_message)
                    
                    # 推送给所有订阅此设备的客户端
                    clients_to_remove = []
                    for client in device_subscriptions[device_key].copy():
                        try:
                            await client.send(message_json)
                            print(f"📤 推送数据到客户端: {device_key} -> {data_message['value']}")
                        except websockets.exceptions.ConnectionClosed:
                            clients_to_remove.append(client)
                        except Exception as e:
                            print(f"❌ 推送数据失败: {e}")
                            clients_to_remove.append(client)
                    
                    # 清理断开的连接
                    for client in clients_to_remove:
                        cleanup_client_connection(client)
            
            # 随机等待间隔
            await asyncio.sleep(random.uniform(DATA_PUSH_MIN_INTERVAL, DATA_PUSH_MAX_INTERVAL))
            
        except Exception as e:
            print(f"❌ 数据推送工作线程错误: {e}")
            await asyncio.sleep(1)


async def main():
    """主函数"""
    print(f"🌟 WebSocket服务器启动中...")
    print(f"📡 监听地址: {SERVER_HOST}:{SERVER_PORT}")
    print(f"📍 WebSocket路径: {WEBSOCKET_PATH}")
    print(f"⏱️  数据推送间隔: {DATA_PUSH_MIN_INTERVAL}-{DATA_PUSH_MAX_INTERVAL}秒")
    print("=" * 50)
    
    # 启动数据推送工作线程
    asyncio.create_task(data_push_worker())
    
    # 启动WebSocket服务器
    async with websockets.serve(
        handle_websocket, 
        SERVER_HOST, 
        SERVER_PORT
    ):
        print(f"✅ WebSocket服务器已启动!")
        print(f"🔗 客户端连接地址: ws://{SERVER_HOST}:{SERVER_PORT}{WEBSOCKET_PATH}")
        print("按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 保持服务器运行
        await asyncio.Future()  # 永远运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
