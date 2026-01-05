import jwt
from fastapi.testclient import TestClient

from app.main import app
from common.metrics import reset_metrics
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


def test_metrics_counts_requests_and_llm_calls():
    reset_metrics()
    reset_agents()
    reset_audit_logs()
    client = TestClient(app)
    payload = {
        "name": "Metrics Agent",
        "type": "chat",
        "status": "active",
        "model_config": {"provider": "openai", "model": "gpt-test"},
        "behavior_config": {"system_prompt": "hi"},
    }
    client.post("/agents", json=payload, headers=_auth_headers())
    client.post("/agents/invalid/chat", json={"message": "hi"}, headers=_auth_headers())
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    data = metrics.json()["data"]
    assert data["request_count"] >= 2
    assert "avg_latency_ms" in data
