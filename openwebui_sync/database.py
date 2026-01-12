"""
Database module for OpenWebUI Sync

Handles:
- Database schema creation
- Connection management
- CRUD operations for all entities
- Efficient querying for reports
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from .config import DB_PATH


class DatabaseManager:
    """
    Manages database operations for OpenWebUI sync data.

    Provides methods for:
    - Database initialization and schema creation
    - Connection management with context managers
    - CRUD operations for all entities
    - Efficient batch inserts and updates
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Uses config default if not specified.
        """
        self.db_path = db_path or str(DB_PATH)
        self._ensure_database()

    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        with self.get_connection() as conn:
            self._create_tables(conn)

    @contextmanager
    def get_connection(self):
        """
        Get database connection with context manager.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM users")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _create_tables(self, conn: sqlite3.Connection):
        """
        Create all database tables with proper schema.

        Args:
            conn: Database connection
        """
        cursor = conn.cursor()

        # Sync runs tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_name VARCHAR(50) NOT NULL,
                sync_type VARCHAR(20) NOT NULL,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                users_synced INTEGER DEFAULT 0,
                chats_synced INTEGER DEFAULT 0,
                messages_synced INTEGER DEFAULT 0,
                status VARCHAR(20) NOT NULL,
                error_message TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_runs_instance ON sync_runs(instance_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_runs_started ON sync_runs(started_at)")

        # Instances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                url VARCHAR(255) NOT NULL,
                api_key TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_sync_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                name VARCHAR(255),
                email VARCHAR(255),
                role VARCHAR(50),
                profile_image_url TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                sync_datetime DATETIME NOT NULL,
                is_deleted BOOLEAN DEFAULT 0,
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (instance_id) REFERENCES instances(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_instance ON users(instance_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(is_deleted)")

        # Chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                title TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                sync_datetime DATETIME NOT NULL,
                is_deleted BOOLEAN DEFAULT 0,
                archived BOOLEAN DEFAULT 0,
                pinned BOOLEAN DEFAULT 0,
                folder_id VARCHAR(36),
                share_id VARCHAR(36),
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (instance_id) REFERENCES instances(id),
                FOREIGN KEY (user_id, instance_id) REFERENCES users(id, instance_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id, instance_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_updated ON chats(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_instance ON chats(instance_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_deleted ON chats(is_deleted)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_sync ON chats(sync_datetime)")

        # Chat models (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_models (
                chat_id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                model_id VARCHAR(255) NOT NULL,
                sync_datetime DATETIME NOT NULL,
                PRIMARY KEY (chat_id, instance_id, model_id),
                FOREIGN KEY (chat_id, instance_id) REFERENCES chats(id, instance_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_models_model ON chat_models(model_id)")

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(36) NOT NULL,
                chat_id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                parent_id VARCHAR(36),
                role VARCHAR(20) NOT NULL,
                content TEXT,
                content_length INTEGER,
                created_at DATETIME,
                sync_datetime DATETIME NOT NULL,
                has_files BOOLEAN DEFAULT 0,
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (chat_id, instance_id) REFERENCES chats(id, instance_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, instance_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)")

        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id VARCHAR(255) NOT NULL,
                instance_id INTEGER NOT NULL,
                name VARCHAR(255),
                info JSON,
                sync_datetime DATETIME NOT NULL,
                is_deleted BOOLEAN DEFAULT 0,
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (instance_id) REFERENCES instances(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_instance ON models(instance_id)")

        # Knowledge bases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                name VARCHAR(255),
                description TEXT,
                data JSON,
                created_at DATETIME,
                updated_at DATETIME,
                sync_datetime DATETIME NOT NULL,
                is_deleted BOOLEAN DEFAULT 0,
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (instance_id) REFERENCES instances(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_instance ON knowledge_bases(instance_id)")

        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id VARCHAR(36) NOT NULL,
                message_id VARCHAR(36) NOT NULL,
                instance_id INTEGER NOT NULL,
                filename VARCHAR(255),
                file_type VARCHAR(50),
                size_bytes INTEGER,
                hash VARCHAR(64),
                sync_datetime DATETIME NOT NULL,
                PRIMARY KEY (id, instance_id),
                FOREIGN KEY (message_id, instance_id) REFERENCES messages(id, instance_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_message ON files(message_id, instance_id)")

        conn.commit()

    # ========================================================================
    # INSTANCE OPERATIONS
    # ========================================================================

    def upsert_instance(self, name: str, url: str, api_key: str, is_active: bool = True) -> int:
        """
        Insert or update an instance.

        Args:
            name: Instance name (e.g., 'fasgpt')
            url: Base URL for API
            api_key: Authentication token
            is_active: Whether instance is active

        Returns:
            int: Instance ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO instances (name, url, api_key, is_active)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    url=excluded.url,
                    api_key=excluded.api_key,
                    is_active=excluded.is_active
                RETURNING id
            """, (name, url, api_key, is_active))
            return cursor.fetchone()[0]

    def get_instance_id(self, name: str) -> Optional[int]:
        """
        Get instance ID by name.

        Args:
            name: Instance name

        Returns:
            int or None: Instance ID if found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM instances WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def update_instance_last_sync(self, instance_id: int, sync_time: datetime):
        """
        Update last sync timestamp for an instance.

        Args:
            instance_id: Instance ID
            sync_time: Sync completion time
        """
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE instances SET last_sync_at = ? WHERE id = ?",
                (sync_time, instance_id)
            )

    def get_last_sync_time(self, instance_id: int) -> Optional[datetime]:
        """
        Get last successful sync time for an instance.

        Args:
            instance_id: Instance ID

        Returns:
            datetime or None: Last sync time if available
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_sync_at FROM instances WHERE id = ?",
                (instance_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None

    # ========================================================================
    # SYNC RUN OPERATIONS
    # ========================================================================

    def start_sync_run(self, instance_name: str, sync_type: str) -> int:
        """
        Create a new sync run record.

        Args:
            instance_name: Name of instance being synced
            sync_type: 'full' or 'incremental'

        Returns:
            int: Sync run ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO sync_runs (instance_name, sync_type, started_at, status)
                VALUES (?, ?, ?, 'in_progress')
                RETURNING id
            """, (instance_name, sync_type, datetime.now()))
            return cursor.fetchone()[0]

    def complete_sync_run(self, sync_run_id: int, users_synced: int = 0,
                          chats_synced: int = 0, messages_synced: int = 0):
        """
        Mark sync run as completed successfully.

        Args:
            sync_run_id: Sync run ID
            users_synced: Number of users synced
            chats_synced: Number of chats synced
            messages_synced: Number of messages synced
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE sync_runs
                SET status = 'success',
                    completed_at = ?,
                    users_synced = ?,
                    chats_synced = ?,
                    messages_synced = ?
                WHERE id = ?
            """, (datetime.now(), users_synced, chats_synced, messages_synced, sync_run_id))

    def fail_sync_run(self, sync_run_id: int, error_message: str):
        """
        Mark sync run as failed.

        Args:
            sync_run_id: Sync run ID
            error_message: Error description
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE sync_runs
                SET status = 'failed',
                    completed_at = ?,
                    error_message = ?
                WHERE id = ?
            """, (datetime.now(), error_message, sync_run_id))

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def upsert_user(self, user_data: Dict[str, Any], instance_id: int, sync_time: datetime):
        """
        Insert or update a user.

        Args:
            user_data: User data from API
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (
                    id, instance_id, name, email, role, profile_image_url,
                    created_at, updated_at, sync_datetime, is_deleted
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    role=excluded.role,
                    profile_image_url=excluded.profile_image_url,
                    updated_at=excluded.updated_at,
                    sync_datetime=excluded.sync_datetime,
                    is_deleted=0
            """, (
                user_data['id'],
                instance_id,
                user_data.get('name'),
                user_data.get('email'),
                user_data.get('role'),
                user_data.get('profile_image_url'),
                user_data.get('created_at'),
                user_data.get('updated_at'),
                sync_time
            ))

    def get_user_ids_for_instance(self, instance_id: int) -> set:
        """
        Get all user IDs for an instance.

        Args:
            instance_id: Instance ID

        Returns:
            set: Set of user IDs
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE instance_id = ? AND is_deleted = 0",
                (instance_id,)
            )
            return {row[0] for row in cursor.fetchall()}

    def mark_users_deleted(self, user_ids: List[str], instance_id: int):
        """
        Mark users as deleted.

        Args:
            user_ids: List of user IDs to mark deleted
            instance_id: Instance ID
        """
        if not user_ids:
            return

        with self.get_connection() as conn:
            placeholders = ','.join('?' * len(user_ids))
            conn.execute(f"""
                UPDATE users
                SET is_deleted = 1
                WHERE id IN ({placeholders}) AND instance_id = ?
            """, (*user_ids, instance_id))

    # ========================================================================
    # CHAT OPERATIONS
    # ========================================================================

    def upsert_chat(self, chat_data: Dict[str, Any], instance_id: int,
                    user_id: str, sync_time: datetime):
        """
        Insert or update a chat.

        Args:
            chat_data: Chat data from API
            instance_id: Instance ID
            user_id: User ID who owns the chat
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            # Convert timestamp to datetime if needed
            created_at = chat_data.get('created_at')
            updated_at = chat_data.get('updated_at')

            if isinstance(created_at, (int, float)):
                created_at = datetime.fromtimestamp(created_at)
            if isinstance(updated_at, (int, float)):
                updated_at = datetime.fromtimestamp(updated_at)

            conn.execute("""
                INSERT INTO chats (
                    id, instance_id, user_id, title, created_at, updated_at,
                    sync_datetime, archived, pinned, folder_id, share_id, is_deleted
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    title=excluded.title,
                    updated_at=excluded.updated_at,
                    sync_datetime=excluded.sync_datetime,
                    archived=excluded.archived,
                    pinned=excluded.pinned,
                    folder_id=excluded.folder_id,
                    share_id=excluded.share_id,
                    is_deleted=0
            """, (
                chat_data['id'],
                instance_id,
                user_id,
                chat_data.get('title'),
                created_at,
                updated_at,
                sync_time,
                chat_data.get('archived', False),
                chat_data.get('pinned', False),
                chat_data.get('folder_id'),
                chat_data.get('share_id')
            ))

    def get_chat(self, chat_id: str, instance_id: int) -> Optional[Dict]:
        """
        Get chat by ID.

        Args:
            chat_id: Chat ID
            instance_id: Instance ID

        Returns:
            dict or None: Chat data if found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM chats WHERE id = ? AND instance_id = ?",
                (chat_id, instance_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def touch_chat(self, chat_id: str, instance_id: int, sync_time: datetime):
        """
        Update chat sync_datetime to mark it as still existing.

        Args:
            chat_id: Chat ID
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE chats SET sync_datetime = ? WHERE id = ? AND instance_id = ?",
                (sync_time, chat_id, instance_id)
            )

    def mark_stale_chats_deleted(self, instance_id: int, cutoff_time: datetime):
        """
        Mark chats that haven't been synced since cutoff time as deleted.

        Args:
            instance_id: Instance ID
            cutoff_time: Chats not synced since this time are marked deleted
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE chats
                SET is_deleted = 1
                WHERE instance_id = ? AND sync_datetime < ? AND is_deleted = 0
            """, (instance_id, cutoff_time))

    # ========================================================================
    # CHAT MODELS OPERATIONS
    # ========================================================================

    def upsert_chat_model(self, chat_id: str, instance_id: int,
                          model_id: str, sync_time: datetime):
        """
        Insert or update a chat-model association.

        Args:
            chat_id: Chat ID
            instance_id: Instance ID
            model_id: Model ID
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO chat_models (chat_id, instance_id, model_id, sync_datetime)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chat_id, instance_id, model_id) DO UPDATE SET
                    sync_datetime=excluded.sync_datetime
            """, (chat_id, instance_id, model_id, sync_time))

    def delete_chat_models(self, chat_id: str, instance_id: int):
        """
        Delete all model associations for a chat.

        Args:
            chat_id: Chat ID
            instance_id: Instance ID
        """
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM chat_models WHERE chat_id = ? AND instance_id = ?",
                (chat_id, instance_id)
            )

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    def upsert_message(self, message_data: Dict[str, Any], chat_id: str,
                       instance_id: int, sync_time: datetime):
        """
        Insert or update a message.

        Args:
            message_data: Message data from API
            chat_id: Chat ID this message belongs to
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        content = message_data.get('content', '')
        content_length = len(content) if content else 0
        has_files = len(message_data.get('files', [])) > 0

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO messages (
                    id, chat_id, instance_id, parent_id, role, content,
                    content_length, created_at, sync_datetime, has_files
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    content=excluded.content,
                    content_length=excluded.content_length,
                    sync_datetime=excluded.sync_datetime,
                    has_files=excluded.has_files
            """, (
                message_data['id'],
                chat_id,
                instance_id,
                message_data.get('parentId'),
                message_data.get('role'),
                content,
                content_length,
                message_data.get('created_at'),
                sync_time,
                has_files
            ))

    def delete_messages_for_chat(self, chat_id: str, instance_id: int):
        """
        Delete all messages for a chat.

        Args:
            chat_id: Chat ID
            instance_id: Instance ID
        """
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM messages WHERE chat_id = ? AND instance_id = ?",
                (chat_id, instance_id)
            )

    # ========================================================================
    # MODEL OPERATIONS
    # ========================================================================

    def upsert_model(self, model_data: Dict[str, Any], instance_id: int, sync_time: datetime):
        """
        Insert or update a model.

        Args:
            model_data: Model data from API
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO models (id, instance_id, name, info, sync_datetime, is_deleted)
                VALUES (?, ?, ?, ?, ?, 0)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    name=excluded.name,
                    info=excluded.info,
                    sync_datetime=excluded.sync_datetime,
                    is_deleted=0
            """, (
                model_data['id'],
                instance_id,
                model_data.get('name', model_data['id']),
                json.dumps(model_data),
                sync_time
            ))

    # ========================================================================
    # KNOWLEDGE BASE OPERATIONS
    # ========================================================================

    def upsert_knowledge_base(self, kb_data: Dict[str, Any], instance_id: int, sync_time: datetime):
        """
        Insert or update a knowledge base.

        Args:
            kb_data: Knowledge base data from API
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO knowledge_bases (
                    id, instance_id, name, description, data, created_at,
                    updated_at, sync_datetime, is_deleted
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    data=excluded.data,
                    updated_at=excluded.updated_at,
                    sync_datetime=excluded.sync_datetime,
                    is_deleted=0
            """, (
                kb_data['id'],
                instance_id,
                kb_data.get('name'),
                kb_data.get('description'),
                json.dumps(kb_data),
                kb_data.get('created_at'),
                kb_data.get('updated_at'),
                sync_time
            ))

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    def upsert_file(self, file_data: Dict[str, Any], message_id: str,
                    instance_id: int, sync_time: datetime):
        """
        Insert or update a file attachment.

        Args:
            file_data: File data from API
            message_id: Message ID this file is attached to
            instance_id: Instance ID
            sync_time: Current sync timestamp
        """
        file_info = file_data.get('file', {})

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO files (
                    id, message_id, instance_id, filename, file_type,
                    size_bytes, hash, sync_datetime
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id, instance_id) DO UPDATE SET
                    filename=excluded.filename,
                    file_type=excluded.file_type,
                    sync_datetime=excluded.sync_datetime
            """, (
                file_info.get('id'),
                message_id,
                instance_id,
                file_info.get('filename'),
                file_data.get('type'),
                file_info.get('size'),
                file_info.get('hash'),
                sync_time
            ))
