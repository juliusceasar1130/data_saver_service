#!/usr/bin/env python3
"""
修改时间：2026-04-15 15:24 Asia/Shanghai
主要修改内容：
1. 新增 `history_station_defect_summary` 固定窗口保留参数与裁剪逻辑
2. 在整轮增量刷新成功后执行 retention cleanup，并输出是否裁剪日志
3. 在 `--print-status` 中补充窗口配置与当前最小/最大范围
4. 支持目标库固定 PostgreSQL、源库支持 PostgreSQL / SQL Server 双方言
5. 新增源库类型、schema 等配置，并阻止不完整源库配置的静默回退
6. 保留本地汇总表的 UPSERT、水位推进、日志记录与 advisory lock 控制
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor, execute_values


JOB_NAME = "refresh_history_station_defect_summary"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_MAP_FILE = PROJECT_ROOT / "defect_summary_etl" / "model_map.json"
DEFAULT_TIMEZONE = "Asia/Shanghai"
ALLOWED_BOOTSTRAP_MODES = {"from_summary", "from_zero"}
ALLOWED_SOURCE_DB_TYPES = {"postgres", "sqlserver"}
ALLOWED_RETENTION_MODES = {"off", "max_rows", "max_months", "both"}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SUMMARY_COLUMNS = [
    "history_id",
    "model",
    "type_name",
    "black_roof",
    "serial_number",
    "date_time",
    "color_code",
    "tunnel",
    "cycle",
    "station_1_defect_count",
    "station_2_defect_count",
    "station_3_defect_count",
    "station_4_defect_count",
    "station_5_defect_count",
    "total_defect_count",
]
TARGET_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS public.model_attribute_map (
    model INTEGER PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    black_roof VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS public.history_station_defect_summary (
    history_id INTEGER PRIMARY KEY,
    model INTEGER NOT NULL,
    type_name VARCHAR(100),
    black_roof VARCHAR(100),
    serial_number VARCHAR(255),
    date_time TIMESTAMP NOT NULL,
    color_code VARCHAR(255),
    tunnel INTEGER,
    cycle INTEGER,
    station_1_defect_count INTEGER NOT NULL DEFAULT 0,
    station_2_defect_count INTEGER NOT NULL DEFAULT 0,
    station_3_defect_count INTEGER NOT NULL DEFAULT 0,
    station_4_defect_count INTEGER NOT NULL DEFAULT 0,
    station_5_defect_count INTEGER NOT NULL DEFAULT 0,
    total_defect_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_history_station_defect_summary_date_time
ON public.history_station_defect_summary(date_time);

CREATE INDEX IF NOT EXISTS idx_history_station_defect_summary_serial_number
ON public.history_station_defect_summary(serial_number);

CREATE TABLE IF NOT EXISTS public.history_station_defect_summary_refresh_state (
    job_name TEXT PRIMARY KEY,
    last_success_history_id INTEGER NOT NULL DEFAULT 0,
    last_success_date_time TIMESTAMP NULL,
    last_run_started_at TIMESTAMPTZ NULL,
    last_run_finished_at TIMESTAMPTZ NULL,
    last_status TEXT NULL,
    last_message TEXT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.history_station_defect_summary_refresh_log (
    id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    source_db_host TEXT NULL,
    source_db_name TEXT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ NULL,
    status TEXT NOT NULL,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    upserted_count INTEGER NOT NULL DEFAULT 0,
    batch_min_history_id INTEGER NULL,
    batch_max_history_id INTEGER NULL,
    watermark_before INTEGER NULL,
    watermark_after INTEGER NULL,
    message TEXT NULL
);
"""
UPSERT_SUMMARY_SQL = f"""
INSERT INTO public.history_station_defect_summary (
    {", ".join(SUMMARY_COLUMNS)}
)
VALUES %s
ON CONFLICT (history_id) DO UPDATE
SET
    model = EXCLUDED.model,
    type_name = EXCLUDED.type_name,
    black_roof = EXCLUDED.black_roof,
    serial_number = EXCLUDED.serial_number,
    date_time = EXCLUDED.date_time,
    color_code = EXCLUDED.color_code,
    tunnel = EXCLUDED.tunnel,
    cycle = EXCLUDED.cycle,
    station_1_defect_count = EXCLUDED.station_1_defect_count,
    station_2_defect_count = EXCLUDED.station_2_defect_count,
    station_3_defect_count = EXCLUDED.station_3_defect_count,
    station_4_defect_count = EXCLUDED.station_4_defect_count,
    station_5_defect_count = EXCLUDED.station_5_defect_count,
    total_defect_count = EXCLUDED.total_defect_count;
"""


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class SourceDbConfig(DbConfig):
    db_type: str
    schema: str


@dataclass(frozen=True)
class RuntimeSettings:
    target_db: DbConfig
    source_db: SourceDbConfig
    batch_size: int
    replay_history_window: int
    lock_key: int
    bootstrap_mode: str
    timezone_name: str
    retention_mode: str
    retention_max_rows: int
    retention_max_months: int
    retention_delete_batch_size: int


@dataclass
class RefreshState:
    job_name: str
    last_success_history_id: int
    last_success_date_time: Optional[datetime]
    last_run_started_at: Optional[datetime]
    last_run_finished_at: Optional[datetime]
    last_status: Optional[str]
    last_message: Optional[str]
    updated_at: Optional[datetime]


@dataclass(frozen=True)
class BatchResult:
    state: RefreshState
    batch_type: str
    candidate_count: int
    replay_count: int
    new_count: int
    upserted_count: int
    watermark_before: int
    watermark_after: int


@dataclass(frozen=True)
class SummaryTableStats:
    row_count: int
    min_history_id: Optional[int]
    max_history_id: Optional[int]
    min_date_time: Optional[datetime]
    max_date_time: Optional[datetime]


