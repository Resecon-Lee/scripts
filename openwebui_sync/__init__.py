"""
OpenWebUI Sync - Database-backed analytics for OpenWebUI instances

This package provides efficient data synchronization and analytics for OpenWebUI
instances by maintaining a local database that is incrementally synced.

Modules:
    database: Database schema and connection management
    sync_engine: Full and incremental sync operations
    report_generator: Generate analytics reports from database
    scheduler: Automated sync scheduling
    config: Configuration management
"""

__version__ = "1.0.0"
__author__ = "AI Usage Analytics Team"

from .database import DatabaseManager
from .sync_engine import SyncEngine
from .report_generator import ReportGenerator

__all__ = ['DatabaseManager', 'SyncEngine', 'ReportGenerator']
