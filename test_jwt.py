"""Quick JWT authentication test script."""
import requests
import json

BASE = "http://localhost:8000"

# 1. Login to get tokens
print("=== 1. LOGIN ===")
r = requests.post(f"{BASE}/api/traceability/login", json={"user_id": "testuser01", "password": "pass@123"})
print(f"Status: {r.status_code}")
data = r.json()
print(f"Success: {data.get('success')}")
print(f"access_token present: {'access_token' in data}")
print(f"refresh_token present: {'refresh_token' in data}")
print(f"token_type: {data.get('token_type')}")
access_token = data.get("access_token", "")
refresh_token = data.get("refresh_token", "")
print(f"access_token (first 50): {access_token[:50]}...")

model_body = {"supplier_code": "SUP001", "plant_code": "PLT01", "station_no": "STN01", "printed_by": "testuser01"}

# 2. No token -> should fail
print("\n=== 2. NO TOKEN - model-list ===")
r2 = requests.post(f"{BASE}/api/traceability/model-list", json=model_body)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.json()}")

# 3. With token -> should succeed
print("\n=== 3. WITH TOKEN - model-list ===")
headers = {"Authorization": f"Bearer {access_token}"}
r3 = requests.post(f"{BASE}/api/traceability/model-list", json=model_body, headers=headers)
print(f"Status: {r3.status_code}")
resp = r3.json()
print(f"Success: {resp.get('success')}")

# 4. Refresh token
print("\n=== 4. REFRESH TOKEN ===")
r4 = requests.post(f"{BASE}/api/traceability/refresh-token", json={"refresh_token": refresh_token})
print(f"Status: {r4.status_code}")
rt = r4.json()
print(f"Success: {rt.get('success')}")
print(f"new access_token present: {'access_token' in rt}")

# 5. Print endpoint with token
print("\n=== 5. WITH TOKEN - scan ===")
r5 = requests.post(f"{BASE}/api/printing/scan", json={"barcode": "KB202602050002"}, headers=headers)
print(f"Status: {r5.status_code}")
print(f"Success: {r5.json().get('success')}")

# 6. Register endpoint with token
print("\n=== 6. WITH TOKEN - groups ===")
r6 = requests.get(f"{BASE}/api/register/groups", headers=headers)
print(f"Status: {r6.status_code}")
print(f"Response keys: {list(r6.json().keys())}")

# 7. Invalid token
print("\n=== 7. INVALID TOKEN ===")
bad_headers = {"Authorization": "Bearer invalidtoken123"}
r7 = requests.post(f"{BASE}/api/traceability/model-list", json=model_body, headers=bad_headers)
print(f"Status: {r7.status_code}")
print(f"Response: {r7.json()}")

print("\n=== ALL TESTS COMPLETE ===")
