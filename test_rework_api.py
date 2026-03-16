"""Test script for ALL rework-related API endpoints."""
import requests
import json
import sys

BASE = "http://localhost:8000"

# 1. Login as DEMO_USER to get access token
print("=" * 70)
print("  REWORK API ENDPOINT TESTS")
print("=" * 70)

print("\n[1] LOGIN as DEMO_USER ...")
r = requests.post(f"{BASE}/api/traceability/login", json={
    "user_id": "DEMO_USER",
    "password": "Test@1234"
}, timeout=10)
print(f"  Status: {r.status_code}")
data = r.json()
token = data.get("access_token", "")
if not token:
    print(f"  FAILED: {data}")
    sys.exit(1)
print(f"  Token obtained: {token[:40]}...")
headers = {"Authorization": f"Bearer {token}"}

passed = 0
failed = 0
total = 0

def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} - {detail}")


# ---------------------------------------------------------------
# 2. GET_ALL_REWORK_PRINT_DETAILS
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[2] POST /api/printing/all-rework-print-details")
print("-" * 70)
r = requests.post(f"{BASE}/api/printing/all-rework-print-details", json={
    "printed_by": "DEMO_USER",
    "station_no": "Station-1",
    "plant_code": "DM1"
}, headers=headers, timeout=30)
data = r.json()
print(f"  Status: {r.status_code}")
check("Status 200", r.status_code == 200)
check("Success=True", data.get("success") == True)
check("Has data", data.get("data") is not None and len(data["data"]) > 0)

if data.get("data"):
    all_rwk = all(item.get("tag_type") == "RWK" for item in data["data"])
    check("All tag_type='RWK'", all_rwk,
          str([i["tag_type"] for i in data["data"] if i["tag_type"] != "RWK"]))
    
    # Check none have 'NEW' tag_type (old bug)
    any_new = any(item.get("tag_type") == "NEW" for item in data["data"])
    check("No tag_type='NEW'", not any_new, "Found 'NEW' in rework results")
    
    for i, item in enumerate(data["data"]):
        print(f"  [{i+1}] {item['barcode']} | tag_type={item['tag_type']} | part={item.get('supplier_part_no')}")


# ---------------------------------------------------------------
# 3. REWORK_RE_PRINT (with correct supervisor)
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[3] POST /api/printing/rework-reprint")
print("-" * 70)
if data.get("data") and len(data["data"]) > 0:
    old_barcode = data["data"][0]["barcode"]
    supplier_part = data["data"][0]["supplier_part_no"]
    part_no_val = data["data"][0]["part_no"]
    supplier_code = data["data"][0]["supplier_code"]
    weight_val = data["data"][0]["weight"] or 100
    print(f"  Using old_barcode: {old_barcode}")

    r = requests.post(f"{BASE}/api/printing/rework-reprint", json={
        "supervisor_user_id": "DEMO_SUPER",
        "supervisor_password": "Super@1234",
        "plant_code": "DM1",
        "station_no": "Station-1",
        "supplier_code": supplier_code,
        "supplier_part_no": supplier_part,
        "part_no": part_no_val,
        "lot_no_1": "LOT-RW-TEST",
        "lot_no_2": "",
        "weight": weight_val,
        "qty": 50,
        "printed_by": "DEMO_USER",
        "old_barcode": old_barcode,
        "gross_weight": "110"
    }, headers=headers, timeout=30)
    rdata = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Response: {json.dumps(rdata, indent=2, default=str)}")
    check("Rework reprint status 200", r.status_code == 200, f"Got {r.status_code}: {rdata}")
    if r.status_code == 200:
        check("Rework reprint success", rdata.get("success") == True)
        if rdata.get("data"):
            check("tag_type='RWK'", rdata["data"].get("tag_type") == "RWK",
                  f"Got {rdata['data'].get('tag_type')}")
else:
    print("  SKIPPED (no rework records found)")


# ---------------------------------------------------------------
# 4. Verify rework details after reprint
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[4] POST /api/printing/all-rework-print-details (after reprint)")
print("-" * 70)
r = requests.post(f"{BASE}/api/printing/all-rework-print-details", json={
    "printed_by": "DEMO_USER",
    "station_no": "Station-1",
    "plant_code": "DM1"
}, headers=headers, timeout=30)
data = r.json()
print(f"  Status: {r.status_code}")
check("Post-reprint status 200", r.status_code == 200)
if data.get("data"):
    all_rwk = all(item.get("tag_type") == "RWK" for item in data["data"])
    check("Post-reprint all tag_type='RWK'", all_rwk)
    print(f"  Records: {len(data['data'])}")
    for i, item in enumerate(data["data"]):
        print(f"    {i+1}. {item['barcode']} | tag_type={item['tag_type']}")


# ---------------------------------------------------------------
# 5. /api/rework/validate-tag
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[5] POST /api/rework/validate-tag")
print("-" * 70)
test_barcodes = [
    "DEMO|DM1|DMPART005|LOT2026E1|RW03",
    "DEMO-DM1-001-RW01",
]
for bc in test_barcodes:
    r = requests.post(f"{BASE}/api/rework/validate-tag", json={
        "barcode": bc,
        "supplier_code": "DEMO"
    }, headers=headers, timeout=30)
    print(f"  Barcode: {bc}")
    print(f"  Status: {r.status_code}")
    rdata = r.json()
    check(f"validate-tag {bc[:30]}...", r.status_code in [200, 404],
          f"Unexpected {r.status_code}")
    if r.status_code == 200:
        print(f"  Success: {rdata.get('success')}")


# ---------------------------------------------------------------
# 6. /api/rework/print-details
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[6] POST /api/rework/print-details")
print("-" * 70)
r = requests.post(f"{BASE}/api/rework/print-details", json={
    "supplier_part_no": "DM-PART-005",
    "lot_no_1": "LOT2026E1",
    "supplier_code": "DEMO"
}, headers=headers, timeout=30)
print(f"  Status: {r.status_code}")
rdata = r.json()
check("rework print-details status", r.status_code in [200, 404])
if r.status_code == 200:
    print(f"  Success: {rdata.get('success')}")
    if rdata.get("data"):
        print(f"  Records: {len(rdata['data'])}")


# ---------------------------------------------------------------
# 7. /api/rework/last-print-details
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[7] POST /api/rework/last-print-details")
print("-" * 70)
r = requests.post(f"{BASE}/api/rework/last-print-details", json={
    "supplier_part_no": "DM-PART-005"
}, headers=headers, timeout=30)
print(f"  Status: {r.status_code}")
rdata = r.json()
check("rework last-print-details status", r.status_code in [200, 404])
if r.status_code == 200:
    print(f"  Data: {json.dumps(rdata.get('data'), default=str)}")


# ---------------------------------------------------------------
# 8. /api/rework/reprint-parameter
# ---------------------------------------------------------------
print("\n" + "-" * 70)
print("[8] POST /api/rework/reprint-parameter")
print("-" * 70)
r = requests.post(f"{BASE}/api/rework/reprint-parameter", json={
    "supplier_part_no": "DM-PART-005"
}, headers=headers, timeout=30)
print(f"  Status: {r.status_code}")
rdata = r.json()
check("rework reprint-parameter status", r.status_code in [200, 404])
if r.status_code == 200:
    print(f"  Data: {json.dumps(rdata.get('data'), default=str)}")


# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
print("\n" + "=" * 70)
print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
print("=" * 70)
