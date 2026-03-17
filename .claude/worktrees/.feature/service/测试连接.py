#!/usr/bin/env python3
"""
修改时间：2025年9月1日14点05分
修改内容：WebSocket连接测试脚本

简单的WebSocket客户端测试脚本，用于验证服务器是否正常工作
"""

import asyncio
import websockets
import json

async def test_websocket():
    """测试WebSocket连接"""
    uri = "ws://localhost:8088/ws/emosweb"
    
    try:
        print(f"🔗 正在连接到: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功!")
            
            # 发送测试订阅消息
            test_message = {
                "id": "",
                "type": "advise",
                "plc": "L3FUB2",
                "tag": ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 发送测试消息: {test_message}")
            
            # 等待接收消息
            print("⏳ 等待服务器响应...")
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                print(f"📨 收到响应: {data}")
                print("✅ 测试成功! 服务器工作正常")
            except asyncio.TimeoutError:
                print("⏰ 等待超时，但连接成功表明服务器正在运行")
                
    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 请确保WebSocket服务器正在运行")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    print("🧪 WebSocket连接测试")
    print("=" * 30)
    asyncio.run(test_websocket())
