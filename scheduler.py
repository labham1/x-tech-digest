"""Continuous background scheduler for X Tech Digest.

Usage:
    python scheduler.py --time "07:00"

Keeps running in the terminal and triggers main.py every day at the designated time.
"""

import time
import argparse
import logging
import subprocess
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("scheduler")


def run_digest():
    logger.info("⏰ Morning schedule triggered! Starting daily tech digest run...")
    try:
        result = subprocess.run([sys.executable, "main.py"], capture_output=False, text=True)
        logger.info(f"Execution finished with exit code {result.returncode}")
    except Exception as e:
        logger.error(f"Failed to execute main.py: {e}")


def main():
    parser = argparse.ArgumentParser(description="Daily X Tech Digest Scheduler")
    parser.add_argument(
        "--time",
        type=str,
        default="07:00",
        help="24-hour time to trigger every morning (e.g. '07:00', '08:30')"
    )
    args = parser.parse_args()

    target_time = args.time
    logger.info(f"Scheduler active. Will run every morning at {target_time}.")
    logger.info("Press Ctrl+C at any time to stop.")

    last_run_date = None

    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_date_str = now.strftime("%Y-%m-%d")

        if current_time_str == target_time and last_run_date != current_date_str:
            last_run_date = current_date_str
            run_digest()

        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    main()
