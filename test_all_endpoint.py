import requests

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
}

# Get a chat ID to test
users = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/all', headers=headers).json()['users']
user = users[0]
chats = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/list/user/{user["id"]}', headers=headers).json()
chat_id = chats[0]['id']

print(f"Testing chat ID: {chat_id}\n")

# Test the /all/ endpoint
resp = requests.get(f'http://berkshiregpt.resecon.ai/api/v1/chats/all/{chat_id}', headers=headers)
print(f"Status Code: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"Content Length: {len(resp.text)}")
print(f"Raw Content: {resp.text[:500]}")

try:
    data = resp.json()
    print(f"\nParsed JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
except Exception as e:
    print(f"\nJSON parse error: {e}")
