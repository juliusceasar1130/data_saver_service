# Analytics DB Refresh Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a unified Docker-based Python scheduler to run the Carbody ETL, defect summary ETL, and `analytics_all` DB refresh tasks sequentially every 3 minutes.

**Architecture:** We will create a `scheduler_main.py` entrypoint that uses the `schedule` library to sequentially trigger three processes every 3 minutes. It handles network failures using try/except, avoids overlapping execution using a global lock `IS_RUNNING`, and periodically updates a healthcheck file. The process runs inside a new Docker container (`refresh-scheduler`) defined via `Dockerfile.scheduler` and orchestrated via `docker-compose.yml`, joining the `app-network` to seamlessly reach the PostgreSQL database and the WSL proxy.

**Tech Stack:** Python 3.10 (slim), `schedule`, `psycopg2-binary`, `subprocess`, Docker, Docker Compose.

---

### Task 1: Add schedule dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Append schedule dependency to requirements.txt**

```bash
echo "schedule==1.2.2" >> requirements.txt
```

### Task 2: Implement the Scheduler Main Script

**Files:**
- Create: `defect_database/scripts/scheduler_main.py`

- [ ] **Step 1: Create the file with basic structure and ETL triggers**

```python
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

# Load env in case it's run locally
load_dotenv()

# Global lock
IS_RUNNING = False
HEALTHCHECK_FILE = "/tmp/scheduler_health"

def run_carbody_etl():
    logger.info("Starting Carbody ETL...")
    result = subprocess.run(
        [sys.executable, "carbody_etl/refresh_carbody_ods.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"Carbody ETL failed:\n{result.stderr}")
        raise RuntimeError("Carbody ETL returned non-zero exit code.")
    logger.info("Carbody ETL completed.")

def run_defect_summary_etl():
    logger.info("Starting Defect Summary ETL...")
    result = subprocess.run(
        [sys.executable, "defect_summary_etl/refresh_history_station_defect_summary.py", "--refresh"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"Defect Summary ETL failed:\n{result.stderr}")
        raise RuntimeError("Defect Summary ETL returned non-zero exit code.")
    logger.info("Defect Summary ETL completed.")
```

- [ ] **Step 2: Add function to run the PostgreSQL stored procedure**

```python
# Append to defect_database/scripts/scheduler_main.py

def run_analytics_all():
    logger.info("Starting Analytics Refresh (CALL meta.refresh_analytics_all())...")
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            dbname=os.environ.get("DB_NAME", "rollerbed_tracking_db"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "")
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CALL meta.refresh_analytics_all();")
        logger.info("Analytics Refresh completed.")
    except Exception as e:
        logger.error(f"Failed to execute refresh_analytics_all: {e}")
        raise
    finally:
        if conn:
            conn.close()
```

- [ ] **Step 3: Implement the job pipeline and main loop**

```python
# Append to defect_database/scripts/scheduler_main.py

def job_pipeline():
    global IS_RUNNING
    if IS_RUNNING:
        logger.warning("Previous job is still running, skipping this iteration.")
        return

    IS_RUNNING = True
    try:
        logger.info("--- Starting 3-minute ETL Pipeline ---")
        run_carbody_etl()
        run_defect_summary_etl()
        run_analytics_all()
        logger.info("--- ETL Pipeline finished successfully ---")
        
        # Touch healthcheck file
        with open(HEALTHCHECK_FILE, 'w') as f:
            f.write(str(time.time()))
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
    finally:
        IS_RUNNING = False

def main():
    logger.info("Initializing unified scheduler...")
    
    # Touch healthcheck initially
    with open(HEALTHCHECK_FILE, 'w') as f:
        f.write(str(time.time()))
        
    schedule.every(3).minutes.do(job_pipeline)
    logger.info("Scheduler started, waiting for first trigger...")
    
    # Run immediately on startup
    job_pipeline()
    
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify syntax**
Run: `python -m py_compile defect_database/scripts/scheduler_main.py`
Expected: No output (successful compilation)

### Task 3: Create Dockerfile for Scheduler

**Files:**
- Create: `Dockerfile.scheduler`

- [ ] **Step 1: Write Dockerfile.scheduler**

```dockerfile
FROM python:3.10-slim

# Set timezone
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files needed for the scripts
COPY . .

# Start the scheduler
CMD ["python", "defect_database/scripts/scheduler_main.py"]
```

### Task 4: Update docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add the refresh-scheduler service at the end of docker-compose.yml**

Append this block exactly to the end of `docker-compose.yml`, ensuring it aligns with the `services:` indentation level (2 spaces indent for `refresh-scheduler`):

```yaml
  refresh-scheduler:
    build: 
      context: .
      dockerfile: Dockerfile.scheduler
    image: refresh-scheduler:v1.0
    container_name: refresh_scheduler_v1.0
    restart: always
    env_file: 
      - .env
    networks:
      - app-network
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "find /tmp/scheduler_health -mmin -5 | grep -q ."]
      interval: 1m
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

- [ ] **Step 2: Validate docker-compose syntax**

Run: `docker-compose config`
Expected: Valid YAML output without errors, showing `refresh-scheduler` along with other services.