@dataclass(frozen=True)
class RetentionCleanupResult:
    mode: str
    deleted_count: int
    row_count_before: int
    row_count_after: int
    min_history_id_after: Optional[int]
    max_history_id_after: Optional[int]
    min_date_time_after: Optional[datetime]
    max_date_time_after: Optional[datetime]


def load_project_env() -> None:
    project_env = PROJECT_ROOT / ".env"
    if project_env.exists():
        load_dotenv(project_env, override=False)
    load_dotenv(override=False)


def setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("DEFECT_SUMMARY_LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("pytds").setLevel(logging.WARNING)


logger = logging.getLogger("history_station_defect_summary_refresh")


def getenv_str(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def getenv_optional_secret(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    return value.strip()


def getenv_int(name: str, default: int) -> int:
    raw = getenv_str(name)
    if raw is None:
        return default
    return int(raw)


def ensure_identifier(name: str, value: str) -> str:
    if not IDENTIFIER_PATTERN.match(value):
        raise ValueError(f"{name} 仅支持字母、数字和下划线，且不能以数字开头: {value}")
    return value


def build_target_db_config() -> DbConfig:
    return DbConfig(
        host=getenv_str("DEFECT_TARGET_DB_HOST", "localhost") or "localhost",
        port=getenv_int("DEFECT_TARGET_DB_PORT", 5432),
        user=getenv_str("DEFECT_TARGET_DB_USER", "root") or "root",
        password=getenv_str("DEFECT_TARGET_DB_PASSWORD", "root") or "root",
        database=getenv_str("DEFECT_TARGET_DB_NAME", "defect_db") or "defect_db",
    )


def build_source_db_config(target_db: DbConfig) -> SourceDbConfig:
    source_db_type = getenv_str("DEFECT_SOURCE_DB_TYPE")
    source_host = getenv_str("DEFECT_SOURCE_DB_HOST")
    source_port = getenv_str("DEFECT_SOURCE_DB_PORT")
    source_name = getenv_str("DEFECT_SOURCE_DB_NAME")
    source_user = getenv_str("DEFECT_SOURCE_DB_USER")
    source_password = getenv_optional_secret("DEFECT_SOURCE_DB_PASSWORD")

    source_fields = {
        "DEFECT_SOURCE_DB_TYPE": source_db_type,
        "DEFECT_SOURCE_DB_HOST": source_host,
        "DEFECT_SOURCE_DB_PORT": source_port,
        "DEFECT_SOURCE_DB_NAME": source_name,
        "DEFECT_SOURCE_DB_USER": source_user,
        "DEFECT_SOURCE_DB_PASSWORD": source_password,
    }
    provided_fields = [name for name, value in source_fields.items() if value is not None]
    if not provided_fields:
        return SourceDbConfig(
            host=target_db.host,
            port=target_db.port,
            user=target_db.user,
            password=target_db.password,
            database=target_db.database,
            db_type="postgres",
            schema="public",
        )

    missing_fields = [name for name, value in source_fields.items() if value is None]
    if missing_fields:
        raise ValueError(
            "已配置部分源库参数，但缺少必要字段: " + ", ".join(missing_fields)
        )

    normalized_type = (source_db_type or "").lower()
    if normalized_type not in ALLOWED_SOURCE_DB_TYPES:
        raise ValueError(
            f"DEFECT_SOURCE_DB_TYPE 仅支持: {', '.join(sorted(ALLOWED_SOURCE_DB_TYPES))}"
        )

    default_schema = "dbo" if normalized_type == "sqlserver" else "public"
    schema = ensure_identifier(
        "DEFECT_SOURCE_DB_SCHEMA",
        getenv_str("DEFECT_SOURCE_DB_SCHEMA", default_schema) or default_schema,
    )

    return SourceDbConfig(
        host=source_host or target_db.host,
        port=int(source_port),
        user=source_user or target_db.user,
        password=source_password if source_password is not None else target_db.password,
        database=source_name or target_db.database,
        db_type=normalized_type,
        schema=schema,
    )


def build_runtime_settings() -> RuntimeSettings:
    target_db = build_target_db_config()
    source_db = build_source_db_config(target_db)
    batch_size = getenv_int("DEFECT_SUMMARY_BATCH_SIZE", 2000)
    replay_history_window = getenv_int("DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW", 500)
    lock_key = getenv_int("DEFECT_SUMMARY_LOCK_KEY", 20260413)
    bootstrap_mode = getenv_str("DEFECT_SUMMARY_BOOTSTRAP_MODE", "from_summary") or "from_summary"
    timezone_name = getenv_str("DEFECT_SUMMARY_TIMEZONE", DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE
    retention_mode = getenv_str("DEFECT_SUMMARY_RETENTION_MODE", "off") or "off"
    retention_max_rows = getenv_int("DEFECT_SUMMARY_RETENTION_MAX_ROWS", 60000)
    retention_max_months = getenv_int("DEFECT_SUMMARY_RETENTION_MAX_MONTHS", 3)
    retention_delete_batch_size = getenv_int("DEFECT_SUMMARY_RETENTION_DELETE_BATCH_SIZE", 5000)

    if batch_size <= 0:
        raise ValueError("DEFECT_SUMMARY_BATCH_SIZE 必须大于 0")
    if replay_history_window < 0:
        raise ValueError("DEFECT_SUMMARY_REPLAY_HISTORY_WINDOW 不能小于 0")
    if bootstrap_mode not in ALLOWED_BOOTSTRAP_MODES:
        raise ValueError(
            f"DEFECT_SUMMARY_BOOTSTRAP_MODE 仅支持: {', '.join(sorted(ALLOWED_BOOTSTRAP_MODES))}"
        )
    if retention_mode not in ALLOWED_RETENTION_MODES:
        raise ValueError(
            f"DEFECT_SUMMARY_RETENTION_MODE 仅支持: {', '.join(sorted(ALLOWED_RETENTION_MODES))}"
        )
    if retention_delete_batch_size <= 0:
        raise ValueError("DEFECT_SUMMARY_RETENTION_DELETE_BATCH_SIZE 必须大于 0")
    if retention_mode in {"max_rows", "both"} and retention_max_rows <= 0:
        raise ValueError("DEFECT_SUMMARY_RETENTION_MAX_ROWS 在 max_rows/both 模式下必须大于 0")
    if retention_mode in {"max_months", "both"} and retention_max_months <= 0:
        raise ValueError("DEFECT_SUMMARY_RETENTION_MAX_MONTHS 在 max_months/both 模式下必须大于 0")

    return RuntimeSettings(
        target_db=target_db,
        source_db=source_db,
        batch_size=batch_size,
        replay_history_window=replay_history_window,
        lock_key=lock_key,
        bootstrap_mode=bootstrap_mode,
        timezone_name=timezone_name,
        retention_mode=retention_mode,
        retention_max_rows=retention_max_rows,
        retention_max_months=retention_max_months,
        retention_delete_batch_size=retention_delete_batch_size,
    )


def connect_target_db(config: DbConfig, timezone_name: str):
    connection = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
    )
    connection.autocommit = False
    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE %s", (timezone_name,))
    connection.commit()
    return connection


def connect_postgres_source(config: SourceDbConfig, timezone_name: str):
    connection = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
    )
    connection.set_session(readonly=True, autocommit=True)
    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE %s", (timezone_name,))
    return connection


def connect_sqlserver_source(config: SourceDbConfig):
    try:
        import pytds
    except ImportError as exc:
        raise RuntimeError(
            "当前环境未安装 python-tds，无法连接 SQL Server。请先安装 `python-tds`。"
        ) from exc

    return pytds.connect(
        server=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        autocommit=True,
    )


def connect_source_db(config: SourceDbConfig, timezone_name: str):
    if config.db_type == "postgres":
        return connect_postgres_source(config, timezone_name)
    if config.db_type == "sqlserver":
        return connect_sqlserver_source(config)
    raise ValueError(f"不支持的源库类型: {config.db_type}")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def execute_schema_sql(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(TARGET_SCHEMA_SQL)
    connection.commit()


def load_model_map_rows() -> List[Tuple[int, str, Optional[str]]]:
    if not MODEL_MAP_FILE.exists():
        raise FileNotFoundError(f"找不到映射文件: {MODEL_MAP_FILE}")

    with MODEL_MAP_FILE.open("r", encoding="utf-8") as fp:
        raw_items = json.load(fp)

    model_rows: List[Tuple[int, str, Optional[str]]] = []
    for item in raw_items:
        model_rows.append((int(item["model"]), item["type_name"], item.get("black_roof")))
    return model_rows


def sync_local_model_map(connection) -> None:
    model_rows = load_model_map_rows()
    with connection.cursor() as cursor:
        execute_values(
            cursor,
            """
            INSERT INTO public.model_attribute_map (model, type_name, black_roof)
            VALUES %s
            ON CONFLICT (model) DO UPDATE
            SET
                type_name = EXCLUDED.type_name,
                black_roof = EXCLUDED.black_roof;
            """,
            model_rows,
        )
    connection.commit()


def ensure_target_schema(connection) -> None:
    execute_schema_sql(connection)
    sync_local_model_map(connection)


def fetch_state(connection) -> Optional[RefreshState]:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                job_name,
                last_success_history_id,
                last_success_date_time,
                last_run_started_at,
                last_run_finished_at,
                last_status,
                last_message,
                updated_at
            FROM public.history_station_defect_summary_refresh_state
            WHERE job_name = %s
            """,
            (JOB_NAME,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return RefreshState(
        job_name=row["job_name"],
        last_success_history_id=int(row["last_success_history_id"]),
        last_success_date_time=row["last_success_date_time"],
        last_run_started_at=row["last_run_started_at"],
        last_run_finished_at=row["last_run_finished_at"],
        last_status=row["last_status"],
        last_message=row["last_message"],
        updated_at=row["updated_at"],
    )


def insert_refresh_log(
    connection,
    settings: RuntimeSettings,
    *,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    candidate_count: int,
    upserted_count: int,
    batch_min_history_id: Optional[int],
    batch_max_history_id: Optional[int],
    watermark_before: Optional[int],
    watermark_after: Optional[int],
    message: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.history_station_defect_summary_refresh_log (
                job_name,
                source_db_host,
                source_db_name,
                started_at,
                finished_at,
                status,
                candidate_count,
                upserted_count,
                batch_min_history_id,
                batch_max_history_id,
                watermark_before,
                watermark_after,
                message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                JOB_NAME,
                settings.source_db.host,
                settings.source_db.database,
                started_at,
                finished_at,
                status,
                candidate_count,
                upserted_count,
                batch_min_history_id,
                batch_max_history_id,
                watermark_before,
                watermark_after,
                message,
            ),
        )


def update_refresh_state(
    connection,
    *,
    last_success_history_id: int,
    last_success_date_time: Optional[datetime],
    last_run_started_at: datetime,
    last_run_finished_at: datetime,
    last_status: str,
    last_message: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.history_station_defect_summary_refresh_state (
                job_name,
                last_success_history_id,
                last_success_date_time,
                last_run_started_at,
                last_run_finished_at,
                last_status,
                last_message,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (job_name) DO UPDATE
            SET
                last_success_history_id = EXCLUDED.last_success_history_id,
                last_success_date_time = EXCLUDED.last_success_date_time,
                last_run_started_at = EXCLUDED.last_run_started_at,
                last_run_finished_at = EXCLUDED.last_run_finished_at,
                last_status = EXCLUDED.last_status,
                last_message = EXCLUDED.last_message,
                updated_at = now()
            """,
            (
                JOB_NAME,
                last_success_history_id,
                last_success_date_time,
                last_run_started_at,
                last_run_finished_at,
                last_status,
                last_message,
            ),
        )


def initialize_state(connection, settings: RuntimeSettings) -> RefreshState:
    existing_state = fetch_state(connection)
    if existing_state is not None:
        return existing_state

    started_at = utc_now()
    finished_at = started_at

    last_success_history_id = 0
    last_success_date_time: Optional[datetime] = None
    if settings.bootstrap_mode == "from_summary":
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(MAX(history_id), 0) AS max_history_id,
                    MAX(date_time) AS max_date_time
                FROM public.history_station_defect_summary
                """
            )
            row = cursor.fetchone()
        last_success_history_id = int(row["max_history_id"])
        last_success_date_time = row["max_date_time"]

    message = (
        f"state initialized with bootstrap_mode={settings.bootstrap_mode}, "
        f"history_id={last_success_history_id}"
    )

    update_refresh_state(
        connection,
        last_success_history_id=last_success_history_id,
        last_success_date_time=last_success_date_time,
        last_run_started_at=started_at,
        last_run_finished_at=finished_at,
        last_status="initialized",
        last_message=message,
    )
    insert_refresh_log(
        connection,
        settings,
        started_at=started_at,
        finished_at=finished_at,
        status="initialized",
        candidate_count=0,
        upserted_count=0,
        batch_min_history_id=None,
        batch_max_history_id=None,
        watermark_before=None,
        watermark_after=last_success_history_id,
        message=message,
    )
    connection.commit()

    logger.info("初始化刷新状态完成，起始水位 history_id=%s", last_success_history_id)
    return fetch_state(connection)  # type: ignore[return-value]


def load_local_model_map(connection) -> Dict[int, Dict[str, Optional[str]]]:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT model, type_name, black_roof
            FROM public.model_attribute_map
            """
        )
        rows = cursor.fetchall()

    return {
        int(row["model"]): {
            "type_name": row["type_name"],
            "black_roof": row["black_roof"],
        }
        for row in rows
    }


def acquire_advisory_lock(connection, lock_key: int) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", (lock_key,))
        return bool(cursor.fetchone()[0])


def release_advisory_lock(connection, lock_key: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
    connection.commit()


def record_non_batch_result(
    connection,
    settings: RuntimeSettings,
    state: RefreshState,
    *,
    status: str,
    message: str,
) -> None:
    started_at = utc_now()
    finished_at = started_at
    update_refresh_state(
        connection,
        last_success_history_id=state.last_success_history_id,
        last_success_date_time=state.last_success_date_time,
        last_run_started_at=started_at,
        last_run_finished_at=finished_at,
        last_status=status,
        last_message=message,
    )
    insert_refresh_log(
        connection,
        settings,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        candidate_count=0,
        upserted_count=0,
        batch_min_history_id=None,
        batch_max_history_id=None,
        watermark_before=state.last_success_history_id,
        watermark_after=state.last_success_history_id,
        message=message,
    )
    connection.commit()


def fetch_summary_table_stats(connection) -> SummaryTableStats:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS row_count,
                MIN(history_id) AS min_history_id,
                MAX(history_id) AS max_history_id,
                MIN(date_time) AS min_date_time,
                MAX(date_time) AS max_date_time
            FROM public.history_station_defect_summary
            """
        )
        row = cursor.fetchone()

    return SummaryTableStats(
        row_count=int(row["row_count"]),
        min_history_id=int(row["min_history_id"]) if row["min_history_id"] is not None else None,
        max_history_id=int(row["max_history_id"]) if row["max_history_id"] is not None else None,
        min_date_time=row["min_date_time"],
        max_date_time=row["max_date_time"],
    )


def fetch_keep_min_history_id(connection, max_rows: int) -> Optional[int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT MIN(history_id)
            FROM (
                SELECT history_id
                FROM public.history_station_defect_summary
                ORDER BY history_id DESC
                LIMIT %s
            ) recent_rows
            """,
            (max_rows,),
        )
        value = cursor.fetchone()[0]
    return int(value) if value is not None else None


def delete_rows_by_history_id(connection, boundary_history_id: int, batch_size: int) -> int:
    total_deleted = 0
    while True:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM public.history_station_defect_summary
                WHERE ctid IN (
                    SELECT ctid
                    FROM public.history_station_defect_summary
                    WHERE history_id < %s
                    ORDER BY history_id ASC
                    LIMIT %s
                )
                """,
                (boundary_history_id, batch_size),
            )
            deleted = cursor.rowcount
        total_deleted += deleted
        if deleted == 0:
            break
    return total_deleted


def delete_rows_by_cutoff_months(connection, max_months: int, batch_size: int) -> int:
    total_deleted = 0
    while True:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM public.history_station_defect_summary
                WHERE ctid IN (
                    SELECT ctid
                    FROM public.history_station_defect_summary
                    WHERE date_time < (CURRENT_TIMESTAMP - (%s * INTERVAL '1 month'))
                    ORDER BY date_time ASC, history_id ASC
                    LIMIT %s
                )
                """,
                (max_months, batch_size),
            )
            deleted = cursor.rowcount
        total_deleted += deleted
        if deleted == 0:
            break
    return total_deleted


