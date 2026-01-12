"""
Sync Engine for OpenWebUI data

Handles:
- Full sync (initial data load)
- Incremental sync (detect and sync changes only)
- API communication with OpenWebUI instances
- Progress tracking and error handling
"""

import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from .database import DatabaseManager
from .config import (
    INSTANCES, API_TIMEOUT, API_DELAY, MAX_RETRIES
)


class SyncEngine:
    """
    Synchronization engine for OpenWebUI instances.

    Provides:
    - Full sync for initial data load
    - Incremental sync for updates
    - Change detection using timestamps
    - Efficient API usage with retry logic
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize sync engine.

        Args:
            db_manager: Database manager instance. Creates new if not provided.
        """
        self.db = db_manager or DatabaseManager()

    # ========================================================================
    # API COMMUNICATION
    # ========================================================================

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """
        Generate authorization headers for API requests.

        Args:
            api_key: JWT bearer token

        Returns:
            dict: Headers with authorization
        """
        return {"Authorization": f"Bearer {api_key}"}

    def _fetch_api(self, instance_name: str, endpoint: str) -> Optional[Any]:
        """
        Fetch data from OpenWebUI API with retry logic.

        Args:
            instance_name: Instance name (e.g., 'fasgpt')
            endpoint: API endpoint path

        Returns:
            JSON response data or None if failed
        """
        instance_config = INSTANCES.get(instance_name)
        if not instance_config:
            print(f"  [ERROR] Unknown instance: {instance_name}")
            return None

        url = f"{instance_config['url']}{endpoint}"
        headers = self._get_headers(instance_config['api_key'])

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"  [WARN] Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    print(f"  [WARN] HTTP {response.status_code} for {endpoint}")
                    return None
            except Exception as e:
                print(f"  [WARN] Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        print(f"  [ERROR] Failed to fetch {endpoint} after {MAX_RETRIES} attempts")
        return None

    def fetch_users(self, instance_name: str) -> List[Dict]:
        """Fetch all users from instance."""
        data = self._fetch_api(instance_name, "/api/v1/users/all")
        return data.get("users", []) if data else []

    def fetch_user_chats(self, instance_name: str, user_id: str) -> List[Dict]:
        """Fetch chats for a specific user."""
        data = self._fetch_api(instance_name, f"/api/v1/chats/list/user/{user_id}")
        return data if isinstance(data, list) else []

    def fetch_chat_detail(self, instance_name: str, chat_id: str) -> Optional[Dict]:
        """
        Fetch detailed chat data including messages.

        Uses admin endpoint /api/v1/chats/all/{id} to access all users' chats.
        """
        return self._fetch_api(instance_name, f"/api/v1/chats/all/{chat_id}")

    def fetch_models(self, instance_name: str) -> List[Dict]:
        """Fetch available models."""
        # Try with trailing slash first
        data = self._fetch_api(instance_name, "/api/v1/models/")
        if not data:
            data = self._fetch_api(instance_name, "/api/v1/models")

        if not data:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data", [])
        return []

    def fetch_knowledge_bases(self, instance_name: str) -> List[Dict]:
        """Fetch knowledge bases."""
        data = self._fetch_api(instance_name, "/api/v1/knowledge/")
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        return []

    # ========================================================================
    # SYNC OPERATIONS
    # ========================================================================

    def sync_instance(self, instance_name: str, force_full: bool = False):
        """
        Sync an instance (auto-detect full vs incremental).

        Args:
            instance_name: Instance to sync
            force_full: Force full sync even if incremental is possible
        """
        # Ensure instance exists in database
        instance_config = INSTANCES.get(instance_name)
        if not instance_config:
            print(f"[ERROR] Unknown instance: {instance_name}")
            return

        instance_id = self.db.upsert_instance(
            instance_name,
            instance_config['url'],
            instance_config['api_key'],
            instance_config['is_active']
        )

        # Determine sync type
        last_sync = self.db.get_last_sync_time(instance_id)

        if force_full or last_sync is None:
            self.full_sync(instance_name, instance_id)
        else:
            self.incremental_sync(instance_name, instance_id)

    def full_sync(self, instance_name: str, instance_id: int):
        """
        Perform full synchronization of all data.

        Args:
            instance_name: Instance to sync
            instance_id: Instance database ID
        """
        print(f"\n{'='*70}")
        print(f"FULL SYNC: {instance_name.upper()}")
        print(f"{'='*70}\n")

        sync_run_id = self.db.start_sync_run(instance_name, 'full')
        sync_time = datetime.now()

        try:
            # 1. Sync models
            print("Fetching models...")
            models = self.fetch_models(instance_name)
            for model in models:
                self.db.upsert_model(model, instance_id, sync_time)
            print(f"  [SUCCESS] Synced {len(models)} models")

            # 2. Sync knowledge bases
            print("Fetching knowledge bases...")
            kbs = self.fetch_knowledge_bases(instance_name)
            for kb in kbs:
                self.db.upsert_knowledge_base(kb, instance_id, sync_time)
            print(f"  [SUCCESS] Synced {len(kbs)} knowledge bases")

            # 3. Sync users
            print("Fetching users...")
            users = self.fetch_users(instance_name)
            for user in users:
                self.db.upsert_user(user, instance_id, sync_time)
            print(f"  [SUCCESS] Synced {len(users)} users")

            # 4. Sync chats and messages
            total_chats = 0
            total_messages = 0

            print(f"\nSyncing chats and messages for {len(users)} users...")
            for i, user in enumerate(users, 1):
                user_name = user.get('name', 'Unknown')
                print(f"  [{i:3}/{len(users)}] {user_name}...", end="", flush=True)

                chats = self.fetch_user_chats(instance_name, user['id'])
                print(f" {len(chats)} chats", end="", flush=True)

                for chat in chats:
                    # Store chat metadata
                    self.db.upsert_chat(chat, instance_id, user['id'], sync_time)
                    total_chats += 1

                    # Fetch full chat details
                    chat_detail = self.fetch_chat_detail(instance_name, chat['id'])
                    if not chat_detail or 'chat' not in chat_detail:
                        continue

                    chat_data = chat_detail['chat']

                    # Store models
                    models_list = chat_data.get('models', [])
                    for model_id in models_list:
                        self.db.upsert_chat_model(chat['id'], instance_id, model_id, sync_time)

                    # Store messages
                    messages = chat_data.get('messages', [])
                    for message in messages:
                        self.db.upsert_message(message, chat['id'], instance_id, sync_time)

                        # Store file attachments
                        for file_data in message.get('files', []):
                            if 'file' in file_data and file_data['file'].get('id'):
                                self.db.upsert_file(file_data, message['id'], instance_id, sync_time)

                    total_messages += len(messages)

                    time.sleep(API_DELAY)  # Rate limiting

                print(f" ({total_messages} msgs)")

            # Mark sync as successful
            self.db.complete_sync_run(sync_run_id, len(users), total_chats, total_messages)
            self.db.update_instance_last_sync(instance_id, sync_time)

            print(f"\n{'='*70}")
            print(f"SYNC COMPLETE")
            print(f"  Users: {len(users)}")
            print(f"  Chats: {total_chats}")
            print(f"  Messages: {total_messages}")
            print(f"{'='*70}\n")

        except Exception as e:
            self.db.fail_sync_run(sync_run_id, str(e))
            print(f"\n[ERROR] Sync failed: {e}")
            raise

    def incremental_sync(self, instance_name: str, instance_id: int):
        """
        Perform incremental synchronization (only changed data).

        Args:
            instance_name: Instance to sync
            instance_id: Instance database ID
        """
        print(f"\n{'='*70}")
        print(f"INCREMENTAL SYNC: {instance_name.upper()}")
        print(f"{'='*70}\n")

        sync_run_id = self.db.start_sync_run(instance_name, 'incremental')
        sync_time = datetime.now()
        last_sync = self.db.get_last_sync_time(instance_id)

        print(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S') if last_sync else 'Never'}")
        print(f"Sync time: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # 1. Quick sync models and KBs (small datasets)
            print("Syncing models...")
            models = self.fetch_models(instance_name)
            for model in models:
                self.db.upsert_model(model, instance_id, sync_time)
            print(f"  [SUCCESS] {len(models)} models")

            print("Syncing knowledge bases...")
            kbs = self.fetch_knowledge_bases(instance_name)
            for kb in kbs:
                self.db.upsert_knowledge_base(kb, instance_id, sync_time)
            print(f"  [SUCCESS] {len(kbs)} knowledge bases")

            # 2. Check for new/changed users
            print("\nChecking users...")
            current_users = self.fetch_users(instance_name)
            current_user_ids = {u['id'] for u in current_users}
            db_user_ids = self.db.get_user_ids_for_instance(instance_id)

            new_user_ids = current_user_ids - db_user_ids
            deleted_user_ids = db_user_ids - current_user_ids

            # Update all current users (in case name/email changed)
            for user in current_users:
                self.db.upsert_user(user, instance_id, sync_time)

            # Mark deleted users
            if deleted_user_ids:
                self.db.mark_users_deleted(list(deleted_user_ids), instance_id)
                print(f"  [WARN] {len(deleted_user_ids)} users marked as deleted")

            print(f"  [SUCCESS] {len(current_users)} users checked")
            if new_user_ids:
                print(f"  + {len(new_user_ids)} new users")

            # 3. Sync chats (check for updates using updated_at timestamp)
            total_chats_updated = 0
            total_messages_updated = 0
            total_chats_checked = 0

            print(f"\nChecking chats for {len(current_users)} users...")
            for i, user in enumerate(current_users, 1):
                user_name = user.get('name', 'Unknown')
                user_id = user['id']

                # For new users, do full chat sync
                is_new_user = user_id in new_user_ids

                chats = self.fetch_user_chats(instance_name, user_id)
                chats_updated_count = 0

                for chat in chats:
                    total_chats_checked += 1
                    chat_updated_at = datetime.fromtimestamp(chat['updated_at'])

                    # Get existing chat from DB
                    db_chat = self.db.get_chat(chat['id'], instance_id)

                    # Check if chat is new or updated
                    needs_update = (
                        is_new_user or
                        not db_chat or
                        chat_updated_at > datetime.fromisoformat(db_chat['sync_datetime'])
                    )

                    if needs_update:
                        # Fetch full chat details
                        chat_detail = self.fetch_chat_detail(instance_name, chat['id'])

                        if chat_detail and 'chat' in chat_detail:
                            # Update chat
                            self.db.upsert_chat(chat, instance_id, user_id, sync_time)

                            # Update models
                            self.db.delete_chat_models(chat['id'], instance_id)
                            for model_id in chat_detail['chat'].get('models', []):
                                self.db.upsert_chat_model(chat['id'], instance_id, model_id, sync_time)

                            # Update messages
                            self.db.delete_messages_for_chat(chat['id'], instance_id)
                            messages = chat_detail['chat'].get('messages', [])
                            for message in messages:
                                self.db.upsert_message(message, chat['id'], instance_id, sync_time)

                                # Update files
                                for file_data in message.get('files', []):
                                    if 'file' in file_data and file_data['file'].get('id'):
                                        self.db.upsert_file(file_data, message['id'], instance_id, sync_time)

                            total_messages_updated += len(messages)
                            chats_updated_count += 1

                        time.sleep(API_DELAY)
                    else:
                        # Chat hasn't changed, just touch it
                        self.db.touch_chat(chat['id'], instance_id, sync_time)

                if chats_updated_count > 0:
                    print(f"  [{i:3}/{len(current_users)}] {user_name}: {chats_updated_count}/{len(chats)} chats updated")

                total_chats_updated += chats_updated_count

            # Mark stale chats as deleted (chats that weren't touched in this sync)
            self.db.mark_stale_chats_deleted(instance_id, last_sync)

            # Mark sync as successful
            self.db.complete_sync_run(
                sync_run_id,
                len(current_users),
                total_chats_updated,
                total_messages_updated
            )
            self.db.update_instance_last_sync(instance_id, sync_time)

            print(f"\n{'='*70}")
            print(f"SYNC COMPLETE")
            print(f"  Chats checked: {total_chats_checked}")
            print(f"  Chats updated: {total_chats_updated}")
            print(f"  Messages updated: {total_messages_updated}")
            print(f"{'='*70}\n")

        except Exception as e:
            self.db.fail_sync_run(sync_run_id, str(e))
            print(f"\n[ERROR] Sync failed: {e}")
            raise

    def sync_all_instances(self, force_full: bool = False):
        """
        Sync all active instances.

        Args:
            force_full: Force full sync for all instances
        """
        active_instances = [name for name, config in INSTANCES.items() if config.get('is_active', True)]

        print(f"\n{'='*70}")
        print(f"SYNCING {len(active_instances)} INSTANCES")
        print(f"{'='*70}\n")

        for instance_name in active_instances:
            self.sync_instance(instance_name, force_full=force_full)
            print()  # Blank line between instances
