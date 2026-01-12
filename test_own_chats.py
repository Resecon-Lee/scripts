import requests
import json
import base64

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
}

# Decode the JWT to get the user ID
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
payload = token.split('.')[1]
# Add padding if needed
payload += '=' * (4 - len(payload) % 4)
decoded = json.loads(base64.b64decode(payload))
user_id = decoded['id']

print(f"JWT User ID: {user_id}")
print("="*70)

# Get chats for this user
print(f"\nFetching chats for JWT user...")
resp = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/list/user/{user_id}', headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    chats = resp.json()
    print(f"Chats found: {len(chats)}")

    if chats:
        # Try to get details for the user's own chat
        chat_id = chats[0]['id']
        print(f"\nTrying to fetch details for own chat: {chat_id}")

        resp2 = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/{chat_id}', headers=headers)
        print(f"Status: {resp2.status_code}")
        print(f"Content-Type: {resp2.headers.get('Content-Type')}")

        if resp2.status_code == 200:
            content_type = resp2.headers.get('Content-Type', '')
            if 'json' in content_type:
                data = resp2.json()
                print(f"SUCCESS! Got chat detail")
                print(f"Keys: {list(data.keys())}")
                if 'chat' in data:
                    print(f"Chat keys: {list(data['chat'].keys())}")
                    if 'messages' in data['chat']:
                        print(f"Messages: {len(data['chat']['messages'])}")
            else:
                print("HTML response")
        else:
            print(f"Error: {resp2.text[:200]}")
else:
    print(f"Error: {resp.text}")

# Also check: Who is this user in the users list?
print(f"\n{'='*70}")
print("Looking up this user in the users list...")
users_resp = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/all', headers=headers)
if users_resp.status_code == 200:
    users = users_resp.json()['users']
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        print(f"Found: {user.get('name')} ({user.get('email')})")
        print(f"Role: {user.get('role')}")
    else:
        print("User ID not found in users list!")
