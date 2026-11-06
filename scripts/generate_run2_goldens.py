import json
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

TOKEN = create_access_token({"sub": 29, "login": "komang", "roles": ["General", "Admin"], "ccId": 1})
client = TestClient(app)
base_headers = {"Authorization": f"Bearer {TOKEN}"}

GOLDEN_DIR = r"\\wsl.localhost\Ubuntu\home\komang\project\graylite-be\tests\golden\run2"
os.makedirs(GOLDEN_DIR, exist_ok=True)

def save_golden(filename, data):
    path = os.path.join(GOLDEN_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved golden: {filename}")

def generate():
    # 1. Menu
    resp = client.get("/v1/menu", headers=base_headers)
    save_golden("menu.json", resp.json())

    # 2. Browser meta 128
    resp = client.get("/v1/meta/browser/128", headers=base_headers)
    save_golden("browser_meta_128.json", resp.json())

    # 3. Form meta 129
    resp = client.get("/v1/meta/form/129", headers=base_headers)
    save_golden("form_meta_129.json", resp.json())

    # 4. Grid meta 132
    resp = client.get("/v1/meta/grid/132", headers=base_headers)
    save_golden("grid_meta_132.json", resp.json())

    # 5. Picker meta 803
    resp = client.get("/v1/meta/picker/803", headers=base_headers)
    save_golden("picker_meta_803.json", resp.json())

    # 6. Browser rows 128
    resp = client.get("/v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31", headers=base_headers)
    save_golden("browser_rows_128.json", resp.json())

    # 7. Form new 129
    resp = client.get("/v1/forms/129/new", headers=base_headers)
    save_golden("form_new_129.json", resp.json())

    # 8. Create record
    meta_resp = client.get("/v1/meta/form/129", headers=base_headers)
    schema_version = meta_resp.json().get("schemaVersion", "18dbdf28") if meta_resp.status_code == 200 else "18dbdf28"

    create_payload = {
        "schemaVersion": schema_version,
        "header": {
            "doc_no": "SO-2026-001",
            "doc_date": "2026-03-29",
            "cust_id": 1,
            "cc_id": 1,
            "doc_total": 840000,
            "doc_remark": "[API-TEST] golden create"
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
    resp = client.post("/v1/forms/129/records", json=create_payload, headers={**base_headers, "Idempotency-Key": "goldengenerate1"})
    save_golden("create_129.json", resp.json())

    # 9. Replay record
    resp = client.post("/v1/forms/129/records", json=create_payload, headers={**base_headers, "Idempotency-Key": "goldengenerate1"})
    save_golden("replay_129.json", resp.json())

if __name__ == "__main__":
    generate()
