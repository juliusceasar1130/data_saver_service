#!/usr/bin/env python3
"""
修改时间：2025年9月1日14点05分
修改内容：创建WebSocket客户端服务，订阅数据并保存到数据库

数据保存服务 - WebSocket客户端
- 连接到WebSocket服务器
- 订阅所有设备数据
- 接收数据并保存到production_record.production表
- 支持自动重连和心跳保活
"""

import asyncio
import websockets
import json
import pymysql
import logging
import traceback
from datetime import datetime
from typing import Optional
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_saver_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket服务器配置
WS_SERVER_HOST = "localhost"
WS_SERVER_PORT = 8088
WS_SERVER_PATH = "/ws/emosweb"
WS_URL = f"ws://{WS_SERVER_HOST}:{WS_SERVER_PORT}{WS_SERVER_PATH}"

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'production_record',
    'charset': 'utf8mb4'
}

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 2

# 重连配置
RECONNECT_DELAY = 5  # 重连延迟（秒）
MAX_RECONNECT_ATTEMPTS = 10  # 最大重连次数


def load_device_config():
    """
    加载设备配置
    从deviceConfig.json读取设备列表
    """
    try:
        # 获取配置文件路径（相对于当前文件）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'src', 'config', 'deviceConfig.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        devices = []
        if 'config' in config:
            for plc, device_list in config['config'].items():
                for device in device_list:
                    devices.append({
                        'plc': device.get('plc', plc),
                        'tag': device.get('tag', ''),
                        'type': device.get('type', 'advise'),
                        'id': device.get('id', '')
                    })
        
        logger.info(f"✅ 已加载 {len(devices)} 个设备配置")
        return devices
        
    except FileNotFoundError:
        logger.error(f"❌ 配置文件未找到: {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ 配置文件JSON解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ 加载设备配置失败: {e}")
        logger.error(traceback.format_exc())
        return []


def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        raise


