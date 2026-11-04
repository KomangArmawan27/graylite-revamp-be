import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token

TOKEN = create_access_token({"sub": 29, "login": "komang", "roles": ["General", "Admin"], "ccId": 1})

client = TestClient(app)
base_headers = {"Authorization": f"Bearer {TOKEN}"}

results = []

def test_endpoint(name, method, url, headers=None, **kwargs):
    print(f"Testing {method} {url} ...")
    req_headers = {**base_headers, **(headers or {})}
    if method == "GET":
        resp = client.get(url, headers=req_headers, **kwargs)
    elif method == "POST":
        resp = client.post(url, headers=req_headers, **kwargs)
    elif method == "PUT":
        resp = client.put(url, headers=req_headers, **kwargs)
    elif method == "DELETE":
        resp = client.delete(url, headers=req_headers, **kwargs)
    
    resp_body = {}
    try:
        resp_body = resp.json()
    except Exception:
        resp_body = resp.text

    results.append({
        "name": name,
        "method": method,
        "url": url,
        "status": resp.status_code,
        "headers": dict(resp.headers),
        "response": resp_body
    })
    print(f"  -> Status: {resp.status_code}")

def run_all():
    settings.ENABLE_WRITES = True
    settings.ENABLE_DELETE = True

    test_endpoint("Get Menu", "GET", "/v1/menu")
    test_endpoint("Get Browser Meta (128)", "GET", "/v1/meta/browser/128")
    
    # Get Form Meta (129) to dynamically fetch schemaVersion
    print("Testing GET /v1/meta/form/129 ...")
    meta_resp = client.get("/v1/meta/form/129", headers=base_headers)
    schema_version = "18dbdf28"
    if meta_resp.status_code == 200:
        meta_data = meta_resp.json()
        schema_version = meta_data.get("schemaVersion", "18dbdf28")
    
    results.append({
        "name": "Get Form Meta (129)",
        "method": "GET",
        "url": "/v1/meta/form/129",
        "status": meta_resp.status_code,
        "headers": dict(meta_resp.headers),
        "response": meta_resp.json() if meta_resp.headers.get("content-type", "").startswith("application/json") else meta_resp.text
    })

    test_endpoint("Get Grid Meta (132)", "GET", "/v1/meta/grid/132")
    test_endpoint("Get Picker Meta (803)", "GET", "/v1/meta/picker/803")
    test_endpoint("Get Browser Rows (128)", "GET", "/v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31")
    test_endpoint("Get New Form (129)", "GET", "/v1/forms/129/new")

    create_payload = {
        "schemaVersion": schema_version,
        "header": {
            "doc_no": "SO-2026-001",
            "doc_date": "2026-03-29",
            "cust_id": 1,
            "cc_id": 1,
            "doc_total": 840000,
            "doc_remark": "[API-TEST] create with grid"
        },
        "grids": {
            "132": {
                "rows": [
                    {
                        "item_id": 1,
                        "trans_qty": 10,
                        "trans_price": 55000,
                        "trans_discvalue": 0,
                        "trans_remark": "t1"
                    }
                ]
            }
        }
    }

    # Test create with idempotency key and grid rows
    test_endpoint("Create Record with Idempotency and Grid", "POST", "/v1/forms/129/records", json=create_payload, headers={"Idempotency-Key": "testkey123456"})

    # Test Idempotent replay
    test_endpoint("Idempotent Replay", "POST", "/v1/forms/129/records", json=create_payload, headers={"Idempotency-Key": "testkey123456"})

    report = "# Integration Test Results against Real Endpoints (Run 2)\n\n"
    for r in results:
        report += f"## {r['name']}\n"
        report += f"- **Method/URL:** `{r['method']} {r['url']}`\n"
        report += f"- **Status Code:** `{r['status']}`\n"
        report += f"- **Response Headers:**\n```json\n{json.dumps(dict(r['headers']), indent=2, default=str)}\n```\n"
        report += f"- **Response:**\n```json\n{json.dumps(r['response'], indent=2, default=str)}\n```\n\n"

    output_path = r"\\wsl.localhost\Ubuntu\home\komang\project\graylite-be\test_results2.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print("Test results written to test_results2.md")

if __name__ == "__main__":
    run_all()
