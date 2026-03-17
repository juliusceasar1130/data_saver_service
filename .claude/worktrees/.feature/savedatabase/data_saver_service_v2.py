#!/usr/bin/env python3
"""
修改时间：2026年1月21日
修改内容：创建 V2 版本 WebSocket 客户端服务，使用 PostgreSQL 数据库

数据保存服务 V2 - WebSocket客户端 (PostgreSQL 版本)
- 连接到 WebSocket 服务器
- 订阅所有设备数据
- 接收数据并更新到 PostgreSQL rb_position_data 表
- 采用位置状态更新模式（UPDATE 而非 INSERT）
- 支持自动重连和心跳保活
"""

import asyncio
import websockets
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict
import os
import sys

# 导入 PostgreSQL 数据库操作类
from rb_position_manager_postgresql import RBPositionDataManager, VehicleDataParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data_saver_service_v2.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# WebSocket服务器配置
WS_SERVER_HOST = "172.21.12.73"
WS_SERVER_PORT = 8088
WS_SERVER_PATH = "/ws/emosweb"
# WS_URL = f"ws://{WS_SERVER_HOST}:{WS_SERVER_PORT}{WS_SERVER_PATH}"
WS_URL = f"ws://{WS_SERVER_HOST}{WS_SERVER_PATH}"

# PostgreSQL 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "root",
    "password": "root",
    "database": "rollerbed_tracking_db",
}

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 2

# 重连配置
RECONNECT_DELAY = 5  # 重连延迟（秒）
MAX_RECONNECT_ATTEMPTS = 10  # 最大重连次数

# 全局数据库管理器
db_manager: Optional[RBPositionDataManager] = None


def load_device_config() -> List[Dict]:
    """
    加载设备配置
    从本地 deviceConfig.json 读取设备列表
    """
    try:
        # 获取配置文件路径（相对于当前文件）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "deviceConfig.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        devices = []
        if "config" in config:
            for plc, device_list in config["config"].items():
                for device in device_list:
                    devices.append(
                        {
                            "plc": device.get("plc", plc),
                            "tag": device.get("tag", ""),
                            "type": device.get("type", "advise"),
                            "id": device.get("id", ""),
                            "RBindex": device.get("RBindex", ""),
                            "remark": device.get("remark", ""),
                        }
                    )

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


