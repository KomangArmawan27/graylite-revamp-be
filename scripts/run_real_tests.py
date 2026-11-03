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
    
    results.append({
        "name": name,
        "method": method,
        "url": url,
        "status": resp.status_code,
        "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
    })
    print(f"  -> Status: {resp.status_code}")

def run_all():
    settings.ENABLE_WRITES = True
    settings.ENABLE_DELETE = True

    test_endpoint("Get Menu", "GET", "/v1/menu")
    test_endpoint("Get Browser Meta (128)", "GET", "/v1/meta/browser/128")
    test_endpoint("Get Form Meta (129)", "GET", "/v1/meta/form/129")
    test_endpoint("Get Grid Meta (132)", "GET", "/v1/meta/grid/132")
    test_endpoint("Get Picker Meta (803)", "GET", "/v1/meta/picker/803")
    test_endpoint("Get Browser Rows (128)", "GET", "/v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31")
    test_endpoint("Get New Form (129)", "GET", "/v1/forms/129/new")

    # Test create with idempotency key
    test_endpoint("Create Record with Idempotency", "POST", "/v1/forms/129/records", json={
        "schemaVersion": "18dbdf28",
        "header": {
            "doc_no": "SO-2026-001",
            "doc_date": "2026-03-29",
            "cust_id": 1,
            "cc_id": 1,
            "doc_total": 840000,
            "doc_remark": "Test Sales Order"
        }
    }, headers={"Idempotency-Key": "testkey123456"})

    # Test Idempotent replay
    test_endpoint("Idempotent Replay", "POST", "/v1/forms/129/records", json={
        "schemaVersion": "18dbdf28",
        "header": {
            "doc_no": "SO-2026-001",
            "doc_date": "2026-03-29",
            "cust_id": 1,
            "cc_id": 1,
            "doc_total": 840000,
            "doc_remark": "Test Sales Order"
        }
    }, headers={"Idempotency-Key": "testkey123456"})

    report = "# Integration Test Results against Real Endpoints\n\n"
    for r in results:
        report += f"## {r['name']}\n"
        report += f"- **Method/URL:** `{r['method']} {r['url']}`\n"
        report += f"- **Status Code:** `{r['status']}`\n"
        report += f"- **Response:**\n```json\n{json.dumps(r['response'], indent=2, default=str)}\n```\n\n"

    with open(r"\\wsl.localhost\Ubuntu\home\komang\project\graylite-be\test_results.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Test results written to test_results.md")

if __name__ == "__main__":
    run_all()