def save_production_data(tag, value, ts):
    """
    保存生产数据到数据库（同步操作）
    
    Args:
        tag: 标签字符串
        value: 数据值字符串
        ts: 时间戳字符串
    
    Returns:
        bool: 是否保存成功
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 插入数据
        sql = """
            INSERT INTO production (tag, value, ts) 
            VALUES (%s, %s, %s)
        """
        
        # 处理时间戳
        if ts:
            try:
                # 解析ISO格式时间戳：2025-09-05T14:27:34.781+08:00
                if 'T' in ts:
                    # 移除时区信息
                    ts_clean = ts.replace('+08:00', '').replace('-08:00', '')
                    # 解析时间戳
                    if '.' in ts_clean:
                        ts_datetime = datetime.strptime(ts_clean, '%Y-%m-%dT%H:%M:%S.%f')
                    else:
                        ts_datetime = datetime.strptime(ts_clean, '%Y-%m-%dT%H:%M:%S')
                else:
                    ts_datetime = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.warning(f"⚠️  时间戳解析失败，使用当前时间: {e}, ts={ts}")
                ts_datetime = datetime.now()
        else:
            ts_datetime = datetime.now()
        
        # 执行插入
        cursor.execute(sql, (tag, str(value), ts_datetime))
        connection.commit()
        
        record_id = cursor.lastrowid
        logger.info(f"💾 数据保存成功 - ID: {record_id}, Tag: {tag}, Value: {value}")
        
        return True
        
    except pymysql.Error as e:
        if connection:
            connection.rollback()
        logger.error(f"❌ 数据库操作失败: {e}")
        logger.error(f"   数据: tag={tag}, value={value}, ts={ts}")
        logger.error(traceback.format_exc())
        return False
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"❌ 保存数据时发生未知错误: {e}")
        logger.error(f"   数据: tag={tag}, value={value}, ts={ts}")
        logger.error(traceback.format_exc())
        return False
        
    finally:
        if connection:
            connection.close()


async def subscribe_devices(websocket, devices):
    """
    订阅所有设备
    
    Args:
        websocket: WebSocket连接
        devices: 设备列表
    """
    logger.info(f"📡 开始订阅 {len(devices)} 个设备...")
    
    for i, device in enumerate(devices):
        try:
            # 构建订阅消息
            subscribe_message = {
                "id": device.get('id', ''),
                "type": device.get('type', 'advise'),
                "plc": device['plc'],
                "tag": device['tag']
            }
            
            # 发送订阅请求
            await websocket.send(json.dumps(subscribe_message))
            logger.debug(f"📤 订阅设备 {i+1}/{len(devices)}: {device['plc']}{device['tag']}")
            
            # 避免一次性发送太多请求，稍微延迟
            if (i + 1) % 10 == 0:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ 订阅设备失败: {device}, 错误: {e}")
    
    logger.info(f"✅ 设备订阅完成")


async def send_heartbeat(websocket):
    """发送心跳消息"""
    try:
        heartbeat_message = {
            "type": "info",
            "info": "alive"
        }
        await websocket.send(json.dumps(heartbeat_message))
        logger.debug("💓 发送心跳")
    except Exception as e:
        logger.error(f"❌ 发送心跳失败: {e}")
        raise


async def handle_message(message, devices):
    """
    处理接收到的消息
    
    Args:
        message: WebSocket消息
        devices: 设备列表（用于验证）
    """
    try:
        data = json.loads(message)
        message_type = data.get('type', '')
        
        if message_type == 'dataChange':
            # 数据变更消息，保存到数据库
            tag = data.get('tag', '')
            value = data.get('value', '')
            ts = data.get('ts', '')
            
            if tag and value is not None:
                # 保存数据（同步操作，失败不影响接收）
                try:
                    save_production_data(tag, value, ts)
                except Exception as e:
                    # 数据库保存失败不影响消息接收
                    logger.error(f"❌ 数据库保存失败（不影响接收）: {e}")
            else:
                logger.warning(f"⚠️  收到无效数据消息: tag={tag}, value={value}")
                
        elif message_type == 'info':
            # 心跳响应或其他信息
            logger.debug(f"📨 收到信息消息: {data}")
        else:
            logger.debug(f"📨 收到未知类型消息: {data}")
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {e}, 消息: {message}")
    except Exception as e:
        logger.error(f"❌ 处理消息失败: {e}")
        logger.error(traceback.format_exc())


async def heartbeat_worker(websocket):
    """心跳工作线程"""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await send_heartbeat(websocket)
    except asyncio.CancelledError:
        logger.info("💓 心跳线程已停止")
    except Exception as e:
        logger.error(f"❌ 心跳线程错误: {e}")


async def websocket_client(devices):
    """
    WebSocket客户端主函数
    
    Args:
        devices: 设备列表
    """
    reconnect_count = 0
    
    while reconnect_count < MAX_RECONNECT_ATTEMPTS:
        try:
            logger.info(f"🔗 正在连接WebSocket服务器: {WS_URL}")
            
            async with websockets.connect(WS_URL) as websocket:
                logger.info("✅ WebSocket连接成功")
                reconnect_count = 0  # 重置重连计数
                
                # 订阅所有设备
                await subscribe_devices(websocket, devices)
                
                # 启动心跳线程
                heartbeat_task = asyncio.create_task(heartbeat_worker(websocket))
                
                try:
                    # 接收消息循环
                    async for message in websocket:
                        await handle_message(message, devices)
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("🔌 WebSocket连接已关闭")
                    heartbeat_task.cancel()
                    break
                except Exception as e:
                    logger.error(f"❌ 接收消息错误: {e}")
                    heartbeat_task.cancel()
                    raise
                    
        except websockets.exceptions.InvalidURI:
            logger.error(f"❌ 无效的WebSocket URI: {WS_URL}")
            break
        except ConnectionRefusedError:
            logger.error(f"❌ 无法连接到WebSocket服务器: {WS_URL}")
            logger.info(f"   请确保WebSocket服务器正在运行")
        except Exception as e:
            logger.error(f"❌ WebSocket连接错误: {e}")
            logger.error(traceback.format_exc())
        
        # 重连逻辑
        reconnect_count += 1
        if reconnect_count < MAX_RECONNECT_ATTEMPTS:
            logger.info(f"🔄 {RECONNECT_DELAY}秒后尝试重连 ({reconnect_count}/{MAX_RECONNECT_ATTEMPTS})...")
            await asyncio.sleep(RECONNECT_DELAY)
        else:
            logger.error(f"❌ 达到最大重连次数，停止服务")
            break


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🌟 数据保存服务启动中...")
    logger.info("=" * 60)
    
    # 加载设备配置
    devices = load_device_config()
    
    if not devices:
        logger.error("❌ 未加载到设备配置，服务无法启动")
        return
    
    logger.info(f"📋 已加载 {len(devices)} 个设备")
    logger.info(f"🔗 WebSocket服务器: {WS_URL}")
    logger.info(f"💾 数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info("=" * 60)
    
    # 测试数据库连接
    try:
        connection = get_db_connection()
        connection.close()
        logger.info("✅ 数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        logger.error("   请检查数据库配置和连接")
        return
    
    # 启动WebSocket客户端
    try:
        await websocket_client(devices)
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止（用户中断）")
    except Exception as e:
        logger.error(f"❌ 服务运行错误: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止")
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)