def cleanup_summary_retention_window(
    connection,
    settings: RuntimeSettings,
    state: RefreshState,
) -> RetentionCleanupResult:
    before_stats = fetch_summary_table_stats(connection)
    deleted_count = 0

    if settings.retention_mode == "off":
        return RetentionCleanupResult(
            mode=settings.retention_mode,
            deleted_count=0,
            row_count_before=before_stats.row_count,
            row_count_after=before_stats.row_count,
            min_history_id_after=before_stats.min_history_id,
            max_history_id_after=before_stats.max_history_id,
            min_date_time_after=before_stats.min_date_time,
            max_date_time_after=before_stats.max_date_time,
        )

    if settings.retention_mode in {"max_rows", "both"}:
        boundary_history_id = fetch_keep_min_history_id(connection, settings.retention_max_rows)
        if boundary_history_id is not None:
            deleted_count += delete_rows_by_history_id(
                connection,
                boundary_history_id,
                settings.retention_delete_batch_size,
            )

    if settings.retention_mode in {"max_months", "both"}:
        deleted_count += delete_rows_by_cutoff_months(
            connection,
            settings.retention_max_months,
            settings.retention_delete_batch_size,
        )

    after_stats = fetch_summary_table_stats(connection)
    if deleted_count > 0:
        message = (
            f"retention applied: mode={settings.retention_mode}, "
            f"deleted_count={deleted_count}, "
            f"row_count {before_stats.row_count}->{after_stats.row_count}, "
            f"history_id_after={after_stats.min_history_id}->{after_stats.max_history_id}, "
            f"date_time_after={after_stats.min_date_time}->{after_stats.max_date_time}"
        )
        status = "retention_applied"
    else:
        message = (
            f"retention noop: mode={settings.retention_mode}, "
            f"deleted_count=0, "
            f"row_count={after_stats.row_count}, "
            f"history_id_after={after_stats.min_history_id}->{after_stats.max_history_id}, "
            f"date_time_after={after_stats.min_date_time}->{after_stats.max_date_time}"
        )
        status = "retention_noop"

    logger.info(message)
    insert_refresh_log(
        connection,
        settings,
        started_at=utc_now(),
        finished_at=utc_now(),
        status=status,
        candidate_count=deleted_count,
        upserted_count=0,
        batch_min_history_id=None,
        batch_max_history_id=None,
        watermark_before=state.last_success_history_id,
        watermark_after=state.last_success_history_id,
        message=message,
    )
    connection.commit()

    return RetentionCleanupResult(
        mode=settings.retention_mode,
        deleted_count=deleted_count,
        row_count_before=before_stats.row_count,
        row_count_after=after_stats.row_count,
        min_history_id_after=after_stats.min_history_id,
        max_history_id_after=after_stats.max_history_id,
        min_date_time_after=after_stats.min_date_time,
        max_date_time_after=after_stats.max_date_time,
    )


