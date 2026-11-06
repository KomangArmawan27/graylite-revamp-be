import json
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

TOKEN = create_access_token({"sub": 29, "login": "komang", "roles": ["General", "Admin"], "ccId": 1})
client = TestClient(app)
base_headers = {"Authorization": f"Bearer {TOKEN}"}
GOLDEN_DIR = r"\\wsl.localhost\Ubuntu\home\komang\project\graylite-be\tests\golden\run2"

def load_golden(filename):
    with open(os.path.join(GOLDEN_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

def mask_volatile(obj):
    if isinstance(obj, dict):
        masked = {}
        for k, v in obj.items():
            if k in ("schemaVersion", "requestId", "id", "trans_id", "doc_id", "created_date", "doc_date", "date"):
                masked[k] = "MASKED"
            else:
                masked[k] = mask_volatile(v)
        return masked
    elif isinstance(obj, list):
        return [mask_volatile(item) for item in obj]
    else:
        return obj

def test_golden_menu():
    golden = load_golden("menu.json")
    resp = client.get("/v1/menu", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)

def test_golden_browser_meta():
    golden = load_golden("browser_meta_128.json")
    resp = client.get("/v1/meta/browser/128", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)

def test_golden_form_meta():
    golden = load_golden("form_meta_129.json")
    resp = client.get("/v1/meta/form/129", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)

def test_golden_grid_meta():
    golden = load_golden("grid_meta_132.json")
    resp = client.get("/v1/meta/grid/132", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)

def test_golden_picker_meta():
    golden = load_golden("picker_meta_803.json")
    resp = client.get("/v1/meta/picker/803", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)

def test_golden_form_new():
    golden = load_golden("form_new_129.json")
    resp = client.get("/v1/forms/129/new", headers=base_headers)
    assert resp.status_code == 200
    assert mask_volatile(resp.json()) == mask_volatile(golden)
