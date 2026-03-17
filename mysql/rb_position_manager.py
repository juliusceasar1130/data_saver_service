"""
RB位置数据表操作封装类
说明: 提供对 rb_position_data 表的常用操作方法
作者: Database Migration Script
创建日期: 2026-01-20
"""

import mysql.connector
from datetime import datetime
from typing import Optional, Dict, List, Tuple


class VehicleDataParser:
    """车辆数据解析器 - 解析30字符车身数据"""
    
    @staticmethod
    def parse(raw_data: str) -> Dict[str, str]:
        """
        解析30字符车身数据
        
        Args:
            raw_data (str): 30字符原始数据
            
        Returns:
            Dict[str, str]: 解析后的字段字典
        """
        if len(raw_data) != 30:
            raise ValueError(f"数据长度错误: 期望30字符,实际{len(raw_data)}字符")
        
        return {
            'vehicle_id': raw_data[0:14],       # 第0-13位
            'body_type': raw_data[14:19],       # 第14-18位
            'color_code': raw_data[19:23],      # 第19-22位
            'platform_code': raw_data[23:26],   # 第23-25位
            'black_roof_flag': raw_data[26],    # 第26位
            'rework_flag': raw_data[27],        # 第27位
            'reserved_1': raw_data[28],         # 第28位
            'reserved_2': raw_data[29],         # 第29位
            'raw_data': raw_data                # 完整原始数据
        }


