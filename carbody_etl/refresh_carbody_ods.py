#!/usr/bin/env python3
"""
carbody ODS 增量刷新脚本
从 SQL Server DXQcontrol_SVWMEB_BI_DWH 抽取 carbody_history 增量行
写入 PostgreSQL analytics_db.ods.carbody_history

修改时间：2026-05-16 18:30 Asia/Shanghai
主要功能：
1. 流式分批从 SQL Server 提取增量数据 (fetchmany)
2. 同一事务内完成 PostgreSQL ODS 写入与水位更新 (Atomic Sync)
3. 设置会话时区以正确处理 timestamptz 字段
4. 调用存储过程完成 DIM 层聚合与 UPSERT
5. 基于 PostgreSQL Advisory Lock 的并发控制
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timezone
import psycopg2
from psycopg2 import extras
import pytds
from dotenv import load_dotenv
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("refresh_carbody_ods")

# PostgreSQL ods.carbody_history 的 quoted 列名（确保大小写敏感性）
ODS_COLUMNS = [
    '"ID"', '"DATE_EVT"', '"SHIFT_NR"', '"RW_STATION_ID"',
    '"RW_STATION_STATUS"', '"SKID_ID"', '"SKID_TYPE"', '"SKID_IS_EMPTY"',
    '"BODY_ID"', '"BODY_TYPE"', '"MDS_DATA"', '"MDS_TELEGRAM_TYPE"',
    '"FK_ERP_HIST_ID"', '"CYCLE_NUM"', '"PRODUCTION_SEGMENT_ID"',
    '"ETL_MODIFY_DATE"', '"ETL_SOURCE_ID"',
]

def load_project_env():
    """加载环境变量"""
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

def connect_pg_target():
    """连接 PostgreSQL analytics_db，并设置会话时区以正确处理 timestamptz"""
    tz = os.getenv("CARBODY_REFRESH_TIMEZONE", "Asia/Shanghai")
    return psycopg2.connect(
        host=os.getenv("CARBODY_TARGET_DB_HOST", "localhost"),
        port=os.getenv("CARBODY_TARGET_DB_PORT", "5432"),
        dbname=os.getenv("CARBODY_TARGET_DB_NAME", "analytics_db"),
        user=os.getenv("CARBODY_TARGET_DB_USER", "root"),
        password=os.getenv("CARBODY_TARGET_DB_PASSWORD", "root"),
        options=f"-c timezone={tz}"
    )

def connect_ss_source():
    """连接 SQL Server 源库"""
    return pytds.connect(
        server=os.getenv("CARBODY_SOURCE_DB_HOST"),
        port=int(os.getenv("CARBODY_SOURCE_DB_PORT", "1433")),
        database=os.getenv("CARBODY_SOURCE_DB_NAME"),
        user=os.getenv("CARBODY_SOURCE_DB_USER"),
        password=os.getenv("CARBODY_SOURCE_DB_PASSWORD"),
        autocommit=True,
    )

def acquire_lock(pg_conn, lock_key: int) -> bool:
    """获取 PostgreSQL advisory lock"""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", (lock_key,))
        return cur.fetchone()[0]

def release_lock(pg_conn, lock_key: int):
    """释放 PostgreSQL advisory lock"""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))

def read_watermark(pg_conn) -> int:
    """从 meta 表读取上次同步的最大 ID"""
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(watermark_value::numeric, 0) "
            "FROM meta.refresh_watermark "
            "WHERE source_name = 'ods.carbody_history.max_id'"
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

def process_incremental_sync(ss_conn, pg_conn, last_id, batch_size):
    """流式拉取并分批写入 ODS，同时更新水位（同一事务控制）"""
    schema = os.getenv("CARBODY_SOURCE_DB_SCHEMA", "dbo")
    table = os.getenv("CARBODY_SOURCE_TABLE_NAME", "carbody_history")
    sql = f"SELECT * FROM {schema}.{table} WHERE ID > %s ORDER BY ID"
    total_inserted = 0
    
    with ss_conn.cursor() as ss_cur:
        ss_cur.execute(sql, (last_id,))
        
        while True:
            rows = ss_cur.fetchmany(batch_size)
            if not rows:
                break
                
            # 在同一个事务中完成 写入 ODS + 更新水位
            with pg_conn:
                with pg_conn.cursor() as cur:
                    # 1. 批量插入 ODS
                    insert_sql = (
                        f'INSERT INTO ods.carbody_history ({", ".join(ODS_COLUMNS)}) '
                        f"VALUES %s"
                    )
                    extras.execute_values(cur, insert_sql, rows)
                    
                    # 2. 紧接着更新本批次后的水位
                    cur.execute(
                        "INSERT INTO meta.refresh_watermark(source_name, watermark_value, updated_at) "
                        "VALUES ('ods.carbody_history.max_id', "
                        "(SELECT COALESCE(MAX(\"ID\")::text, '0') FROM ods.carbody_history), now()) "
                        "ON CONFLICT (source_name) DO UPDATE SET "
                        "watermark_value = EXCLUDED.watermark_value, "
                        "updated_at = EXCLUDED.updated_at"
                    )
            total_inserted += len(rows)
            logger.info(f"已同步 {total_inserted} 条记录...")
            
    return total_inserted

def call_refresh_carbody_dim(pg_conn):
    """触发 DIM 层聚合转换存储过程"""
    with pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("CALL meta.refresh_carbody_dim()")

def refresh_fct_view(pg_conn):
    """刷新 FCT 层物化视图"""
    with pg_conn:
        with pg_conn.cursor() as cur:
            # 这里如果不加 CONCURRENTLY，刷新时会锁定视图
            # 只有在创建了唯一索引的情况下才能用 CONCURRENTLY
            cur.execute("REFRESH MATERIALIZED VIEW fct.fct_vehicle_defect_enriched")

def log_sync_job(pg_conn, status: str, message: str):
    """记录作业日志"""
    with pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta.sync_job_log(job_name, status, finished_at, message) "
                "VALUES ('refresh_carbody_ods', %s, now(), %s)",
                (status, message),
            )

def main():
    load_project_env()
    
    parser = argparse.ArgumentParser(description="Carbody History ODS Sync Script")
    parser.add_argument("--full-refresh", action="store_true", help="执行全量刷新（重置水位并清空 ODS）")
    args = parser.parse_args()

    lock_key = int(os.getenv("CARBODY_REFRESH_LOCK_KEY", "20260515"))
    batch_size = int(os.getenv("CARBODY_REFRESH_BATCH_SIZE", "5000"))

    pg_conn = connect_pg_target()
    try:
        if not acquire_lock(pg_conn, lock_key):
            logger.warning("上一轮刷新任务尚未结束，跳过本轮执行。")
            return

        ss_conn = connect_ss_source()
        try:
            # ---- 全量刷新模式处理 ----
            if args.full_refresh:
                logger.info("检测到 --full-refresh 参数，准备执行全量重刷...")
                with pg_conn:
                    with pg_conn.cursor() as cur:
                        cur.execute(
                            "UPDATE meta.refresh_watermark SET watermark_value='0' "
                            "WHERE source_name='ods.carbody_history.max_id'"
                        )
                        cur.execute("TRUNCATE TABLE ods.carbody_history")
                        # 保持 dim.carbody_registry 不截断，避免业务中断
                logger.info("水位已重置，ODS 已清空。")

            # ---- 执行同步 ----
            v_last_id = 0 if args.full_refresh else read_watermark(pg_conn)
            logger.info(f"开始同步，起始 ID: {v_last_id}")
            
            inserted = process_incremental_sync(ss_conn, pg_conn, v_last_id, batch_size)

            if inserted == 0:
                logger.info("没有发现新数据。")
                log_sync_job(pg_conn, "success", "ods_new: 0 rows")
                return

            # ---- 触发下游转换 ----
            logger.info("数据已写入 ODS，正在触发 DIM 层转换...")
            call_refresh_carbody_dim(pg_conn)
            logger.info("DIM 层 UPSERT 完成。")

            # 新增：显式刷新 FCT 物化视图
            logger.info("正在刷新 FCT 层物化视图 (fct_vehicle_defect_enriched)...")
            refresh_fct_view(pg_conn)
            logger.info("FCT 层刷新成功。")

            # ---- 记录成功日志 ----
            log_sync_job(pg_conn, "success", f"ods_new: {inserted} rows")
            logger.info(f"作业执行成功，共同步 {inserted} 行。")

        finally:
            ss_conn.close()
    except Exception as e:
        logger.error("refresh_carbody_ods 执行过程中发生异常:", exc_info=True)
        try:
            log_sync_job(pg_conn, "failed", str(e))
        except:
            pass
        sys.exit(1)
    finally:
        release_lock(pg_conn, lock_key)
        pg_conn.close()

if __name__ == "__main__":
    main()
