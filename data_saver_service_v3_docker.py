#!/usr/bin/env python3
"""
修改时间：2026年3月20日
修改内容：创建 Docker 版本 WebSocket 客户端服务，支持环境变量配置。新增 carrier_id 订阅及保存逻辑。
版本：V3_Docker

数据保存服务 V3 - WebSocket客户端 (Docker 版)
- 连接到 WebSocket 服务器
- 订阅设备的 BodyID 和 CarrierID 数据
- 接收数据并更新到 PostgreSQL rb_position_data 表
- 支持自动重连和心跳保活
- 支持通过环境变量配置数据库连接和WebSocket地址
- 支持挂载 deviceConfig.json 配置文件
"""

import asyncio
import websockets
import json
import logging
import socket
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Set
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入 PostgreSQL 数据库操作类
try:
    from rb_position_manager_postgresql import RBPositionDataManager, VehicleDataParser
except ImportError:
    print("错误: 找不到 rb_position_manager_postgresql.py 模块。")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("DataSaverService_V3_Docker")

# WebSocket服务器配置
WS_SERVER_HOST = os.getenv("WS_SERVER_HOST", "172.21.12.73")
WS_SERVER_PORT = int(os.getenv("WS_SERVER_PORT", "8088"))
WS_SERVER_PATH = os.getenv("WS_SERVER_PATH", "/ws/emosweb")
WS_USE_PORT_IN_URL = os.getenv("WS_USE_PORT_IN_URL", "false").lower() == "true"
if WS_USE_PORT_IN_URL:
     WS_URL = f"ws://{WS_SERVER_HOST}:{WS_SERVER_PORT}{WS_SERVER_PATH}"
else:
     WS_URL = f"ws://{WS_SERVER_HOST}{WS_SERVER_PATH}"

logger.info(f"配置 WebSocket URL: {WS_URL}")


# PostgreSQL 数据库配置
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
RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))
MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "10"))

# 配置文件路径
CONFIG_FILE_PATH = os.getenv("DEVICE_CONFIG_PATH", "deviceConfig.json")

# 全局数据库管理器
db_manager: Optional[RBPositionDataManager] = None


def get_effective_ws_port() -> int:
    """获取当前实际使用的 WebSocket 目标端口。"""
    return WS_SERVER_PORT if WS_USE_PORT_IN_URL else 80


