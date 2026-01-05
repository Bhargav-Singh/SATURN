import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.agent_service import reset_agents
from services.audit_service import reset_audit_logs
from tests.helpers import ensure_company


def _auth_headers():
    ensure_company("company-1")
    token = jwt.encode(
        {"company_id": "company-1", "user_id": "user-1", "role": "admin"},
        "change-me",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_agent():
    reset_agents()
    reset_audit_logs()
    client = TestClient(app)
    payload = {
        "name": "Test Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    create_resp = client.post("/agents", json=payload, headers=_auth_headers())
    assert create_resp.status_code == 200
    agent_id = create_resp.json()["data"]["agent_id"]

    get_resp = client.get(f"/agents/{agent_id}", headers=_auth_headers())
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["data"]["agent_id"] == agent_id
    assert body["data"]["version"] == 1


def test_update_agent_increments_version():
    reset_agents()
    reset_audit_logs()
    client = TestClient(app)
    payload = {
        "name": "Update Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    create_resp = client.post("/agents", json=payload, headers=_auth_headers())
    agent_id = create_resp.json()["data"]["agent_id"]

    update_resp = client.patch(
        f"/agents/{agent_id}", json={"name": "Updated"}, headers=_auth_headers()
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["version"] == 2


def test_list_agents_by_type():
    reset_agents()
    reset_audit_logs()
    client = TestClient(app)
    payload = {
        "name": "Voice Agent",
        "type": "voice",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    client.post("/agents", json=payload, headers=_auth_headers())
    list_resp = client.get("/agents?type=voice", headers=_auth_headers())
    assert list_resp.status_code == 200
    agents = list_resp.json()["data"]["agents"]
    assert any(agent["type"] == "voice" for agent in agents)
