import pytest

from app.core.config import settings
from app.core.deps import get_current_user
from app.main import app


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "login": "admin", "roles": ["Admin"], "ccId": 1}
    yield
    app.dependency_overrides.clear()

def test_writes_disabled_default(client):
    settings.ENABLE_WRITES = False
    response = client.post("/v1/forms/129/records", json={"header": {}})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"

def test_role_check_fail_closed_no_browser(client):
    settings.ENABLE_WRITES = True
    from unittest.mock import patch
    with patch("app.modules.form.router.meta_service.can_add", return_value=False):
        response = client.post(
            "/v1/forms/129/records",
            json={"header": {}, "schemaVersion": "123"},
            headers={"Idempotency-Key": "validkey123"}
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "forbidden"
    settings.ENABLE_WRITES = False

def test_idempotency_store_logic():
    from app.core.cache import InMemoryIdempotencyStore, Replay
    store = InMemoryIdempotencyStore()
    
    res = store.begin("key1", 1, "/v1/test", "hash1")
    store.finish("key1", 1, "/v1/test", "hash1", 200, b"success", {"Content-Type": "application/json"})
    
    replay = store.begin("key1", 1, "/v1/test", "hash1")
    assert isinstance(replay, Replay)
    assert replay.status == 200
    assert replay.body == b"success"
    
    conflict = store.begin("key1", 1, "/v1/test", "hash2")
    assert conflict == "conflict_body"

def test_create_record_success_scenario(client):
    settings.ENABLE_WRITES = True
    
    from unittest.mock import MagicMock, patch

    from app.core.db import get_db_write

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.first.return_value = (222,)
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db_write] = lambda: mock_session
    
    with patch("app.modules.form.router.meta_service.can_add", return_value=True), \
         patch("app.modules.form.router.meta_service.get_form_meta", return_value={"schemaVersion": "18dbdf28", "idField": "doc_id", "grids": {}}), \
         patch("app.modules.form.router.meta_service.get_screen", return_value={"hdr_basetable": "[Sales].[Order]", "hdr_id": 129}), \
         patch("app.modules.form.router.get_form_record", return_value={"header": {"doc_id": 222, "doc_no": "SO-2026-001"}, "grids": {"132": {"rows": []}}, "schemaVersion": "18dbdf28"}):
        
        response = client.post(
            "/v1/forms/129/records",
            json={
                "schemaVersion": "18dbdf28",
                "header": {
                    "doc_no": "SO-2026-001",
                    "doc_date": "2026-03-29",
                    "cust_id": 1,
                    "cc_id": 1,
                    "doc_total": 840000,
                    "doc_remark": "Test Sales Order"
                }
            },
            headers={"Idempotency-Key": "successkey123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["header"]["doc_id"] == 222
        assert data["header"]["doc_no"] == "SO-2026-001"
        
        # Test Idempotent Replay
        response_replay = client.post(
            "/v1/forms/129/records",
            json={
                "schemaVersion": "18dbdf28",
                "header": {
                    "doc_no": "SO-2026-001",
                    "doc_date": "2026-03-29",
                    "cust_id": 1,
                    "cc_id": 1,
                    "doc_total": 840000,
                    "doc_remark": "Test Sales Order"
                }
            },
            headers={"Idempotency-Key": "successkey123"}
        )
        assert response_replay.status_code == 200
        assert response_replay.headers.get("Idempotent-Replay") == "true"

    app.dependency_overrides.clear()
    settings.ENABLE_WRITES = False


