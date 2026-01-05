from datetime import datetime, timezone

import jwt
from fastapi.testclient import TestClient

from app.main import app
from services.billing_service import reset_invoices
from services.usage_service import record_usage_event, reset_usage_events
from tests.helpers import ensure_company


def _auth_headers():
    ensure_company("company-1")
    token = jwt.encode(
        {"company_id": "company-1", "user_id": "user-1", "role": "admin"},
        "change-me",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _current_period():
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


def _create_agent(client):
    payload = {
        "name": "Billing Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    response = client.post("/agents", json=payload, headers=_auth_headers())
    return response.json()["data"]["agent_id"]


def test_generate_invoice_and_summary():
    reset_invoices()
    reset_usage_events()
    client = TestClient(app)
    agent_id = _create_agent(client)
    record_usage_event("company-1", agent_id, None, "llm_tokens_in", 100, "tokens")
    record_usage_event("company-1", agent_id, None, "kb_query", 2, "calls")

    period = _current_period()
    summary = client.get(f"/usage/summary?period={period}", headers=_auth_headers())
    assert summary.status_code == 200
    assert summary.json()["data"]["tokens_in"] == 100
    assert summary.json()["data"]["kb_queries"] == 2

    generate = client.post(f"/invoices/generate?period={period}", headers=_auth_headers())
    assert generate.status_code == 200
    invoice_id = generate.json()["data"]["invoice_id"]

    fetch = client.get(f"/invoices/{invoice_id}", headers=_auth_headers())
    assert fetch.status_code == 200
    assert fetch.json()["data"]["status"] == "draft"
