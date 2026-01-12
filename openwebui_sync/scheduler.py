"""
Automated Sync Scheduler

Runs periodic syncs of OpenWebUI instances on a schedule.

Default schedule:
- Incremental sync every hour
- Can be customized in this file

Usage:
    python sync_cli.py schedule start
"""

import schedule
import time
from datetime import datetime
from .sync_engine import SyncEngine


def sync_job():
    """
    Scheduled sync job - runs incremental sync for all instances.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled sync...")

    engine = SyncEngine()

    try:
        engine.sync_all_instances(force_full=False)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled sync completed successfully\n")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled sync failed: {e}\n")


def run_scheduler():
    """
    Run the sync scheduler.

    Schedules:
    - Incremental sync every hour on the hour
    """
    print("="*70)
    print(f"{'SYNC SCHEDULER STARTED':^70}")
    print("="*70)
    print(f"\nSchedule: Incremental sync every hour")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")

    # Schedule sync every hour
    schedule.every().hour.do(sync_job)

    # Alternative schedules (comment/uncomment as needed):
    # schedule.every(30).minutes.do(sync_job)  # Every 30 minutes
    # schedule.every().day.at("02:00").do(sync_job)  # Daily at 2 AM
    # schedule.every().day.at("08:00").do(sync_job)  # Daily at 8 AM
    # schedule.every().monday.at("09:00").do(sync_job)  # Weekly on Monday

    # Run first sync immediately
    sync_job()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print(f"{'SCHEDULER STOPPED':^70}")
        print("="*70 + "\n")
