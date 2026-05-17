# Main Scheduler for Analytics DB Refresh Pipelines
# Created: 2026-05-17 21:08 Asia/Shanghai

import os
import sys
import time
import subprocess
import schedule
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Calculate absolute paths to ensure robustness from any working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Load env in case it's run locally
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# Global lock and configs
IS_RUNNING = False
HEALTHCHECK_FILE = "/tmp/scheduler_health"
SCHEDULER_INTERVAL_MINUTES = int(os.environ.get("SCHEDULER_INTERVAL_MINUTES", "3"))

def run_carbody_etl():
    logger.info("Starting Carbody ETL...")
    carbody_script = os.path.join(PROJECT_ROOT, "carbody_etl", "refresh_carbody_ods.py")
    result = subprocess.run(
        [sys.executable, carbody_script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        logger.error(f"Carbody ETL failed with exit code {result.returncode}:\n{result.stderr}")
        raise RuntimeError(f"Carbody ETL failed: {result.stderr}")
    logger.info("Carbody ETL completed successfully.")

def run_defect_summary_etl():
    logger.info("Starting Defect Summary ETL...")
    defect_script = os.path.join(PROJECT_ROOT, "defect_summary_etl", "refresh_history_station_defect_summary.py")
    result = subprocess.run(
        [sys.executable, defect_script, "--refresh"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        logger.error(f"Defect Summary ETL failed with exit code {result.returncode}:\n{result.stderr}")
        raise RuntimeError(f"Defect Summary ETL failed: {result.stderr}")
    logger.info("Defect Summary ETL completed successfully.")

def run_analytics_all():
    logger.info("Starting Analytics Refresh (CALL meta.refresh_analytics_all())...")
    conn = None
    try:
        # Connect using target database parameters
        conn = psycopg2.connect(
            host=os.environ.get("CARBODY_TARGET_DB_HOST", os.environ.get("DB_HOST", "postgres")),
            port=os.environ.get("CARBODY_TARGET_DB_PORT", os.environ.get("DB_PORT", "5432")),
            dbname=os.environ.get("CARBODY_TARGET_DB_NAME", "analytics_db"),
            user=os.environ.get("CARBODY_TARGET_DB_USER", os.environ.get("DB_USER", "root")),
            password=os.environ.get("CARBODY_TARGET_DB_PASSWORD", os.environ.get("DB_PASSWORD", "root"))
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CALL meta.refresh_analytics_all();")
        logger.info("Analytics Refresh (meta.refresh_analytics_all) completed successfully.")
    except Exception as e:
        logger.error(f"Failed to execute refresh_analytics_all: {e}")
        raise
    finally:
        if conn:
            conn.close()

def job_pipeline():
    global IS_RUNNING
    if IS_RUNNING:
        logger.warning("Previous job pipeline is still running, skipping this iteration.")
        return

    IS_RUNNING = True
    try:
        logger.info(f"--- Starting {SCHEDULER_INTERVAL_MINUTES}-minute ETL Pipeline ---")
        run_carbody_etl()
        run_defect_summary_etl()
        run_analytics_all()
        logger.info("--- ETL Pipeline finished successfully ---")
        
        # Touch healthcheck file with current timestamp
        try:
            with open(HEALTHCHECK_FILE, 'w') as f:
                f.write(str(time.time()))
        except Exception as he:
            logger.error(f"Failed to write healthcheck file: {he}")
            
    except Exception as e:
        logger.error(f"Pipeline execution encountered error: {e}")
    finally:
        IS_RUNNING = False

def main():
    logger.info("Initializing unified scheduler...")
    
    # Touch healthcheck file initially on startup
    try:
        with open(HEALTHCHECK_FILE, 'w') as f:
            f.write(str(time.time()))
    except Exception as he:
        logger.error(f"Failed to initialize healthcheck file: {he}")
        
    schedule.every(SCHEDULER_INTERVAL_MINUTES).minutes.do(job_pipeline)
    logger.info("Scheduler configured. Starting first pipeline run immediately...")
    
    # Run once immediately on startup
    job_pipeline()
    
    logger.info("Scheduler main loop active. Checking schedule every 10 seconds.")
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()