class RBPositionDataManager:
    """RB位置数据管理器 - 数据库操作封装"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        初始化数据库连接
        
        Args:
            db_config (dict): 数据库连接配置
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.parser = VehicleDataParser()
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            print(f"✓ 数据库连接成功: {self.db_config['database']}")
        except mysql.connector.Error as err:
            print(f"✗ 数据库连接失败: {err}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ 数据库连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
    
    # ========== 核心更新方法 ==========
    
    def update_vehicle_by_tag(self, tag: str, raw_data_30: str) -> bool:
        """
        根据 tag 更新车辆数据 (核心方法)
        
        Args:
            tag (str): Tag标签
            raw_data_30 (str): 30字符车身数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 解析车辆数据
            vehicle_data = self.parser.parse(raw_data_30)
            
            # 2. 更新数据库
            update_sql = """
            UPDATE rb_position_data
            SET 
                vehicle_id = %s,
                body_type = %s,
                color_code = %s,
                platform_code = %s,
                black_roof_flag = %s,
                rework_flag = %s,
                reserved_1 = %s,
                reserved_2 = %s,
                raw_data = %s,
                vehicle_updated_at = %s
            WHERE tag = %s
            """
            
            self.cursor.execute(update_sql, (
                vehicle_data['vehicle_id'],
                vehicle_data['body_type'],
                vehicle_data['color_code'],
                vehicle_data['platform_code'],
                vehicle_data['black_roof_flag'],
                vehicle_data['rework_flag'],
                vehicle_data['reserved_1'],
                vehicle_data['reserved_2'],
                vehicle_data['raw_data'],
                datetime.now(),
                tag
            ))
            
            self.connection.commit()
            
            # 3. 检查是否更新成功
            if self.cursor.rowcount > 0:
                print(f"✓ 更新成功: tag={tag}, vehicle_id={vehicle_data['vehicle_id']}")
                
                # 4. 自动发现并插入未知的代码
                self._auto_discover_codes(vehicle_data)
                
                return True
            else:
                print(f"⚠ 未找到对应的 tag: {tag}")
                return False
                
        except Exception as e:
            print(f"✗ 更新失败: {e}")
            self.connection.rollback()
            return False
    
    def _auto_discover_codes(self, vehicle_data: Dict[str, str]):
        """
        自动发现并插入未知的车型/颜色/平台代码
        
        Args:
            vehicle_data (dict): 车辆数据字典
        """
        # 检查并插入 body_type
        self._insert_if_not_exists(
            'vehicle_body_types',
            'body_type',
            vehicle_data['body_type'],
            f"未定义车型-{vehicle_data['body_type']}"
        )
        
        # 检查并插入 color_code
        self._insert_if_not_exists(
            'vehicle_color_codes',
            'color_code',
            vehicle_data['color_code'],
            f"未定义颜色-{vehicle_data['color_code']}"
        )
        
        # 检查并插入 platform_code
        self._insert_if_not_exists(
            'vehicle_platforms',
            'platform_code',
            vehicle_data['platform_code'],
            f"未定义平台-{vehicle_data['platform_code']}"
        )
    
    def _insert_if_not_exists(self, table: str, code_field: str, code: str, default_name: str):
        """
        检查代码是否存在,不存在则插入
        
        Args:
            table (str): 表名
            code_field (str): 代码字段名
            code (str): 代码值
            default_name (str): 默认名称
        """
        try:
            # 检查是否存在
            check_sql = f"SELECT COUNT(*) as count FROM {table} WHERE {code_field} = %s"
            self.cursor.execute(check_sql, (code,))
            result = self.cursor.fetchone()
            
            if result['count'] == 0:
                # 不存在,插入新记录
                if table == 'vehicle_body_types':
                    name_field = 'type_name'
                elif table == 'vehicle_color_codes':
                    name_field = 'color_name'
                elif table == 'vehicle_platforms':
                    name_field = 'platform_name'
                else:
                    return
                
                insert_sql = f"""
                INSERT INTO {table} 
                    ({code_field}, {name_field}, is_defined, first_seen)
                VALUES 
                    (%s, %s, FALSE, %s)
                """
                
                self.cursor.execute(insert_sql, (code, default_name, datetime.now()))
                self.connection.commit()
                print(f"  ℹ 自动发现新代码: {table}.{code_field}={code}")
                
        except mysql.connector.Error as err:
            # 忽略重复键错误
            if err.errno != 1062:
                print(f"  ⚠ 插入代码失败: {err}")
    
    # ========== 查询方法 ==========
    
    def get_position_by_tag(self, tag: str) -> Optional[Dict]:
        """
        根据 tag 查询位置信息
        
        Args:
            tag (str): Tag标签
            
        Returns:
            Optional[Dict]: 位置数据字典,不存在返回 None
        """
        query_sql = "SELECT * FROM rb_position_data WHERE tag = %s"
        self.cursor.execute(query_sql, (tag,))
        return self.cursor.fetchone()
    
    def get_position_by_rbindex(self, rbindex: str) -> Optional[Dict]:
        """
        根据 RBindex 查询位置信息
        
        Args:
            rbindex (str): RB位置索引
            
        Returns:
            Optional[Dict]: 位置数据字典,不存在返回 None
        """
        query_sql = "SELECT * FROM rb_position_data WHERE RBindex = %s"
        self.cursor.execute(query_sql, (rbindex,))
        return self.cursor.fetchone()
    
    def get_all_positions(self, plc: Optional[str] = None) -> List[Dict]:
        """
        查询所有位置信息
        
        Args:
            plc (str, optional): PLC名称,用于过滤
            
        Returns:
            List[Dict]: 位置数据列表
        """
        if plc:
            query_sql = "SELECT * FROM rb_position_data WHERE plc = %s ORDER BY id"
            self.cursor.execute(query_sql, (plc,))
        else:
            query_sql = "SELECT * FROM rb_position_data ORDER BY id"
            self.cursor.execute(query_sql)
        
        return self.cursor.fetchall()
    
    def get_occupied_positions(self) -> List[Dict]:
        """
        查询有车辆的位置
        
        Returns:
            List[Dict]: 有车辆的位置数据列表
        """
        query_sql = """
        SELECT * FROM rb_position_data 
        WHERE vehicle_id IS NOT NULL 
        ORDER BY vehicle_updated_at DESC
        """
        self.cursor.execute(query_sql)
        return self.cursor.fetchall()
    
    def get_empty_positions(self) -> List[Dict]:
        """
        查询空位置
        
        Returns:
            List[Dict]: 空位置数据列表
        """
        query_sql = """
        SELECT * FROM rb_position_data 
        WHERE vehicle_id IS NULL 
        ORDER BY id
        """
        self.cursor.execute(query_sql)
        return self.cursor.fetchall()
    
    # ========== 清空/重置方法 ==========
    
    def clear_vehicle_by_tag(self, tag: str) -> bool:
        """
        清空指定位置的车辆数据(车辆离开时调用)
        
        Args:
            tag (str): Tag标签
            
        Returns:
            bool: 是否成功
        """
        try:
            update_sql = """
            UPDATE rb_position_data
            SET 
                vehicle_id = NULL,
                body_type = NULL,
                color_code = NULL,
                platform_code = NULL,
                black_roof_flag = NULL,
                rework_flag = NULL,
                reserved_1 = NULL,
                reserved_2 = NULL,
                raw_data = NULL,
                vehicle_updated_at = NULL
            WHERE tag = %s
            """
            
            self.cursor.execute(update_sql, (tag,))
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                print(f"✓ 清空成功: tag={tag}")
                return True
            else:
                print(f"⚠ 未找到对应的 tag: {tag}")
                return False
                
        except Exception as e:
            print(f"✗ 清空失败: {e}")
            self.connection.rollback()
            return False
    
    # ========== 统计方法 ==========
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计数据
        """
        stats = {}
        
        # 总位置数
        self.cursor.execute("SELECT COUNT(*) as count FROM rb_position_data")
        stats['total_positions'] = self.cursor.fetchone()['count']
        
        # 有车位置数
        self.cursor.execute("SELECT COUNT(*) as count FROM rb_position_data WHERE vehicle_id IS NOT NULL")
        stats['occupied_positions'] = self.cursor.fetchone()['count']
        
        # 空位置数
        stats['empty_positions'] = stats['total_positions'] - stats['occupied_positions']
        
        # 按 PLC 统计
        self.cursor.execute("""
            SELECT plc, 
                   COUNT(*) as total,
                   SUM(CASE WHEN vehicle_id IS NOT NULL THEN 1 ELSE 0 END) as occupied
            FROM rb_position_data
            GROUP BY plc
        """)
        stats['by_plc'] = self.cursor.fetchall()
        
        return stats


# ========== 使用示例 ==========

def example_usage():
    """使用示例"""
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'your_password',
        'database': 'your_database'
    }
    
    # 使用上下文管理器
    with RBPositionDataManager(db_config) as manager:
        
        # 1. 更新车辆数据 (WebSocket 接收到数据时调用)
        tag = ".L3F13_1A_1A010LT_1A010RB.IL.SD.M1003_BodyID"
        raw_data = "12345678901234VS21J2LA1MLB100"  # 示例30字符数据
        manager.update_vehicle_by_tag(tag, raw_data)
        
        # 2. 查询位置信息
        position = manager.get_position_by_tag(tag)
        print(f"位置信息: {position}")
        
        # 3. 查询所有有车的位置
        occupied = manager.get_occupied_positions()
        print(f"有车位置数: {len(occupied)}")
        
        # 4. 获取统计信息
        stats = manager.get_statistics()
        print(f"统计信息: {stats}")
        
        # 5. 清空车辆数据 (车辆离开时)
        manager.clear_vehicle_by_tag(tag)


if __name__ == '__main__':
    example_usage()
