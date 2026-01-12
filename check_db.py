import sqlite3

conn = sqlite3.connect('data/openwebui_sync.db')
conn.row_factory = sqlite3.Row

print('\n' + '='*70)
print('DATABASE CONTENTS - BERKSHIREGPT')
print('='*70 + '\n')

print('Top Users by Messages:')
print('-'*70)
for row in conn.execute("""
    SELECT u.name, u.email,
           COUNT(DISTINCT c.id) as chats,
           COUNT(m.id) as messages
    FROM users u
    LEFT JOIN chats c ON u.id = c.user_id AND c.instance_id = u.instance_id
    LEFT JOIN messages m ON c.id = m.chat_id
    WHERE u.instance_id = (SELECT id FROM instances WHERE name = 'berkshiregpt')
    GROUP BY u.id
    ORDER BY messages DESC
    LIMIT 10
"""):
    print(f"  {row['name']:<30} {row['messages']:>4} messages, {row['chats']:>3} chats")

print('\n' + 'Model Usage:')
print('-'*70)
for row in conn.execute("""
    SELECT cm.model_id, COUNT(*) as usage
    FROM chat_models cm
    JOIN chats c ON cm.chat_id = c.id
    WHERE c.instance_id = (SELECT id FROM instances WHERE name = 'berkshiregpt')
    GROUP BY cm.model_id
    ORDER BY usage DESC
    LIMIT 5
"""):
    print(f"  {row['model_id']:<40} {row['usage']:>3} chats")

print('\n' + 'Message Statistics:')
print('-'*70)
stats = conn.execute("""
    SELECT
        COUNT(*) as total_msgs,
        SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_msgs,
        SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as ai_msgs,
        AVG(content_length) as avg_length
    FROM messages
    WHERE instance_id = (SELECT id FROM instances WHERE name = 'berkshiregpt')
""").fetchone()

print(f"  Total Messages: {stats['total_msgs']:,}")
print(f"  User Messages: {stats['user_msgs']:,}")
print(f"  AI Messages: {stats['ai_msgs']:,}")
print(f"  Avg Message Length: {stats['avg_length']:.0f} chars")

print('\n' + '='*70 + '\n')
conn.close()