def fetchall_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def build_source_table_name(config: SourceDbConfig, table_name: str) -> str:
    if config.db_type == "postgres":
        return f"{config.schema}.{table_name}"
    if config.db_type == "sqlserver":
        return f"[{config.schema}].[{table_name}]"
    raise ValueError(f"不支持的源库类型: {config.db_type}")


def fetch_candidate_history_ids_postgres(
    source_connection,
    source_config: SourceDbConfig,
    last_success_history_id: int,
    replay_history_window: int,
    batch_size: int,
) -> Tuple[List[int], List[int]]:
    history_table = build_source_table_name(source_config, "history")
    replay_ids: List[int] = []
    if last_success_history_id > 0 and replay_history_window > 0:
        replay_start = max(last_success_history_id - replay_history_window, 0)
        with source_connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT history_id
                FROM {history_table}
                WHERE history_id > %s
                  AND history_id <= %s
                ORDER BY history_id
                """,
                (replay_start, last_success_history_id),
            )
            replay_ids = [int(row[0]) for row in cursor.fetchall()]

    with source_connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT history_id
            FROM {history_table}
            WHERE history_id > %s
            ORDER BY history_id
            LIMIT %s
            """,
            (last_success_history_id, batch_size),
        )
        new_ids = [int(row[0]) for row in cursor.fetchall()]

    candidate_ids = sorted(set(replay_ids + new_ids))
    return candidate_ids, new_ids