def probe_tcp_connectivity(host: str, port: int, timeout: float = 3.0) -> bool:
    """启动前做一次轻量 TCP 探测，帮助判断容器网络是否可达。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            logger.info(f"✅ TCP 探测成功: {host}:{port} (timeout={timeout}s)")
            return True
    except Exception as e:
        logger.warning(f"⚠️ TCP 探测失败: {host}:{port} (timeout={timeout}s), error={e}")
        return False


def normalize_tag(server_tag: str) -> str:
    """
    将服务器返回的tag格式转换为数据库中存储的格式

    服务器返回格式: L3F13.L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID
    数据库存储格式: .L3F13_1A_1A015LT_1A015RB.IL.SD.M1003_BodyID
    """
    if server_tag.startswith("."):
        return server_tag

    if "." not in server_tag:
        return f".{server_tag}"

    parts = server_tag.split(".", 1)

    if len(parts) >= 2:
        return f".{parts[1]}"
    else:
        return f".{server_tag}"


def load_device_config() -> Tuple[List[Dict], List[Dict], Dict[str, str]]:
    """
    加载设备配置
    从 deviceConfig.json 读取设备列表
    
    返回:
        (body_devices, carrier_devices, carrier_tag_to_body_tag)
    """
    try:
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

        body_devices = []
        carrier_devices = []
        carrier_tag_to_body_tag = {}

        if "config" in config:
            for plc, device_list in config["config"].items():
                for device in device_list:
                    body_tag = device.get("tag", "")
                    
                    # 1. 组装 BodyID 订阅设备
                    body_devices.append(
                        {
                            "plc": device.get("plc", plc),
                            "tag": body_tag,
                            "type": device.get("type", "advise"),
                            "id": device.get("id", ""),
                            "RBindex": device.get("RBindex", ""),
                            "remark": device.get("remark", ""),
                        }
                    )
                    
                    # 2. 组装 CarrierID 订阅设备并构建映射关系
                    carrier_tag = device.get("tag_carrier_id", "")
                    if carrier_tag:
                        carrier_devices.append(
                            {
                                "plc": device.get("plc", plc),
                                "tag": carrier_tag,
                                "type": device.get("type", "advise"),
                                "id": device.get("id", ""),
                            }
                        )
                        # 映射关系: normalized(carrier_tag) -> normalized(body_tag)
                        normalized_carrier = normalize_tag(carrier_tag)
                        normalized_body = normalize_tag(body_tag)
                        carrier_tag_to_body_tag[normalized_carrier] = normalized_body

        logger.info(f"✅ 已加载 {len(body_devices)} 个 BodyID 订阅 + {len(carrier_devices)} 个 CarrierID 订阅")
        return body_devices, carrier_devices, carrier_tag_to_body_tag

    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return [], [], {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ 配置文件JSON解析失败: {e}")
        return [], [], {}
    except Exception as e:
        logger.error(f"❌ 加载设备配置失败: {e}")
        logger.error(traceback.format_exc())
        return [], [], {}


def init_db_manager() -> bool:
    """初始化数据库管理器"""
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


def save_vehicle_data(tag: str, value: str, ts: str) -> bool:
    """保存车辆数据到数据库（BodyID - 30字符）"""
    global db_manager

    if not db_manager:
        logger.error("❌ 数据库管理器未初始化")
        return False

    try:
        normalized_tag = normalize_tag(tag)
        
        # 检查数据长度
        if not value or len(value) != 30:
            logger.warning(
                f"⚠️ BodyID 数据长度不符合要求: 期望30字符, 实际{len(value) if value else 0}字符, tag={tag}"
            )
            return False

        success = db_manager.update_vehicle_by_tag(normalized_tag, value)

        if success:
            logger.info(f"💾 车身数据更新成功 - Tag: {normalized_tag}, VehicleID: {value[:14]}")
        else:
            logger.warning(f"⚠️ 车身数据更新失败或未找到对应位置 - Tag: {normalized_tag}")

        return success

    except Exception as e:
        logger.error(f"❌ 保存车身数据时发生错误: {e}")
        logger.error(f"   数据: tag={tag}, value={value}, ts={ts}")
        return False


def save_carrier_id_data(carrier_tag: str, value: str, ts: str, carrier_tag_to_body_tag: Dict[str, str]) -> bool:
    """保存载体数据到数据库 (CarrierID)"""
    global db_manager

    if not db_manager:
        logger.error("❌ 数据库管理器未初始化")
        return False

    try:
        normalized_carrier_tag = normalize_tag(carrier_tag)
        body_tag = carrier_tag_to_body_tag.get(normalized_carrier_tag)
        
        if not body_tag:
            logger.warning(f"⚠️ 找不到 carrier_tag 对应的 body_tag: {normalized_carrier_tag}")
            return False

        # 不做 30 字符校验，直接保存 carrier_id
        if not value:
            # 如果推送了空值，可以选择跳过或清除载体ID，这里暂时跳过空值更新
            logger.debug(f"ℹ️ CarrierID 收到空值，跳过更新: tag={carrier_tag}")
            return True

        success = db_manager.update_carrier_id_by_tag(body_tag, value, ts)

        if success:
            logger.info(f"🔧 载体数据更新成功 - BodyTag: {body_tag}, CarrierID: {value}")
        else:
            logger.warning(f"⚠️ 载体数据更新失败或未找到对应位置 - BodyTag: {body_tag}")

        return success

    except Exception as e:
        logger.error(f"❌ 保存载体数据时发生错误: {e}")
        logger.error(f"   数据: tag={carrier_tag}, value={value}, ts={ts}")
        return False


async def subscribe_devices(websocket, body_devices: List[Dict], carrier_devices: List[Dict]):
    """订阅所有设备"""
    total_devices = len(body_devices) + len(carrier_devices)
    logger.info(f"📡 开始订阅 {total_devices} 个设备 (BodyID: {len(body_devices)}, CarrierID: {len(carrier_devices)})...")

    # 合并列表订阅
    all_devices = body_devices + carrier_devices
    
    for i, device in enumerate(all_devices):
        try:
            subscribe_message = {
                "id": device.get("id", ""),
                "type": device.get("type", "advise"),
                "plc": device["plc"],
                "tag": device["tag"],
            }
            await websocket.send(json.dumps(subscribe_message))
            
            if (i + 1) % 20 == 0:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"❌ 订阅设备失败: {device}, 错误: {e}")

    logger.info(f"✅ 设备订阅完成（BodyID: {len(body_devices)}个, CarrierID: {len(carrier_devices)}个）")


async def send_heartbeat(websocket):
    """发送心跳消息"""
    try:
        heartbeat_message = {"type": "info", "info": "alive"}
        await websocket.send(json.dumps(heartbeat_message))
        logger.debug("💓 发送心跳")
    except Exception as e:
        logger.error(f"❌ 发送心跳失败: {e}")
        raise


async def handle_message(message: str, carrier_tag_set: Set[str], carrier_tag_to_body_tag: Dict[str, str]):
    """处理接收到的消息"""
    try:
        data = json.loads(message)
        message_type = data.get("type", "")

        if message_type == "dataChange":
            tag = data.get("tag", "")
            value = data.get("value", "")
            ts = data.get("ts", "")

            if tag:
                normalized_received_tag = normalize_tag(tag)
                
                try:
                    if normalized_received_tag in carrier_tag_set:
                        # 是载体消息
                        save_carrier_id_data(tag, value, ts, carrier_tag_to_body_tag)
                    else:
                        # 默认作为车身消息处理
                        save_vehicle_data(tag, value, ts)
                except Exception as e:
                    logger.error(f"❌ 数据库保存失败（不影响接收）: {e}")
            else:
                logger.warning(f"⚠️ 收到缺失 tag 的数据消息: {data}")

        elif message_type == "info":
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


async def websocket_client(body_devices: List[Dict], carrier_devices: List[Dict], carrier_tag_to_body_tag: Dict[str, str]):
    """WebSocket客户端主函数"""
    reconnect_count = 0
    # 建立用于快速查找的 carrier tags 集合
    carrier_tag_set = set(carrier_tag_to_body_tag.keys())

    while True: 
        try:
            logger.info(f"🔗 正在连接WebSocket服务器: {WS_URL}")

            async with websockets.connect(WS_URL) as websocket:
                logger.info("✅ WebSocket连接成功")
                reconnect_count = 0 

                await subscribe_devices(websocket, body_devices, carrier_devices)

                heartbeat_task = asyncio.create_task(heartbeat_worker(websocket))

                try:
                    async for message in websocket:
                        await handle_message(message, carrier_tag_set, carrier_tag_to_body_tag)

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("🔌 WebSocket连接已关闭")
                    heartbeat_task.cancel()
                except Exception as e:
                    logger.error(f"❌ 接收消息错误: {e}")
                    heartbeat_task.cancel()
                    raise

        except websockets.exceptions.InvalidURI:
            logger.error(f"❌ 无效的WebSocket URI: {WS_URL}, 请检查配置")
            await asyncio.sleep(30)
        except ConnectionRefusedError:
            logger.error(f"❌ 无法连接到WebSocket服务器: {WS_URL}")
            logger.info(f"   请确保WebSocket服务器正在运行")
        except Exception as e:
            logger.error(f"❌ WebSocket连接错误: {e}")
            logger.error(traceback.format_exc())

        reconnect_count += 1
        delay = min(RECONNECT_DELAY * (1.5 ** (reconnect_count -1)), 60)
        
        logger.info(f"🔄 {int(delay)}秒后尝试第 {reconnect_count} 次重连...")
        await asyncio.sleep(delay)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🌟 数据保存服务 V3 (Docker版) - 支持CarrierID 启动中...")
    logger.info("=" * 60)

    logger.info(f"配置信息:")
    logger.info(f"  - WebSocket: {WS_URL}")
    logger.info(f"  - WebSocket目标主机: {WS_SERVER_HOST}")
    logger.info(f"  - WebSocket目标端口: {get_effective_ws_port()}")
    logger.info(f"  - 数据库主机: {DB_CONFIG['host']}")
    logger.info(f"  - 数据库名: {DB_CONFIG['database']}")
    logger.info(f"  - 配置文件: {CONFIG_FILE_PATH}")
    
    if os.path.isabs(CONFIG_FILE_PATH):
        check_path = CONFIG_FILE_PATH
    else:
        check_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_PATH)
        
    if not os.path.exists(check_path):
         logger.warning(f"⚠️ 警告: 配置文件 {check_path} 未找到。请确保 Docker 挂载正确。")

    # 先确认容器当前对目标主机端口的 TCP 可达性
    probe_tcp_connectivity(WS_SERVER_HOST, get_effective_ws_port())

    # 加载设备配置
    body_devices, carrier_devices, carrier_tag_to_body_tag = load_device_config()

    if not body_devices:
        logger.error("❌ 未加载到Body设备配置，服务即将退出")
        sys.exit(1)

    logger.info("=" * 60)

    # 初始化数据库连接
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
        await websocket_client(body_devices, carrier_devices, carrier_tag_to_body_tag)
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止（用户中断）")
    except Exception as e:
        logger.error(f"❌ 服务运行严重错误: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        close_db_manager()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止")
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)
