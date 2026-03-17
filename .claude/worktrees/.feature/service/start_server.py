#!/usr/bin/env python3
"""
修改时间：2025年9月1日14点05分
修改内容：WebSocket服务器启动脚本，使用配置文件

WebSocket服务器启动脚本 - 支持配置文件
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List

# 导入配置
try:
    from server_config import get_config, get_device_config
    config = get_config()
    device_config = get_device_config()
    print("✅ 已加载配置文件")
except ImportError:
    # 如果没有配置文件，使用默认配置
    print("⚠️  未找到配置文件，使用默认配置")
    config = {
        "host": "0.0.0.0",
        "port": 8088,
        "path": "/ws/emosweb",
        "push_interval_min": 2,
        "push_interval_max": 5,
        "debug_mode": True,
        "show_heartbeat": True,
    }
    device_config = {
        "L3FUB2": [".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"],
        "L3FKT1": [".L3FKT1_1F_1F110TT_1F110LT.IL.SD.I1030_RBDataSkidNo"]
    }

# 全局变量
connected_clients: Dict[websockets.WebSocketServerProtocol, Set[str]] = {}
device_subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}


def generate_mock_data(plc: str, tag: str) -> str:
    """生成模拟数据"""
    if "BodyID" in tag:
        return f"{random.randint(100000, 999999)}{random.choice(['N', 'S'])}{random.randint(10, 99)}Y{random.randint(1, 9)}T{random.randint(1, 9)}TMQ{random.choice(['A', 'B', 'C'])}{random.randint(100, 999)}-"
    elif "SkidNo" in tag:
        return str(random.randint(1000, 9999))
    elif "TT" in tag:
        return f"{random.uniform(15.0, 35.0):.1f}"
    elif "LT" in tag:
        return f"{random.uniform(0.0, 100.0):.1f}"
    else:
        return str(random.randint(1, 1000))


def create_data_message(plc: str, tag: str) -> dict:
    """创建数据推送消息"""
    now = datetime.now(timezone(timedelta(hours=8)))
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+08:00"
    
    return {
        "type": "dataChange",
        "id": "",
        "tag": f"{plc}{tag}",
        "ts": timestamp,
        "value": generate_mock_data(plc, tag),
        "quality": 192,
        "source": "PythonSimulator",
        "userRights": 0
    }


async def handle_client_message(websocket, message_data: dict):
    """处理客户端消息"""
    try:
        message_type = message_data.get("type", "")
        
        if message_type == "advise":
            plc = message_data.get("plc", "")
            tag = message_data.get("tag", "")
            
            if plc and tag:
                device_key = f"{plc}{tag}"
                
                if websocket not in connected_clients:
                    connected_clients[websocket] = set()
                connected_clients[websocket].add(device_key)
                
                if device_key not in device_subscriptions:
                    device_subscriptions[device_key] = set()
                device_subscriptions[device_key].add(websocket)
                
                if config.get("debug_mode", True):
                    print(f"✅ 客户端订阅设备: {device_key}")
                
        elif message_type == "info" and message_data.get("info") == "alive":
            if config.get("show_heartbeat", True):
                print(f"💓 收到客户端心跳: {websocket.remote_address}")
                
    except Exception as e:
        print(f"❌ 处理客户端消息失败: {e}")


async def handle_websocket(websocket, path):
    """处理WebSocket连接"""
    client_address = websocket.remote_address
    
    # 检查WebSocket路径是否匹配
    expected_path = config.get("path", "/ws/emosweb")
    if path != expected_path:
        print(f"❌ 无效的WebSocket路径: {path}, 期望: {expected_path}")
        await websocket.close(code=1008, reason="Invalid path")
        return
    
    print(f"🔗 新客户端连接: {client_address}")
    
    connected_clients[websocket] = set()
    
    try:
        async for message in websocket:
            try:
                message_data = json.loads(message)
                if config.get("debug_mode", True):
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
        cleanup_client_connection(websocket)


def cleanup_client_connection(websocket):
    """清理客户端连接和相关订阅"""
    if websocket in connected_clients:
        subscribed_devices = connected_clients[websocket]
        for device_key in subscribed_devices:
            if device_key in device_subscriptions:
                device_subscriptions[device_key].discard(websocket)
                if not device_subscriptions[device_key]:
                    del device_subscriptions[device_key]
        
        del connected_clients[websocket]
        if config.get("debug_mode", True):
            print(f"🧹 已清理客户端连接和订阅")


async def data_push_worker():
    """数据推送工作线程"""
    print("🚀 数据推送工作线程已启动")
    
    while True:
        try:
            if device_subscriptions:
                device_keys = list(device_subscriptions.keys())
                device_key = random.choice(device_keys)
                
                if "." in device_key:
                    plc = device_key.split(".")[0]
                    tag = "." + ".".join(device_key.split(".")[1:])
                    
                    data_message = create_data_message(plc, tag)
                    message_json = json.dumps(data_message)
                    
                    clients_to_remove = []
                    for client in device_subscriptions[device_key].copy():
                        try:
                            await client.send(message_json)
                            if config.get("debug_mode", True):
                                print(f"📤 推送数据: {device_key} -> {data_message['value']}")
                        except websockets.exceptions.ConnectionClosed:
                            clients_to_remove.append(client)
                        except Exception as e:
                            print(f"❌ 推送数据失败: {e}")
                            clients_to_remove.append(client)
                    
                    for client in clients_to_remove:
                        cleanup_client_connection(client)
            
            await asyncio.sleep(random.uniform(
                config.get("push_interval_min", 2), 
                config.get("push_interval_max", 5)
            ))
            
        except Exception as e:
            print(f"❌ 数据推送工作线程错误: {e}")
            await asyncio.sleep(1)


async def main():
    """主函数"""
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 8088)
    path = config.get("path", "/ws/emosweb")
    
    print(f"🌟 WebSocket服务器启动中...")
    print(f"📡 监听地址: {host}:{port}")
    print(f"📍 WebSocket路径: {path}")
    print(f"⏱️  数据推送间隔: {config.get('push_interval_min', 2)}-{config.get('push_interval_max', 5)}秒")
    print("=" * 50)
    
    asyncio.create_task(data_push_worker())
    
    async with websockets.serve(handle_websocket, host, port):
        print(f"✅ WebSocket服务器已启动!")
        print(f"🔗 客户端连接地址: ws://{host}:{port}{path}")
        print("按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
