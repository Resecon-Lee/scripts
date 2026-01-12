import requests
import json
import base64

# All API keys from the config
API_KEYS = {
    "resgpt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjA2MDMyOTk4LWY5YjktNDY0ZS1iMmI2LTc1Zjg2MTRlMjBmMCJ9.sVAkpP6TZsg0VdXZ7GAKLxNTgPNAYvPBXDlr3tkH0wE",
    "fasgpt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImY3Njg4YzQ1LWIxNDctNDlmNy1hMDZjLTVhYzhiZjUyYjFiOSJ9.8YQcL-BIBA7w2Y0v3lxOcNwh2MMWaS5adOs22ruK9H4",
    "berkshiregpt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8"
}

URLS = {
    "resgpt": "http://resgpt.resecon.ai",
    "fasgpt": "http://fasgpt.resecon.ai",
    "berkshiregpt": "http://berkshiregpt.resecon.ai"
}

print("="*70)
print("CHECKING API KEY IDENTITIES")
print("="*70)

for instance, token in API_KEYS.items():
    print(f"\n{instance.upper()}:")
    print("-"*70)

    # Decode JWT to get user ID
    payload = token.split('.')[1]
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    user_id = decoded['id']
    print(f"JWT User ID: {user_id}")

    # Try to get user info from the instance
    headers = {'Authorization': f'Bearer {token}'}
    url = f"{URLS[instance]}/api/v1/users/all"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            users = resp.json()['users']
            user = next((u for u in users if u['id'] == user_id), None)
            if user:
                print(f"User: {user.get('name')} ({user.get('email')})")
                print(f"Role: {user.get('role')}")

                # Count chats
                chats_resp = requests.get(f"{URLS[instance]}/api/v1/chats/list/user/{user_id}", headers=headers)
                if chats_resp.status_code == 200:
                    chats = chats_resp.json()
                    print(f"Own chats: {len(chats)}")
            else:
                print("User ID not found in users list")
        else:
            print(f"Error: HTTP {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*70)
