"""
数据库初始化脚本 - RB位置数据初始化 (PostgreSQL 版本)
说明: 读取 deviceConfig.json,初始化 rb_position_data 表的98条位置记录
创建日期: 2026-01-20
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv


class RBPositionInitializer:
    """RB位置数据初始化器 (PostgreSQL)"""

    def __init__(self, db_config):
        """
        初始化数据库连接配置

        Args:
            db_config (dict): 数据库连接配置
                {
                    'host': 'localhost',
                    'port': 5432,
                    'user': 'postgres',
                    'password': 'your_password',
                    'database': 'your_database'
                }
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def connect(self):
        """连接到数据库"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config.get("port", 5432),
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"],
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            # 设置会话时区为上海 (UTC+8)
            self.cursor.execute("SET TIME ZONE 'Asia/Shanghai'")
            print(f"✓ 成功连接到 PostgreSQL 数据库: {self.db_config['database']} (时区: Asia/Shanghai)")
        except psycopg2.Error as err:
            print(f"✗ 数据库连接失败: {err}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ 数据库连接已关闭")

    def load_device_config(self, config_path="deviceConfig.json"):
        """
        加载设备配置文件

        Args:
            config_path (str): 配置文件路径

        Returns:
            dict: 配置数据
        """
        config_file = Path(__file__).parent / config_path

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        print(f"✓ 成功加载配置文件: {config_file}")
        return config

    def clear_existing_data(self):
        """清空现有的位置数据(可选操作)"""
        try:
            self.cursor.execute("DELETE FROM rb_position_data")
            self.connection.commit()
            print("✓ 已清空现有位置数据")
        except psycopg2.Error as err:
            print(f"✗ 清空数据失败: {err}")
            raise

    def initialize_positions(self, config_data, clear_first=False):
        """
        初始化位置数据

        Args:
            config_data (dict): deviceConfig.json 的数据
            clear_first (bool): 是否先清空现有数据
        """
        if clear_first:
            self.clear_existing_data()

        # 准备插入 SQL (PostgreSQL 使用 %s 占位符)
        insert_sql = """
        INSERT INTO rb_position_data 
            (plc, tag, rb_index, remark, process_area, carrier_id, carrier_type)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tag) DO NOTHING
        """

        total_count = 0
        success_count = 0
        error_count = 0

        # 遍历所有 PLC 设备配置
        for plc_name, devices in config_data["config"].items():
            print(f"\n处理 PLC: {plc_name} ({len(devices)} 个位置)")

            for device in devices:
                total_count += 1

                try:
                    # 插入数据
                    self.cursor.execute(
                        insert_sql,
                        (
                            device["plc"],
                            device["tag"],
                            device["RBindex"],
                            device["remark"],
                            device.get("process_area", ""),
                            device.get("carrier_id", ""),
                            device.get("carrier_type", ""),
                        ),
                    )
                    success_count += 1

                    if total_count % 10 == 0:
                        print(f"  已处理 {total_count} 条记录...")

                except psycopg2.Error as err:
                    error_count += 1
                    print(f"  ✗ 插入失败 [{device['RBindex']}]: {err}")

        # 提交事务
        self.connection.commit()

        # 打印统计信息
        print("\n" + "=" * 50)
        print("初始化完成统计:")
        print(f"  总记录数: {total_count}")
        print(f"  成功插入: {success_count}")
        print(f"  插入失败: {error_count}")
        print("=" * 50)

        return success_count, error_count

    def verify_initialization(self):
        """验证初始化结果"""
        # 查询总记录数
        self.cursor.execute("SELECT COUNT(*) as count FROM rb_position_data")
        total = self.cursor.fetchone()["count"]

        # 按 PLC 分组统计
        self.cursor.execute(
            """
            SELECT plc, COUNT(*) as count 
            FROM rb_position_data 
            GROUP BY plc
        """
        )
        plc_stats = self.cursor.fetchall()

        print("\n" + "=" * 50)
        print("验证结果:")
        print(f"  总位置记录数: {total}")
        print("\n  按 PLC 分组统计:")
        for stat in plc_stats:
            print(f"    {stat['plc']}: {stat['count']} 个位置")
        print("=" * 50)

        return total


def main():
    """主函数"""
    # ========== 从 .env 读取配置 ==========
    load_dotenv()
    
    db_config = {
        "host": os.getenv("DB_HOST", "172.22.44.99"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "root"),
        "database": os.getenv("DB_NAME", "rollerbed_tracking_db"),
    }

    print("=" * 50)
    print("RB位置数据初始化脚本 (PostgreSQL)")
    print("=" * 50)

    # 创建初始化器
    initializer = RBPositionInitializer(db_config)

    try:
        # 1. 连接数据库
        initializer.connect()

        # 2. 加载配置文件
        config_path = os.getenv("DEVICE_CONFIG_PATH", "deviceConfig.json")
        config = initializer.load_device_config(config_path)

        # 3. 初始化位置数据
        success, error = initializer.initialize_positions(config, clear_first=False)

        # 4. 验证初始化结果
        total = initializer.verify_initialization()

        # 5. 检查是否与配置文件一致
        expected_total = config["metadata"]["totalDevices"]
        if total == expected_total:
            print(f"\n✓ 初始化成功! 位置数量与配置文件一致 ({total})")
        else:
            print(f"\n⚠ 警告: 位置数量不一致!")
            print(f"  配置文件: {expected_total}")
            print(f"  数据库: {total}")

    except Exception as e:
        print(f"\n✗ 初始化过程出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        initializer.close()


if __name__ == "__main__":
    main()