def fetch_candidate_history_ids_sqlserver(
    source_connection,
    source_config: SourceDbConfig,
    last_success_history_id: int,
    replay_history_window: int,
    batch_size: int,
) -> Tuple[List[int], List[int]]:
    history_table = build_source_table_name(source_config, "history")
    replay_ids: List[int] = []
    if last_success_history_id > 0 and replay_history_window > 0:
        replay_start = max(last_success_history_id - replay_history_window, 0)
        cursor = source_connection.cursor()
        cursor.execute(
            f"""
            SELECT history_id
            FROM {history_table}
            WHERE history_id > {int(replay_start)}
              AND history_id <= {int(last_success_history_id)}
            ORDER BY history_id
            """
        )
        replay_ids = [int(row[0]) for row in cursor.fetchall()]

    cursor = source_connection.cursor()
    cursor.execute(
        f"""
        SELECT history_id
        FROM {history_table}
        WHERE history_id > {int(last_success_history_id)}
        ORDER BY history_id
        OFFSET 0 ROWS FETCH NEXT {int(batch_size)} ROWS ONLY
        """
    )
    new_ids = [int(row[0]) for row in cursor.fetchall()]
    candidate_ids = sorted(set(replay_ids + new_ids))
    return candidate_ids, new_ids


def fetch_candidate_history_ids(
    source_connection,
    source_config: SourceDbConfig,
    last_success_history_id: int,
    replay_history_window: int,
    batch_size: int,
) -> Tuple[List[int], List[int]]:
    if source_config.db_type == "postgres":
        return fetch_candidate_history_ids_postgres(
            source_connection,
            source_config,
            last_success_history_id,
            replay_history_window,
            batch_size,
        )
    if source_config.db_type == "sqlserver":
        return fetch_candidate_history_ids_sqlserver(
            source_connection,
            source_config,
            last_success_history_id,
            replay_history_window,
            batch_size,
        )
    raise ValueError(f"不支持的源库类型: {source_config.db_type}")


