"""
数据库初始化脚本 - 字典表预填充 (PostgreSQL 版本)
说明: 读取 seed_data.json，预填充 process_areas 和 carrier_types 两张字典表
      冲突策略: ON CONFLICT DO UPDATE (已存在则覆盖更新 description、sort_order 等字段)
创建日期: 2026-03-30
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import os
from dotenv import load_dotenv


class SeedDataInitializer:
    """字典表预填充初始化器 (PostgreSQL)"""

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

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def load_seed_data(self, seed_path="seed_data.json"):
        """
        加载 seed_data.json 预填充数据文件

        Args:
            seed_path (str): JSON 文件路径（相对于脚本目录）

        Returns:
            dict: JSON 数据
        """
        seed_file = Path(__file__).parent / seed_path

        if not seed_file.exists():
            raise FileNotFoundError(f"数据源文件不存在: {seed_file}")

        with open(seed_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"✓ 成功加载数据源文件: {seed_file}")
        meta = data.get("metadata", {})
        print(f"  版本: {meta.get('version', 'N/A')}  说明: {meta.get('description', '')}")
        return data

    # ------------------------------------------------------------------
    # process_areas 填充
    # ------------------------------------------------------------------

    def init_process_areas(self, seed_data):
        """
        填充 process_areas 字典表

        冲突策略: ON CONFLICT (area_name) DO UPDATE
          - 更新 description、sort_order、updated_at

        Args:
            seed_data (dict): load_seed_data() 返回的完整 JSON 数据

        Returns:
            tuple: (upsert_count, error_count)
        """
        records = seed_data.get("process_areas", [])
        if not records:
            print("\n⚠ process_areas 数据源为空，跳过填充")
            return 0, 0

        print(f"\n{'='*50}")
        print(f"开始填充 process_areas 表 (共 {len(records)} 条)")

        # ON CONFLICT DO UPDATE: 按 area_name 唯一键冲突时覆盖更新
        upsert_sql = """
        INSERT INTO process_areas (area_name, description, sort_order)
        VALUES (%s, %s, %s)
        ON CONFLICT (area_name) DO UPDATE SET
            description = EXCLUDED.description,
            sort_order  = EXCLUDED.sort_order,
            updated_at  = CURRENT_TIMESTAMP
        """

        upsert_count = 0
        error_count = 0

        for record in records:
            try:
                self.cursor.execute(
                    upsert_sql,
                    (
                        record["area_name"],
                        record.get("description", ""),
                        record.get("sort_order", 0),
                    ),
                )
                upsert_count += 1
                print(f"  ✓ [{record['area_name']}]  sort_order={record.get('sort_order', 0)}")
            except psycopg2.Error as err:
                error_count += 1
                print(f"  ✗ 写入失败 [{record.get('area_name', '?')}]: {err}")

        self.connection.commit()
        print(f"\n  填充完成: 成功 {upsert_count} 条 / 失败 {error_count} 条")
        return upsert_count, error_count

    # ------------------------------------------------------------------
    # carrier_types 填充
    # ------------------------------------------------------------------

    def init_carrier_types(self, seed_data):
        """
        填充 carrier_types 字典表

        冲突策略: ON CONFLICT (type_code) DO UPDATE
          - 更新 type_name_cn、description、sort_order、updated_at

        Args:
            seed_data (dict): load_seed_data() 返回的完整 JSON 数据

        Returns:
            tuple: (upsert_count, error_count)
        """
        records = seed_data.get("carrier_types", [])
        if not records:
            print("\n⚠ carrier_types 数据源为空，跳过填充")
            return 0, 0

        print(f"\n{'='*50}")
        print(f"开始填充 carrier_types 表 (共 {len(records)} 条)")

        # ON CONFLICT DO UPDATE: 按 type_code 唯一键冲突时覆盖更新
        upsert_sql = """
        INSERT INTO carrier_types (type_code, type_name_cn, description, sort_order)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (type_code) DO UPDATE SET
            type_name_cn = EXCLUDED.type_name_cn,
            description  = EXCLUDED.description,
            sort_order   = EXCLUDED.sort_order,
            updated_at   = CURRENT_TIMESTAMP
        """

        upsert_count = 0
        error_count = 0

        for record in records:
            try:
                self.cursor.execute(
                    upsert_sql,
                    (
                        record["type_code"],
                        record.get("type_name_cn", ""),
                        record.get("description", ""),
                        record.get("sort_order", 0),
                    ),
                )
                upsert_count += 1
                print(f"  ✓ [{record['type_code']}] {record.get('type_name_cn', '')}  sort_order={record.get('sort_order', 0)}")
            except psycopg2.Error as err:
                error_count += 1
                print(f"  ✗ 写入失败 [{record.get('type_code', '?')}]: {err}")

        self.connection.commit()
        print(f"\n  填充完成: 成功 {upsert_count} 条 / 失败 {error_count} 条")
        return upsert_count, error_count

    # ------------------------------------------------------------------
    # 验证
    # ------------------------------------------------------------------

    def verify(self):
        """查询两张表当前记录，打印验证信息"""
        print(f"\n{'='*50}")
        print("验证结果")

        # process_areas
        self.cursor.execute(
            "SELECT id, area_name, sort_order, description FROM process_areas ORDER BY sort_order"
        )
        rows = self.cursor.fetchall()
        print(f"\n  process_areas ({len(rows)} 条):")
        for row in rows:
            print(f"    id={row['id']}  sort={row['sort_order']:>5}  [{row['area_name']}]  {row['description'] or ''}")

        # carrier_types
        self.cursor.execute(
            "SELECT id, type_code, type_name_cn, sort_order, description FROM carrier_types ORDER BY sort_order"
        )
        rows = self.cursor.fetchall()
        print(f"\n  carrier_types ({len(rows)} 条):")
        for row in rows:
            print(f"    id={row['id']}  sort={row['sort_order']:>5}  [{row['type_code']}] {row['type_name_cn'] or ''}  {row['description'] or ''}")

        print(f"{'='*50}")


# ======================================================================
# 主函数
# ======================================================================

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

    seed_path = os.getenv("SEED_DATA_PATH", "seed_data.json")

    print("=" * 50)
    print("字典表预填充脚本 (PostgreSQL)")
    print("  目标表: process_areas / carrier_types")
    print("  冲突策略: ON CONFLICT DO UPDATE (覆盖更新)")
    print("=" * 50)

    initializer = SeedDataInitializer(db_config)

    try:
        # 1. 连接数据库
        initializer.connect()

        # 2. 加载数据源
        seed_data = initializer.load_seed_data(seed_path)

        # 3. 填充 process_areas
        initializer.init_process_areas(seed_data)

        # 4. 填充 carrier_types
        initializer.init_carrier_types(seed_data)

        # 5. 验证结果
        initializer.verify()

        print("\n✓ 字典表预填充完成!")

    except FileNotFoundError as e:
        print(f"\n✗ 数据源文件错误: {e}")
        print("  请确认 seed_data.json 文件存在于脚本同级目录，或通过 SEED_DATA_PATH 环境变量指定路径")

    except Exception as e:
        print(f"\n✗ 初始化过程出错: {e}")
        import traceback
        traceback.print_exc()
        if initializer.connection:
            initializer.connection.rollback()
            print("✓ 事务已回滚")

    finally:
        initializer.close()


if __name__ == "__main__":
    main()
