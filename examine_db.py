import sqlite3
import json
import sys
from datetime import datetime

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Connect to the database
conn = sqlite3.connect(r'.\data\berkshiregpt.db')
cursor = conn.cursor()

print("="*70)
print("BERKSHIREGPT DATABASE ANALYSIS")
print("="*70)

# Get counts
print("\nRECORD COUNTS:")
print(f"  Users: {cursor.execute('SELECT COUNT(*) FROM user').fetchone()[0]}")
print(f"  Chats: {cursor.execute('SELECT COUNT(*) FROM chat').fetchone()[0]}")
print(f"  Models: {cursor.execute('SELECT COUNT(*) FROM model').fetchone()[0]}")
print(f"  Documents: {cursor.execute('SELECT COUNT(*) FROM document').fetchone()[0]}")
print(f"  Tags: {cursor.execute('SELECT COUNT(*) FROM tag').fetchone()[0]}")
print(f"  Knowledge Bases: {cursor.execute('SELECT COUNT(*) FROM knowledge').fetchone()[0]}")
print(f"  Files: {cursor.execute('SELECT COUNT(*) FROM file').fetchone()[0]}")

# Examine a sample chat
print("\nSAMPLE CHAT STRUCTURE:")
chat = cursor.execute('SELECT id, user_id, title, created_at, updated_at, chat FROM chat WHERE chat IS NOT NULL LIMIT 1').fetchone()

if chat:
    print(f"  Chat ID: {chat[0]}")
    print(f"  User ID: {chat[1]}")
    print(f"  Title: {chat[2][:50]}...")
    print(f"  Created: {chat[3]}")
    print(f"  Updated: {chat[4]}")

    # Parse chat JSON
    chat_data = json.loads(chat[5]) if chat[5] else {}
    print(f"\n  Chat JSON Keys: {list(chat_data.keys())}")
    print(f"  Models used: {chat_data.get('models', [])}")
    print(f"  Message count: {len(chat_data.get('messages', []))}")

    if chat_data.get('messages'):
        msg = chat_data['messages'][0]
        print(f"\n  First message:")
        print(f"    Role: {msg.get('role')}")
        print(f"    Content length: {len(msg.get('content', ''))} chars")
        print(f"    Has files: {len(msg.get('files', [])) > 0}")

# Sample user data
print("\nSAMPLE USER DATA:")
users = cursor.execute('SELECT id, name, email, role, created_at, last_active_at FROM user LIMIT 3').fetchall()
for user in users:
    print(f"  - {user[1]} ({user[2]}) - Role: {user[3]}")

# Model information
print("\nAVAILABLE MODELS:")
models = cursor.execute('SELECT id, name, base_model_id FROM model LIMIT 5').fetchall()
for model in models:
    print(f"  - {model[1]} (ID: {model[0]})")

# Chat activity by user
print("\nCHAT ACTIVITY BY USER:")
user_chats = cursor.execute('''
    SELECT u.name, u.email, COUNT(c.id) as chat_count
    FROM user u
    LEFT JOIN chat c ON u.id = c.user_id
    GROUP BY u.id, u.name, u.email
    ORDER BY chat_count DESC
    LIMIT 10
''').fetchall()

for uc in user_chats:
    print(f"  {uc[0]:25} - {uc[2]:3} chats")

# Chat date range
print("\nCHAT DATE RANGE:")
date_range = cursor.execute('''
    SELECT
        MIN(created_at) as first_chat,
        MAX(created_at) as last_chat
    FROM chat
''').fetchone()
print(f"  First chat: {date_range[0]}")
print(f"  Last chat: {date_range[1]}")

# Check if we can extract model usage from chats
print("\nEXTRACTING MODEL USAGE FROM CHATS...")
model_usage = {}
chats_with_data = cursor.execute('SELECT chat FROM chat WHERE chat IS NOT NULL').fetchall()

for (chat_json,) in chats_with_data[:50]:  # Sample first 50
    try:
        chat_data = json.loads(chat_json)
        models_list = chat_data.get('models', [])
        for model in models_list:
            model_usage[model] = model_usage.get(model, 0) + 1
    except:
        pass

print(f"  Found {len(model_usage)} unique models in sample:")
for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"    {model}: {count} chats")

conn.close()

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