def build_postgres_aggregate_sql(
    source_config: SourceDbConfig,
    candidate_ids: Sequence[int],
) -> Tuple[str, List[Any]]:
    history_table = build_source_table_name(source_config, "history")
    detail_table = build_source_table_name(source_config, "history_detail")
    placeholders = ", ".join(["%s"] * len(candidate_ids))
    sql = f"""
    SELECT
        h.history_id,
        h.model,
        h.serial_number,
        h.date_time,
        h.color_code,
        h.tunnel,
        h."CYCLE" AS cycle,
        SUM(CASE WHEN hd.station = 1 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_1_defect_count,
        SUM(CASE WHEN hd.station = 2 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_2_defect_count,
        SUM(CASE WHEN hd.station = 3 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_3_defect_count,
        SUM(CASE WHEN hd.station = 4 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_4_defect_count,
        SUM(CASE WHEN hd.station = 5 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_5_defect_count,
        SUM(CASE WHEN hd.station BETWEEN 1 AND 5 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS total_defect_count
    FROM {history_table} AS h
    LEFT JOIN {detail_table} AS hd
        ON hd.history_id = h.history_id
    WHERE h.history_id IN ({placeholders})
    GROUP BY
        h.history_id,
        h.model,
        h.serial_number,
        h.date_time,
        h.color_code,
        h.tunnel,
        h."CYCLE"
    ORDER BY h.history_id
    """
    return sql, list(candidate_ids)


def build_sqlserver_aggregate_sql(
    source_config: SourceDbConfig,
    candidate_ids: Sequence[int],
) -> str:
    history_table = build_source_table_name(source_config, "history")
    detail_table = build_source_table_name(source_config, "history_detail")
    id_list = ", ".join([str(int(candidate_id)) for candidate_id in candidate_ids])
    sql = f"""
    SELECT
        h.history_id,
        h.model,
        h.serial_number,
        h.date_time,
        h.color_code,
        h.tunnel,
        h.[CYCLE] AS cycle,
        SUM(CASE WHEN hd.station = 1 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_1_defect_count,
        SUM(CASE WHEN hd.station = 2 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_2_defect_count,
        SUM(CASE WHEN hd.station = 3 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_3_defect_count,
        SUM(CASE WHEN hd.station = 4 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_4_defect_count,
        SUM(CASE WHEN hd.station = 5 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS station_5_defect_count,
        SUM(CASE WHEN hd.station BETWEEN 1 AND 5 AND hd.diameter > 0 THEN 1 ELSE 0 END) AS total_defect_count
    FROM {history_table} AS h
    LEFT JOIN {detail_table} AS hd
        ON hd.history_id = h.history_id
    WHERE h.history_id IN ({id_list})
    GROUP BY
        h.history_id,
        h.model,
        h.serial_number,
        h.date_time,
        h.color_code,
        h.tunnel,
        h.[CYCLE]
    ORDER BY h.history_id
    """
    return sql


def fetch_aggregated_rows(
    source_connection,
    source_config: SourceDbConfig,
    candidate_ids: Sequence[int],
) -> List[Dict[str, Any]]:
    if not candidate_ids:
        return []

    if source_config.db_type == "postgres":
        sql, params = build_postgres_aggregate_sql(source_config, candidate_ids)
        with source_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    if source_config.db_type == "sqlserver":
        sql = build_sqlserver_aggregate_sql(source_config, candidate_ids)
        cursor = source_connection.cursor()
        cursor.execute(sql)
        return fetchall_dicts(cursor)

    raise ValueError(f"不支持的源库类型: {source_config.db_type}")


def build_upsert_rows(
    aggregated_rows: Iterable[Dict[str, Any]],
    model_map: Dict[int, Dict[str, Optional[str]]],
) -> List[Tuple[Any, ...]]:
    upsert_rows: List[Tuple[Any, ...]] = []
    for row in aggregated_rows:
        model = int(row["model"])
        model_info = model_map.get(model, {})
        upsert_rows.append(
            (
                int(row["history_id"]),
                model,
                model_info.get("type_name"),
                model_info.get("black_roof"),
                row["serial_number"],
                row["date_time"],
                row["color_code"],
                row["tunnel"],
                row["cycle"],
                int(row["station_1_defect_count"] or 0),
                int(row["station_2_defect_count"] or 0),
                int(row["station_3_defect_count"] or 0),
                int(row["station_4_defect_count"] or 0),
                int(row["station_5_defect_count"] or 0),
                int(row["total_defect_count"] or 0),
            )
        )
    return upsert_rows


def upsert_summary_rows(connection, upsert_rows: Sequence[Tuple[Any, ...]]) -> int:
    if not upsert_rows:
        return 0

    with connection.cursor() as cursor:
        execute_values(cursor, UPSERT_SUMMARY_SQL, list(upsert_rows), page_size=1000)
    return len(upsert_rows)


