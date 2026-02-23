import urllib.request, json

data = json.dumps({
    "supplier_part_no": "SP-PART-01",
    "supplier_code": "SUP001",
    "plant_code": "PLT01",
    "station_no": "STN01"
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/traceability/confirm-model",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    r = urllib.request.urlopen(req)
    print(json.dumps(json.loads(r.read()), indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"ERROR {e.code}: {body}")
except Exception as e:
    import traceback
    traceback.print_exc()
