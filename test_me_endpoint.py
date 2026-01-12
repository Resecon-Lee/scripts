import requests
import json

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8'
}

print("Testing /api/v1/users/me endpoint:")
print("="*70)

resp = requests.get('http://berkshiregpt.resecon.ai/api/v1/users/me', headers=headers)
print(f"Status Code: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"\nRaw Response:")
print(resp.text)

print("\n" + "="*70)

if resp.status_code == 200:
    try:
        data = resp.json()
        print("\nParsed JSON:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"\nJSON parse error: {e}")