def process_refresh_batch(
    target_connection,
    source_connection,
    settings: RuntimeSettings,
    state: RefreshState,
    model_map: Dict[int, Dict[str, Optional[str]]],
    candidate_ids: Sequence[int],
    new_ids: Sequence[int],
) -> BatchResult:
    started_at = utc_now()
    watermark_before = state.last_success_history_id
    replay_count = max(len(candidate_ids) - len(new_ids), 0)
    batch_type = "new_and_replay" if new_ids else "replay_only"
    batch_min_history_id = min(candidate_ids) if candidate_ids else None
    batch_max_history_id = max(candidate_ids) if candidate_ids else None
    aggregated_rows = fetch_aggregated_rows(source_connection, settings.source_db, candidate_ids)
    upsert_rows = build_upsert_rows(aggregated_rows, model_map)
    upserted_count = len(upsert_rows)
    new_watermark = max(watermark_before, max(new_ids) if new_ids else watermark_before)
    new_watermark_date_time = state.last_success_date_time
    if new_ids:
        date_time_by_history_id = {
            int(row["history_id"]): row["date_time"] for row in aggregated_rows
        }
        new_watermark_date_time = date_time_by_history_id.get(new_watermark, state.last_success_date_time)

    message = (
        f"batch_type={batch_type}, "
        f"source_type={settings.source_db.db_type}, "
        f"candidate_count={len(candidate_ids)}, "
        f"replay_history_count={replay_count}, "
        f"upserted_count={upserted_count}, "
        f"new_history_count={len(new_ids)}"
    )

    try:
        upsert_summary_rows(target_connection, upsert_rows)
        finished_at = utc_now()
        update_refresh_state(
            target_connection,
            last_success_history_id=new_watermark,
            last_success_date_time=new_watermark_date_time,
            last_run_started_at=started_at,
            last_run_finished_at=finished_at,
            last_status="success",
            last_message=message,
        )
        insert_refresh_log(
            target_connection,
            settings,
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            candidate_count=len(candidate_ids),
            upserted_count=upserted_count,
            batch_min_history_id=batch_min_history_id,
            batch_max_history_id=batch_max_history_id,
            watermark_before=watermark_before,
            watermark_after=new_watermark,
            message=message,
        )
        target_connection.commit()
    except Exception as exc:
        target_connection.rollback()
        finished_at = utc_now()
        failure_message = f"{message}; error={exc}"
        update_refresh_state(
            target_connection,
            last_success_history_id=state.last_success_history_id,
            last_success_date_time=state.last_success_date_time,
            last_run_started_at=started_at,
            last_run_finished_at=finished_at,
            last_status="failed",
            last_message=failure_message,
        )
        insert_refresh_log(
            target_connection,
            settings,
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            candidate_count=len(candidate_ids),
            upserted_count=0,
            batch_min_history_id=batch_min_history_id,
            batch_max_history_id=batch_max_history_id,
            watermark_before=watermark_before,
            watermark_after=watermark_before,
            message=failure_message,
        )
        target_connection.commit()
        raise

    logger.info(
        "批次刷新完成 [%s]: source_type=%s, candidate=%s, replay=%s, new=%s, upserted=%s, watermark %s -> %s",
        batch_type,
        settings.source_db.db_type,
        len(candidate_ids),
        replay_count,
        len(new_ids),
        upserted_count,
        watermark_before,
        new_watermark,
    )
    refreshed_state = fetch_state(target_connection) or state
    return BatchResult(
        state=refreshed_state,
        batch_type=batch_type,
        candidate_count=len(candidate_ids),
        replay_count=replay_count,
        new_count=len(new_ids),
        upserted_count=upserted_count,
        watermark_before=watermark_before,
        watermark_after=new_watermark,
    )


def run_refresh(target_connection, source_connection, settings: RuntimeSettings) -> None:
    ensure_target_schema(target_connection)
    state = initialize_state(target_connection, settings)

    lock_acquired = acquire_advisory_lock(target_connection, settings.lock_key)
    if not lock_acquired:
        record_non_batch_result(
            target_connection,
            settings,
            state,
            status="skipped",
            message=f"lock busy: {settings.lock_key}",
        )
        logger.warning("未获取到 advisory lock，跳过本次刷新: %s", settings.lock_key)
        return

    try:
        model_map = load_local_model_map(target_connection)
        total_batches = 0
        total_upserted = 0
        total_candidates = 0
        total_new_history = 0
        total_replay_history = 0
        final_watermark = state.last_success_history_id
        while True:
            current_state = fetch_state(target_connection) or state
            candidate_ids, new_ids = fetch_candidate_history_ids(
                source_connection,
                settings.source_db,
                current_state.last_success_history_id,
                settings.replay_history_window,
                settings.batch_size,
            )
            if not candidate_ids:
                record_non_batch_result(
                    target_connection,
                    settings,
                    current_state,
                    status="noop",
                    message="source history table has no candidate rows",
                )
                logger.info("无可处理数据，结束本次刷新。")
                break

            batch_result = process_refresh_batch(
                target_connection,
                source_connection,
                settings,
                current_state,
                model_map,
                candidate_ids,
                new_ids,
            )
            state = batch_result.state
            total_batches += 1
            total_upserted += batch_result.upserted_count
            total_candidates += batch_result.candidate_count
            total_new_history += batch_result.new_count
            total_replay_history += batch_result.replay_count
            final_watermark = batch_result.watermark_after

            if not new_ids:
                logger.info("本次进入 replay_only 收尾批次，无新增 history_id，结束刷新。")
                break
        logger.info(
            "本次刷新汇总: source_type=%s, total_batches=%s, total_candidates=%s, total_replay=%s, total_new=%s, total_upserted=%s, final_watermark=%s",
            settings.source_db.db_type,
            total_batches,
            total_candidates,
            total_replay_history,
            total_new_history,
            total_upserted,
            final_watermark,
        )
        cleanup_result = cleanup_summary_retention_window(target_connection, settings, state)
        logger.info(
            "本次窗口裁剪结果: mode=%s, deleted_count=%s, row_count %s->%s",
            cleanup_result.mode,
            cleanup_result.deleted_count,
            cleanup_result.row_count_before,
            cleanup_result.row_count_after,
        )
    finally:
        release_advisory_lock(target_connection, settings.lock_key)


