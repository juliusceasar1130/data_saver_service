#!/usr/bin/env python3
"""
修改时间：2025年1月19日
修改内容：创建WebSocket服务器V2版本，generate_mock_data生成30字符固定格式字符串

WebSocket服务器 V2 - 工业数据采集系统演示
- 端口：8088（可配置）
- 路径：/ws/emosweb
- 功能：设备订阅、数据模拟推送、心跳保活
- 数据格式：30字符固定格式
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
      "L3F13": [
          ".L3F13_1A_1A010LT_1A010RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A025LT_1A025RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A030LT_1A030RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A035RB_1A035RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A090RB_1A090RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A150RB_1A150RB.IL.SD.M1003_BodyID",
          ".L3F13_1A_1A280RB_1A280RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B040RB_1B040RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B045RB_1B045RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B050RB_1B050RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B055RB_1B055RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B060RB_1B060RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B095RB_1B095RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B100RB_1B100RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B105RB_1B105RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B110RB_1B110RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B115RB_1B115RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B155RB_1B155RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B160RB_1B160RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B165RB_1B165RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B170RB_1B170RB.IL.SD.M1003_BodyID",
          ".L3F13_1B_1B175RB_1B175RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C065RB_1C065RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C070RB_1C070RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C075RB_1C075RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C080RB_1C080RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C120RB_1C120RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C125RB_1C125RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C130RB_1C130RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C135RB_1C135RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C180RB_1C180RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C185RB_1C185RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C190RB_1C190RB.IL.SD.M1003_BodyID",
          ".L3F13_1C_1C195RB_1C195RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D085RB_1D085RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D140RB_1D140RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D200RB_1D200RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D215LT_1D215RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D220LT_1D220RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D225LT_1D225RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D240LT_1D240RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D260RB_1D260RB.IL.SD.M1003_BodyID",
          ".L3F13_1D_1D261RB_1D261RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E285RB_1E285RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E290RB_1E290RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E295RB_1E295RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E300RB_1E300RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E305RB_1E305RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E310RB_1E310RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E315RB_1E315RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E375RB_1E375RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E380RB_1E380RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E385RB_1E385RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E390RB_1E390RB.IL.SD.M1003_BodyID",
          ".L3F13_1E_1E395RB_1E395RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F320RB_1F320RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F330LT_1F330RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F335LT_1F335RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F340LT_1F340RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F355LT_1F355RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F360LT_1F360RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F370RB_1F370RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F405RB_1F405RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F450RB_1F450RB.IL.SD.M1003_BodyID",
          ".L3F13_1F_1F485RB_1F485RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G410RB_1G410RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G415RB_1G415RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G420RB_1G420RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G425RB_1G425RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G430RB_1G430RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G455RB_1G455RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G460RB_1G460RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G465RB_1G465RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G470RB_1G470RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G475RB_1G475RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G490RB_1G490RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G495RB_1G495RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G500RB_1G500RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G505RB_1G505RB.IL.SD.M1003_BodyID",
          ".L3F13_1G_1G510RB_1G510RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H400RB_1H400RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H435RB_1H435RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H480RB_1H480RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H515RB_1H515RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H525LT_1H525RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H530LT_1H530RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H545LT_1H545RB.IL.SD.M1003_BodyID",
          ".L3F13_1H_1H550LT_1H550RB.IL.SD.M1003_BodyID"
      ],
      "L3FCC2": [
          ".L3FCC2_1L_1L270TC_1L270RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1L_1L275RB_1L275RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M280TT_1M280RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M285RB_1M285RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M295RB_1M295RB.ILO.SD.M1003_BodyID",
          ".L3FCC2_1M_1M300RB_1M300RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M305RB_1M305RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M310RB_1M310RB.IL.SD.M1003_BodyID",
          ".L3FCC2_1M_1M315RB_1M315RB.IL.SD.M1003_BodyID"
      ]
  }

def generate_mock_data(plc: str, tag: str) -> str:
    """
    生成30字符固定格式的模拟数据
    格式说明：
    格式1：
    - 0-5: "782026"
    - 6-13: 8 random digits
    - 14-18: "2N211" or "VS21J"
    - 19-22: "2LA1" or "2T2T"
    - 23-25: "MLB" or "MQB"
    - 26: "0" or "1"
    - 27: "0", "1", or "2"
    - 28: "1"
    - 29: "-"

    格式2：
    - 30个"-"组成的字符串
    """
    # 20%的概率生成30个横杠
    if random.random() < 0.2:
        return "-" * 30

    part1 = "782026"
    part2 = f"{random.randint(10000000, 99999999)}"
    part3 = random.choice(["2N211", "VS21J"])
    part4 = random.choice(["2LA1", "2T2T"])
    part5 = random.choice(["MLB", "MQB"])
    part6 = random.choice(["0", "1"])
    part7 = random.choice(["0", "1", "2"])
    part8 = "1"
    part9 = "-"

    return part1 + part2 + part3 + part4 + part5 + part6 + part7 + part8 + part9


def create_data_message(plc: str, tag: str) -> dict:
    """创建数据推送消息"""
    # 获取当前时间（东八区）
    now = datetime.now(timezone(timedelta(hours=8)))
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+08:00"

    return {
        "type": "dataChange",
        "id": "",
        "tag": tag,  # 格式：.L3F13_xxx (与数据库存储格式一致)
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
                device_key = tag  # 直接使用 tag 作为设备键，格式：.L3F13_xxx

                # 添加到客户端订阅列表
                if websocket not in connected_clients:
                    connected_clients[websocket] = set()
                connected_clients[websocket].add(device_key)

                # 添加到设备订阅列表
                if device_key not in device_subscriptions:
                    device_subscriptions[device_key] = set()
                device_subscriptions[device_key].add(websocket)

                print(f"客户端订阅设备: {device_key}")

        elif message_type == "info" and message_data.get("info") == "alive":
            # 处理心跳消息
            print(f"收到客户端心跳: {websocket.remote_address}")

    except Exception as e:
        print(f"处理客户端消息失败: {e}")


async def handle_websocket(websocket, path):
    """处理WebSocket连接"""
    client_address = websocket.remote_address

    # 检查WebSocket路径是否匹配
    if path != WEBSOCKET_PATH:
        print(f"无效的WebSocket路径: {path}, 期望: {WEBSOCKET_PATH}")
        await websocket.close(code=1008, reason="Invalid path")
        return

    print(f"新客户端连接: {client_address}")

    # 初始化客户端连接
    connected_clients[websocket] = set()

    try:
        async for message in websocket:
            try:
                message_data = json.loads(message)
                print(f"收到消息: {message_data}")
                await handle_client_message(websocket, message_data)
            except json.JSONDecodeError:
                print(f"无效的JSON消息: {message}")
            except Exception as e:
                print(f"处理消息失败: {e}")

    except websockets.exceptions.ConnectionClosed:
        print(f"客户端断开连接: {client_address}")
    except Exception as e:
        print(f"WebSocket连接错误: {e}")
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
        print(f"已清理客户端连接和订阅")


async def data_push_worker():
    """数据推送工作线程"""
    print("数据推送工作线程已启动")

    while True:
        try:
            if device_subscriptions:
                # 随机选择一个有订阅的设备推送数据
                device_keys = list(device_subscriptions.keys())
                device_key = random.choice(device_keys)

                # 解析设备信息
                # device_key格式: ".L3F13_xxx" 或 ".L3FCC2_xxx"
                # 从 tag 中提取 plc 信息（如 L3F13 或 L3FCC2）
                tag = device_key
                if tag.startswith("."):
                    # 提取 PLC 名称（格式如 .L3F13_xxx 中的 L3F13）
                    parts = tag[1:].split("_")  # 去掉开头的 "." 后按 "_" 分割
                    plc = parts[0] if parts else "Unknown"

                    # 创建数据消息
                    data_message = create_data_message(plc, tag)
                    message_json = json.dumps(data_message)

                    # 推送给所有订阅此设备的客户端
                    clients_to_remove = []
                    for client in device_subscriptions[device_key].copy():
                        try:
                            await client.send(message_json)
                            print(f"推送数据到客户端: {device_key} -> {data_message['value']}")
                        except websockets.exceptions.ConnectionClosed:
                            clients_to_remove.append(client)
                        except Exception as e:
                            print(f"推送数据失败: {e}")
                            clients_to_remove.append(client)

                    # 清理断开的连接
                    for client in clients_to_remove:
                        cleanup_client_connection(client)

            # 随机等待间隔
            await asyncio.sleep(random.uniform(DATA_PUSH_MIN_INTERVAL, DATA_PUSH_MAX_INTERVAL))

        except Exception as e:
            print(f"数据推送工作线程错误: {e}")
            await asyncio.sleep(1)


async def main():
    """主函数"""
    print(f"WebSocket服务器V2启动中...")
    print(f"监听地址: {SERVER_HOST}:{SERVER_PORT}")
    print(f"WebSocket路径: {WEBSOCKET_PATH}")
    print(f"数据推送间隔: {DATA_PUSH_MIN_INTERVAL}-{DATA_PUSH_MAX_INTERVAL}秒")
    print(f"数据格式: 30字符固定格式")
    print("=" * 50)

    # 启动数据推送工作线程
    asyncio.create_task(data_push_worker())

    # 启动WebSocket服务器
    async with websockets.serve(
        handle_websocket,
        SERVER_HOST,
        SERVER_PORT
    ):
        print(f"WebSocket服务器已启动!")
        print(f"客户端连接地址: ws://{SERVER_HOST}:{SERVER_PORT}{WEBSOCKET_PATH}")
        print("按 Ctrl+C 停止服务器")
        print("=" * 50)

        # 保持服务器运行
        await asyncio.Future()  # 永远运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
