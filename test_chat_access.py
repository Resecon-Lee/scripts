import requests

# Test if we can access other users' chats
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
}

print("Testing chat access permissions...")
print("="*70)

# Get all users
users = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/all', headers=headers).json()['users']
print(f"\nTotal users: {len(users)}")

# Find first user with chats (not Lehem Felican)
for user in users:
    if 'Lehem' not in user['name']:
        print(f"\nTesting with user: {user['name']} ({user['email']})")

        # Get their chats
        chats = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/list/user/{user["id"]}', headers=headers).json()
        print(f"  Chats listed: {len(chats)}")

        if chats:
            # Try to access first chat
            chat_id = chats[0]['id']
            print(f"  Testing chat ID: {chat_id}")

            # Try standard endpoint
            resp = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/{chat_id}', headers=headers)
            print(f"  GET /api/v1/chats/{chat_id[:8]}...")
            print(f"    Status: {resp.status_code}")
            print(f"    Response: {resp.text[:150]}")

            # Try with /all suffix (admin endpoint?)
            resp2 = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/all/{chat_id}', headers=headers)
            print(f"  GET /api/v1/chats/all/{chat_id[:8]}...")
            print(f"    Status: {resp2.status_code}")

            # Check who the authenticated user is
            me = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/me', headers=headers).json()
            print(f"\n  Authenticated as: {me.get('name')} (Role: {me.get('role')})")

            break

print("\n" + "="*70)
