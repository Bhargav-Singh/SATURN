import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.agent_service import reset_agents
from services.audit_service import reset_audit_logs
from services.kb_service import reset_kb
from tests.helpers import ensure_company


def _auth_headers():
    ensure_company("company-1")
    token = jwt.encode(
        {"company_id": "company-1", "user_id": "user-1", "role": "admin"},
        "change-me",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _create_agent(client):
    payload = {
        "name": "KB Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
        "rag_config": {"enabled": True, "top_k": 2},
    }
    response = client.post("/agents", json=payload, headers=_auth_headers())
    return response.json()["data"]["agent_id"]


def test_kb_upload_list_delete_reindex():
    reset_agents()
    reset_audit_logs()
    reset_kb()
    client = TestClient(app)
    agent_id = _create_agent(client)

    upload = client.post(
        f"/agents/{agent_id}/kb/upload",
        json={"filename": "faq.txt", "content": "hello\n\nworld"},
        headers=_auth_headers(),
    )
    assert upload.status_code == 200
    doc_id = upload.json()["data"]["doc_id"]

    listing = client.get(f"/agents/{agent_id}/kb", headers=_auth_headers())
    assert listing.status_code == 200
    assert any(doc["doc_id"] == doc_id for doc in listing.json()["data"]["documents"])

    reindex = client.post(f"/agents/{agent_id}/kb/{doc_id}/reindex", headers=_auth_headers())
    assert reindex.status_code == 200
    assert reindex.json()["data"]["status"] == "ready"

    delete = client.delete(f"/agents/{agent_id}/kb/{doc_id}", headers=_auth_headers())
    assert delete.status_code == 200
    assert delete.json()["data"]["status"] == "deleted"
