import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.agent_service import reset_agents
from services.audit_service import reset_audit_logs
from services.kb_service import reset_kb
from services.session_service import reset_sessions
from services.usage_service import list_usage_events, reset_usage_events
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
        "name": "Usage Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
        "rag_config": {"enabled": True, "top_k": 1},
    }
    response = client.post("/agents", json=payload, headers=_auth_headers())
    return response.json()["data"]["agent_id"]


def test_usage_events_created_for_chat():
    reset_agents()
    reset_audit_logs()
    reset_kb()
    reset_sessions()
    reset_usage_events()
    client = TestClient(app)
    agent_id = _create_agent(client)
    client.post(
        f"/agents/{agent_id}/kb/upload",
        json={"filename": "notes.txt", "content": "hello world"},
        headers=_auth_headers(),
    )
    response = client.post(
        f"/agents/{agent_id}/chat",
        json={"message": "hello"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    events = list_usage_events("company-1")
    event_types = {event.event_type for event in events}
    assert "llm_tokens_in" in event_types
    assert "llm_tokens_out" in event_types
    assert "kb_query" in event_types