def print_status(target_connection, settings: RuntimeSettings) -> None:
    with target_connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT to_regclass('public.history_station_defect_summary_refresh_state') AS regclass")
        state_table_exists = cursor.fetchone()["regclass"] is not None

    if not state_table_exists:
        print("history_station_defect_summary_refresh_state 尚未创建。请先执行 --init-state。")
        return

    state = fetch_state(target_connection)
    with target_connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS row_count,
                MIN(history_id) AS min_history_id,
                COALESCE(MAX(history_id), 0) AS max_history_id,
                MIN(date_time) AS min_date_time,
                MAX(date_time) AS max_date_time
            FROM public.history_station_defect_summary
            """
        )
        summary_stats = cursor.fetchone()
        cursor.execute(
            """
            SELECT
                id,
                started_at,
                finished_at,
                status,
                candidate_count,
                upserted_count,
                batch_min_history_id,
                batch_max_history_id,
                watermark_before,
                watermark_after,
                message
            FROM public.history_station_defect_summary_refresh_log
            WHERE job_name = %s
            ORDER BY id DESC
            LIMIT 5
            """,
            (JOB_NAME,),
        )
        recent_logs = cursor.fetchall()

    print("=== history_station_defect_summary 刷新状态 ===")
    print(f"job_name: {JOB_NAME}")
    print(f"source_type: {settings.source_db.db_type}")
    print(f"source_host: {settings.source_db.host}")
    print(f"source_database: {settings.source_db.database}")
    print(f"source_schema: {settings.source_db.schema}")
    print(f"retention_mode: {settings.retention_mode}")
    print(f"retention_max_rows: {settings.retention_max_rows}")
    print(f"retention_max_months: {settings.retention_max_months}")
    print(f"retention_delete_batch_size: {settings.retention_delete_batch_size}")
    print(f"summary_row_count: {summary_stats['row_count']}")
    print(f"summary_min_history_id: {summary_stats['min_history_id']}")
    print(f"summary_max_history_id: {summary_stats['max_history_id']}")
    print(f"summary_min_date_time: {summary_stats['min_date_time']}")
    print(f"summary_max_date_time: {summary_stats['max_date_time']}")
    if state is None:
        print("state: 尚未初始化")
    else:
        print(f"last_success_history_id: {state.last_success_history_id}")
        print(f"last_success_date_time: {state.last_success_date_time}")
        print(f"last_status: {state.last_status}")
        print(f"last_message: {state.last_message}")
        print(f"last_run_started_at: {state.last_run_started_at}")
        print(f"last_run_finished_at: {state.last_run_finished_at}")
        print(f"updated_at: {state.updated_at}")

    print("recent_logs:")
    if not recent_logs:
        print("  (empty)")
        return

    for log_row in recent_logs:
        print(
            "  "
            f"id={log_row['id']}, "
            f"status={log_row['status']}, "
            f"candidate_count={log_row['candidate_count']}, "
            f"upserted_count={log_row['upserted_count']}, "
            f"watermark={log_row['watermark_before']}->{log_row['watermark_after']}, "
            f"batch={log_row['batch_min_history_id']}->{log_row['batch_max_history_id']}, "
            f"started_at={log_row['started_at']}, "
            f"finished_at={log_row['finished_at']}, "
            f"message={log_row['message']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="增量刷新 defect_db.history_station_defect_summary"
    )
    parser.add_argument("--init-state", action="store_true", help="初始化目标表、水位表与首个状态")
    parser.add_argument("--refresh", action="store_true", help="执行一次增量刷新")
    parser.add_argument("--print-status", action="store_true", help="打印当前刷新状态")
    args = parser.parse_args()

    selected_count = sum([args.init_state, args.refresh, args.print_status])
    if selected_count != 1:
        parser.error("请从 --init-state / --refresh / --print-status 中选择一个")
    return args


def close_safely(connection) -> None:
    if connection is not None:
        connection.close()


def main() -> int:
    load_project_env()
    setup_logging()

    try:
        settings = build_runtime_settings()
    except Exception as exc:
        logger.error("配置错误: %s", exc)
        return 1

    logger.info(
        "目标库: %s:%s/%s, 源库: %s:%s/%s, source_type=%s, source_schema=%s, retention_mode=%s, retention_max_rows=%s, retention_max_months=%s, retention_delete_batch_size=%s",
        settings.target_db.host,
        settings.target_db.port,
        settings.target_db.database,
        settings.source_db.host,
        settings.source_db.port,
        settings.source_db.database,
        settings.source_db.db_type,
        settings.source_db.schema,
        settings.retention_mode,
        settings.retention_max_rows,
        settings.retention_max_months,
        settings.retention_delete_batch_size,
    )

    args = parse_args()
    target_connection = None
    source_connection = None

    try:
        target_connection = connect_target_db(settings.target_db, settings.timezone_name)

        if args.init_state:
            ensure_target_schema(target_connection)
            initialize_state(target_connection, settings)
            logger.info("初始化完成。")
            return 0

        if args.print_status:
            print_status(target_connection, settings)
            return 0

        source_connection = connect_source_db(settings.source_db, settings.timezone_name)
        run_refresh(target_connection, source_connection, settings)
        logger.info("本次刷新执行结束。")
        return 0
    except Exception as exc:
        logger.exception("执行失败: %s", exc)
        if target_connection is not None:
            target_connection.rollback()
        return 1
    finally:
        close_safely(source_connection)
        close_safely(target_connection)


if __name__ == "__main__":
    raise SystemExit(main())