def init_db_manager() -> bool:
    """
    初始化数据库管理器

    Returns:
        bool: 是否初始化成功
    """
    global db_manager
    try:
        db_manager = RBPositionDataManager(DB_CONFIG)
        db_manager.connect()
        logger.info("✅ PostgreSQL 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        logger.error(traceback.format_exc())
        return False


def close_db_manager():
    """关闭数据库连接"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None
        logger.info("✅ 数据库连接已关闭")


def normalize_tag(server_tag: str) -> str:
    """
    将服务器返回的tag格式转换为数据库中存储的格式

    服务器返回格式: L3F13.L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID
    数据库存储格式: .L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID

    转换规则:
    1. 如果tag以点开头，直接返回（已经是正确格式）
    2. 如果tag包含两个部分（PLC名称.完整路径），提取完整路径部分
    3. 在完整路径前加上点号

    Args:
        server_tag: 服务器返回的tag字符串

    Returns:
        str: 转换后的tag字符串（数据库格式）
    """
    # 如果已经是正确格式（以点开头），直接返回
    if server_tag.startswith("."):
        return server_tag

    # 检查是否包含点号
    if "." not in server_tag:
        # 没有点号，直接在开头加点返回
        return f".{server_tag}"

    # 分割tag: "L3F13.L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID"
    parts = server_tag.split(".", 1)  # 只分割第一个点

    if len(parts) >= 2:
        # parts[0] = "L3F13" (PLC名称)
        # parts[1] = "L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID"
        # 返回 ".L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID"
        return f".{parts[1]}"
    else:
        # 只有一个部分，在开头加点
        return f".{server_tag}"


def save_vehicle_data(tag: str, value: str, ts: str) -> bool:
    """
    保存车辆数据到数据库（位置状态更新模式）

    Args:
        tag: 标签字符串
        value: 30字符车身数据
        ts: 时间戳字符串

    Returns:
        bool: 是否保存成功
    """
    global db_manager

    if not db_manager:
        logger.error("❌ 数据库管理器未初始化")
        return False

    try:
        # 转换tag格式: 从服务器格式转换为数据库格式
        # 服务器: L3F13.L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID
        # 数据库: .L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID
        normalized_tag = normalize_tag(tag)
        logger.debug(f"🔄 Tag格式转换: {tag} -> {normalized_tag}")

        # 检查数据长度
        if not value or len(value) != 30:
            logger.warning(
                f"⚠️ 数据长度不符合要求: 期望30字符, 实际{len(value) if value else 0}字符, tag={tag}"
            )
            return False

        # 使用转换后的tag更新车辆数据
        success = db_manager.update_vehicle_by_tag(normalized_tag, value)

        if success:
            logger.info(
                f"💾 数据更新成功 - Tag: {normalized_tag}, VehicleID: {value[:14]}"
            )
        else:
            logger.warning(f"⚠️ 数据更新失败或未找到对应位置 - Tag: {normalized_tag}")

        return success

    except Exception as e:
        logger.error(f"❌ 保存数据时发生错误: {e}")
        logger.error(f"   数据: tag={tag}, value={value}, ts={ts}")
        logger.error(traceback.format_exc())
        return False


async def subscribe_devices(websocket, devices: List[Dict]):
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
                "id": device.get("id", ""),
                "type": device.get("type", "advise"),
                "plc": device["plc"],
                "tag": device["tag"],
            }

            # 发送订阅请求
            await websocket.send(json.dumps(subscribe_message))
            logger.debug(f"📤 订阅设备 {i+1}/{len(devices)}: {device['tag']}")

            # 避免一次性发送太多请求，稍微延迟
            if (i + 1) % 10 == 0:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"❌ 订阅设备失败: {device}, 错误: {e}")

    logger.info(f"✅ 设备订阅完成")


async def send_heartbeat(websocket):
    """发送心跳消息"""
    try:
        heartbeat_message = {"type": "info", "info": "alive"}
        await websocket.send(json.dumps(heartbeat_message))
        logger.debug("💓 发送心跳")
    except Exception as e:
        logger.error(f"❌ 发送心跳失败: {e}")
        raise


async def handle_message(message: str, devices: List[Dict]):
    """
    处理接收到的消息

    Args:
        message: WebSocket消息
        devices: 设备列表（用于验证）
    """
    try:
        data = json.loads(message)
        message_type = data.get("type", "")

        if message_type == "dataChange":
            # 数据变更消息，更新到数据库
            tag = data.get("tag", "")
            value = data.get("value", "")
            ts = data.get("ts", "")

            if tag and value:
                # 保存数据（同步操作，失败不影响接收）
                try:
                    save_vehicle_data(tag, value, ts)
                except Exception as e:
                    # 数据库保存失败不影响消息接收
                    logger.error(f"❌ 数据库保存失败（不影响接收）: {e}")
            else:
                logger.warning(f"⚠️ 收到无效数据消息: tag={tag}, value={value}")

        elif message_type == "info":
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


async def websocket_client(devices: List[Dict]):
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
            logger.info(
                f"🔄 {RECONNECT_DELAY}秒后尝试重连 ({reconnect_count}/{MAX_RECONNECT_ATTEMPTS})..."
            )
            await asyncio.sleep(RECONNECT_DELAY)
        else:
            logger.error(f"❌ 达到最大重连次数，停止服务")
            break


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🌟 数据保存服务 V2 (PostgreSQL) 启动中...")
    logger.info("=" * 60)

    # 加载设备配置
    devices = load_device_config()

    if not devices:
        logger.error("❌ 未加载到设备配置，服务无法启动")
        return

    logger.info(f"📋 已加载 {len(devices)} 个设备")
    logger.info(f"🔗 WebSocket服务器: {WS_URL}")
    logger.info(
        f"💾 数据库: PostgreSQL {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    logger.info("=" * 60)

    # 初始化数据库连接
    if not init_db_manager():
        logger.error("❌ 数据库初始化失败，服务无法启动")
        return

    # 启动WebSocket客户端
    try:
        await websocket_client(devices)
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止（用户中断）")
    except Exception as e:
        logger.error(f"❌ 服务运行错误: {e}")
        logger.error(traceback.format_exc())
    finally:
        # 关闭数据库连接
        close_db_manager()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止")
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)
