"""
OpenWebUI Sync - Command Line Interface

Provides commands for:
- Syncing instances (full or incremental)
- Generating reports from database
- Checking sync status
- Managing the sync schedule

Usage:
    python sync_cli.py sync <instance>          # Sync specific instance
    python sync_cli.py sync --all               # Sync all instances
    python sync_cli.py sync --all --full        # Force full sync
    python sync_cli.py report <instance>        # Generate report
    python sync_cli.py report --all             # Generate all reports
    python sync_cli.py status                   # Show sync status
    python sync_cli.py schedule start           # Start sync scheduler
"""

import sys
import argparse
from datetime import datetime
from openwebui_sync import DatabaseManager, SyncEngine
from openwebui_sync.config import INSTANCES


def sync_command(args):
    """Execute sync command."""
    engine = SyncEngine()

    if args.all:
        print("\n" + "="*70)
        print(f"{'SYNCING ALL INSTANCES':^70}")
        print("="*70 + "\n")
        engine.sync_all_instances(force_full=args.full)
    else:
        if args.instance not in INSTANCES:
            print(f"[ERROR] Unknown instance: {args.instance}")
            print(f"Available instances: {', '.join(INSTANCES.keys())}")
            return 1

        engine.sync_instance(args.instance, force_full=args.full)

    return 0


def report_command(args):
    """Execute report command."""
    print("[INFO] DB-based report generation coming soon!")
    print("[INFO] For now, use the existing ai_usage_analyzer.py")
    print("[INFO] Once synced, reports will be generated instantly from the database.")
    return 0


def status_command(args):
    """Show sync status."""
    db = DatabaseManager()

    print("\n" + "="*70)
    print(f"{'SYNC STATUS':^70}")
    print("="*70 + "\n")

    with db.get_connection() as conn:
        # Get last sync for each instance
        for instance_name in INSTANCES.keys():
            cursor = conn.execute("""
                SELECT
                    last_sync_at,
                    (SELECT COUNT(*) FROM users WHERE instance_id = i.id AND is_deleted = 0) as user_count,
                    (SELECT COUNT(*) FROM chats WHERE instance_id = i.id AND is_deleted = 0) as chat_count,
                    (SELECT COUNT(*) FROM messages WHERE instance_id = i.id) as message_count
                FROM instances i
                WHERE name = ?
            """, (instance_name,))

            row = cursor.fetchone()

            if row and row['last_sync_at']:
                last_sync = datetime.fromisoformat(row['last_sync_at'])
                print(f"{instance_name.upper()}:")
                print(f"  Last Sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Users: {row['user_count']:,}")
                print(f"  Chats: {row['chat_count']:,}")
                print(f"  Messages: {row['message_count']:,}")
            else:
                print(f"{instance_name.upper()}: Never synced")
            print()

        # Show recent sync runs
        print("Recent Sync Runs:")
        print("-" * 70)

        cursor = conn.execute("""
            SELECT instance_name, sync_type, started_at, completed_at, status,
                   users_synced, chats_synced, messages_synced
            FROM sync_runs
            ORDER BY started_at DESC
            LIMIT 10
        """)

        for row in cursor.fetchall():
            status_icon = "[OK]" if row['status'] == 'success' else "[FAIL]"
            started = datetime.fromisoformat(row['started_at'])
            completed = datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None

            duration = ""
            if completed:
                delta = completed - started
                duration = f"({delta.total_seconds():.1f}s)"

            print(f"{status_icon} {row['instance_name']:<15} {row['sync_type']:<12} "
                  f"{started.strftime('%Y-%m-%d %H:%M')} {duration:<10} "
                  f"U:{row['users_synced']} C:{row['chats_synced']} M:{row['messages_synced']}")

    print()
    return 0


def schedule_command(args):
    """Manage sync scheduler."""
    if args.action == 'start':
        print("[INFO] Starting scheduler...")
        from openwebui_sync.scheduler import run_scheduler
        run_scheduler()
    elif args.action == 'stop':
        print("[INFO] Scheduler stop not implemented - use Ctrl+C to stop running scheduler")
    elif args.action == 'status':
        print("[INFO] Scheduler status not implemented")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenWebUI Sync - Efficient database-backed analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Synchronize instance data')
    sync_parser.add_argument('instance', nargs='?', help='Instance name (fasgpt, resgpt, berkshiregpt)')
    sync_parser.add_argument('--all', action='store_true', help='Sync all instances')
    sync_parser.add_argument('--full', action='store_true', help='Force full sync')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate analytics report')
    report_parser.add_argument('instance', nargs='?', help='Instance name or --all')
    report_parser.add_argument('--all', action='store_true', help='Generate all reports')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show sync status')

    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Manage sync scheduler')
    schedule_parser.add_argument('action', choices=['start', 'stop', 'status'], help='Scheduler action')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'sync':
        return sync_command(args)
    elif args.command == 'report':
        return report_command(args)
    elif args.command == 'status':
        return status_command(args)
    elif args.command == 'schedule':
        return schedule_command(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
