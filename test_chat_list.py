import requests
import json

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
}

print("Testing chat list and detail endpoints:")
print("="*70)

# Get a user
users = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/all', headers=headers).json()['users']
test_user = users[0]
print(f"\nTest user: {test_user['name']} (ID: {test_user['id']})")

# Get their chats
print(f"\nTesting: GET /api/v1/chats/list/user/{test_user['id'][:8]}...")
resp = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/list/user/{test_user["id"]}', headers=headers)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")

if resp.status_code == 200:
    chats = resp.json()
    print(f"Chats returned: {len(chats)}")

    if chats:
        chat = chats[0]
        print(f"\nFirst chat structure:")
        print(json.dumps(chat, indent=2)[:500])

        # Now try to get the full chat details
        chat_id = chat['id']
        print(f"\n{'='*70}")
        print(f"Testing chat detail for: {chat_id}")
        print(f"{'='*70}")

        # Try different endpoint patterns (with and without trailing slashes)
        endpoints_to_test = [
            f"/api/v1/chats/{chat_id}",
            f"/api/v1/chats/{chat_id}/",
            f"/api/v1/chats/all/{chat_id}",
            f"/api/v1/chats/all/{chat_id}/",
            f"/api/v1/admin/chats/{chat_id}",
            f"/api/v1/admin/chats/{chat_id}/",
            f"/api/v1/chats/{chat_id}/messages",
            f"/api/v1/chats/{chat_id}/messages/",
        ]

        for endpoint in endpoints_to_test:
            full_url = f"http://berkshiregpt.resecon.ai{endpoint}"
            print(f"\nTrying: {endpoint}")
            resp = requests.get(full_url, headers=headers)
            print(f"  Status: {resp.status_code}")
            print(f"  Content-Type: {resp.headers.get('Content-Type')}")

            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                if 'json' in content_type:
                    try:
                        data = resp.json()
                        print(f"  SUCCESS! Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                        print(f"  Preview: {str(data)[:200]}")
                    except:
                        print(f"  Response: {resp.text[:200]}")
                else:
                    print(f"  HTML response (endpoint doesn't exist)")
            elif resp.status_code == 401:
                print(f"  Unauthorized")
            elif resp.status_code == 404:
                print(f"  Not found")
else:
    print(f"Error: {resp.text}")
