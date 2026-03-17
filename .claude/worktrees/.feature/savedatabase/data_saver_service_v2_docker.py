#!/usr/bin/env python3
"""
修改时间：2026年1月24日
修改内容：创建 Docker 版本 WebSocket 客户端服务，支持环境变量配置
版本：V2_Docker

数据保存服务 V2 - WebSocket客户端 (Docker 版)
- 连接到 WebSocket 服务器
- 订阅所有设备数据
- 接收数据并更新到 PostgreSQL rb_position_data 表
- 采用位置状态更新模式（UPDATE 而非 INSERT）
- 支持自动重连和心跳保活
- 支持通过环境变量配置数据库连接和WebSocket地址
- 支持挂载 deviceConfig.json 配置文件
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
from dotenv import load_dotenv

# 加载环境变量
# 如果当前目录下有 .env 文件，它会覆盖系统环境变量
load_dotenv()

# 导入 PostgreSQL 数据库操作类
# 确保 rb_position_manager_postgresql.py 与本脚本在同一目录下
try:
    from rb_position_manager_postgresql import RBPositionDataManager, VehicleDataParser
except ImportError:
    print("错误: 找不到 rb_position_manager_postgresql.py 模块。")
    sys.exit(1)

# 配置日志
# Docker 环境下通常打印到标准输出，由 Docker 收集日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # 输出到 stdout 方便 Docker logs 查看
    ],
)
logger = logging.getLogger("DataSaverService_Docker")

# WebSocket服务器配置 - 从环境变量读取，提供默认值
WS_SERVER_HOST = os.getenv("WS_SERVER_HOST", "172.21.12.73")
WS_SERVER_PORT = int(os.getenv("WS_SERVER_PORT", "8088"))
WS_SERVER_PATH = os.getenv("WS_SERVER_PATH", "/ws/emosweb")
# 兼容两种格式构建 URL
if os.getenv("WS_USE_PORT_IN_URL", "false").lower() == "true":
     WS_URL = f"ws://{WS_SERVER_HOST}:{WS_SERVER_PORT}{WS_SERVER_PATH}"
else:
     WS_URL = f"ws://{WS_SERVER_HOST}{WS_SERVER_PATH}"

logger.info(f"配置 WebSocket URL: {WS_URL}")


# PostgreSQL 数据库配置 - 从环境变量读取
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "172.22.44.99"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "rollerbed_tracking_db"),
}

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "2"))

# 重连配置
RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))  # 重连延迟（秒）
MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "10"))  # 最大重连次数

# 配置文件路径
CONFIG_FILE_PATH = os.getenv("DEVICE_CONFIG_PATH", "deviceConfig.json")

# 全局数据库管理器
db_manager: Optional[RBPositionDataManager] = None


def load_device_config() -> List[Dict]:
    """
    加载设备配置
    从 deviceConfig.json 读取设备列表
    """
    try:
        # 获取配置文件绝对路径
        if os.path.isabs(CONFIG_FILE_PATH):
            config_path = CONFIG_FILE_PATH
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, CONFIG_FILE_PATH)

        logger.info(f"正在加载配置文件: {config_path}")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

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

    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
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
        logger.info(f"正在连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']} ({DB_CONFIG['database']})")
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
        try:
            db_manager.close()
            db_manager = None
            logger.info("✅ 数据库连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭数据库连接出错: {e}")


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

    while True: # Docker 模式下，我们希望永久重试，除非人为停止
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
                    # 退出内部 try，进入外层 while 进行重连
                except Exception as e:
                    logger.error(f"❌ 接收消息错误: {e}")
                    heartbeat_task.cancel()
                    raise

        except websockets.exceptions.InvalidURI:
            logger.error(f"❌ 无效的WebSocket URI: {WS_URL}, 请检查配置")
            # 配置错误，重试无意义，等待时间长一些或者退出
            await asyncio.sleep(30)
        except ConnectionRefusedError:
            logger.error(f"❌ 无法连接到WebSocket服务器: {WS_URL}")
            logger.info(f"   请确保WebSocket服务器正在运行")
        except Exception as e:
            logger.error(f"❌ WebSocket连接错误: {e}")
            logger.error(traceback.format_exc())

        # 重连逻辑
        reconnect_count += 1
        
        # 指数退避策略，但不超过 60 秒
        delay = min(RECONNECT_DELAY * (1.5 ** (reconnect_count -1)), 60)
        
        logger.info(
            f"🔄 {int(delay)}秒后尝试第 {reconnect_count} 次重连..."
        )
        await asyncio.sleep(delay)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🌟 数据保存服务 V2 (Docker版) 启动中...")
    logger.info("=" * 60)

    # 打印关键配置
    logger.info(f"配置信息:")
    logger.info(f"  - WebSocket: {WS_URL}")
    logger.info(f"  - 数据库主机: {DB_CONFIG['host']}")
    logger.info(f"  - 数据库名: {DB_CONFIG['database']}")
    logger.info(f"  - 配置文件: {CONFIG_FILE_PATH}")
    
    # 检查配置文件是否存在
    if os.path.isabs(CONFIG_FILE_PATH):
        check_path = CONFIG_FILE_PATH
    else:
        check_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_PATH)
        
    if not os.path.exists(check_path):
         logger.warning(f"⚠️ 警告: 配置文件 {check_path} 未找到。请确保 Docker 挂载正确。")

    # 加载设备配置
    devices = load_device_config()

    if not devices:
        logger.error("❌ 未加载到设备配置，服务无法正常工作 (但将继续尝试，等待文件被挂载或修复)")
        # 即使没有设备，程序也不退出，而是每隔一段时间重试加载，适合容器环境
        # 但这里为了简单，我们还是在 main 中加载一次。
        # 如果需要动态热加载配置文件，需要改写逻辑。
        # 这里先保持原逻辑: 失败则退出容器，由 Docker 重启策略处理
        logger.error("❌ 服务即将退出，等待 Docker 重启")
        sys.exit(1)

    logger.info(f"📋 已加载 {len(devices)} 个设备")
    logger.info("=" * 60)

    # 初始化数据库连接
    # 在 Docker 环境中，数据库可能启动较慢，增加重试机制
    db_retries = 0
    max_db_retries = 5
    while not init_db_manager():
        db_retries += 1
        if db_retries >= max_db_retries:
             logger.error("❌ 数据库连接多次失败，退出服务")
             sys.exit(1)
        logger.info(f"🔄 等待 5 秒后重试数据库连接 ({db_retries}/{max_db_retries})...")
        await asyncio.sleep(5)

    # 启动WebSocket客户端
    try:
        await websocket_client(devices)
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止（用户中断）")
    except Exception as e:
        logger.error(f"❌ 服务运行严重错误: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
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
