import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.agent_service import reset_agents
from services.audit_service import reset_audit_logs
from services.tool_service import reset_tools
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
        "name": "Tool Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    response = client.post("/agents", json=payload, headers=_auth_headers())
    return response.json()["data"]["agent_id"]


def _create_tool(client, schema):
    payload = {
        "name": "crm.create_lead",
        "type": "http",
        "description": "Create a lead",
        "input_schema": schema,
        "config": {"method": "POST", "url": "https://example.test"},
    }
    response = client.post("/tools", json=payload, headers=_auth_headers())
    return response.json()["data"]["tool_id"]


def test_attach_and_test_tool():
    reset_agents()
    reset_audit_logs()
    reset_tools()
    client = TestClient(app)
    agent_id = _create_agent(client)
    tool_id = _create_tool(
        client,
        {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    )
    attach_resp = client.post(
        f"/agents/{agent_id}/tools/attach",
        json={"tool_id": tool_id},
        headers=_auth_headers(),
    )
    assert attach_resp.status_code == 200

    test_resp = client.post(
        f"/tools/{tool_id}/test",
        json={"input": {"name": "Alice"}},
        headers=_auth_headers(),
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["data"]["result"]["status"] == "ok"


def test_tool_schema_validation_error():
    reset_agents()
    reset_audit_logs()
    reset_tools()
    client = TestClient(app)
    tool_id = _create_tool(
        client,
        {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"],
        },
    )
    test_resp = client.post(
        f"/tools/{tool_id}/test",
        json={"input": {"age": "bad"}},
        headers=_auth_headers(),
    )
    assert test_resp.status_code == 400
