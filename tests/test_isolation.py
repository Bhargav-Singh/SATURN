import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.agent_service import reset_agents
from services.audit_service import reset_audit_logs
from services.kb_service import reset_kb
from services.tool_service import reset_tools
from tests.helpers import ensure_company


def _jwt(company_id, role="admin"):
    return jwt.encode(
        {"company_id": company_id, "user_id": f"user-{company_id}", "role": role},
        "change-me",
        algorithm="HS256",
    )


def _headers(company_id):
    ensure_company(company_id)
    return {"Authorization": f"Bearer {_jwt(company_id)}"}


def test_agent_isolation_between_companies():
    reset_agents()
    reset_audit_logs()
    client = TestClient(app)
    payload = {
        "name": "Isolation Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    create = client.post("/agents", json=payload, headers=_headers("company-a"))
    agent_id = create.json()["data"]["agent_id"]

    other = client.get(f"/agents/{agent_id}", headers=_headers("company-b"))
    assert other.status_code == 404


def test_kb_isolation_between_companies():
    reset_agents()
    reset_audit_logs()
    reset_kb()
    client = TestClient(app)
    payload = {
        "name": "KB Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    create = client.post("/agents", json=payload, headers=_headers("company-a"))
    agent_id = create.json()["data"]["agent_id"]
    upload = client.post(
        f"/agents/{agent_id}/kb/upload",
        json={"filename": "notes.txt", "content": "hello world"},
        headers=_headers("company-a"),
    )
    doc_id = upload.json()["data"]["doc_id"]

    other = client.get(f"/agents/{agent_id}/kb", headers=_headers("company-b"))
    assert other.status_code == 404

    delete = client.delete(
        f"/agents/{agent_id}/kb/{doc_id}",
        headers=_headers("company-b"),
    )
    assert delete.status_code == 404


def test_tool_isolation_between_companies():
    reset_agents()
    reset_audit_logs()
    reset_tools()
    client = TestClient(app)
    tool_payload = {
        "name": "crm.create_lead",
        "type": "http",
        "description": "Create a lead",
        "input_schema": {"type": "object", "properties": {}, "required": []},
        "config": {"method": "POST", "url": "https://example.test"},
    }
    create_tool = client.post("/tools", json=tool_payload, headers=_headers("company-a"))
    tool_id = create_tool.json()["data"]["tool_id"]

    other = client.post(
        f"/tools/{tool_id}/test",
        json={"input": {}},
        headers=_headers("company-b"),
    )
    assert other.status_code in (403, 404)
