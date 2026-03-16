"""Quick test for image endpoint on port 8001."""
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

BASE = "http://localhost:8001"

# Login
r = urlopen(Request(
    f"{BASE}/api/traceability/login",
    data=json.dumps({"user_id": "DEMO_USER", "password": "Demo@123"}).encode(),
    headers={"Content-Type": "application/json"},
))
token = json.loads(r.read())["data"]["access_token"]
print("Login OK")

# Get image
try:
    r2 = urlopen(Request(
        f"{BASE}/api/printing/image/DM-PART-006",
        headers={"Authorization": f"Bearer {token}"},
    ))
    print(f"Status: {r2.status}")
    print(json.dumps(json.loads(r2.read()), indent=2))
except HTTPError as e:
    print(f"Error: {e.code}")
    print(e.read().decode())
