import hashlib
import jwt
from fastapi.testclient import TestClient

from app.main import app
from models.core import ApiKey
from db.session import session_scope
from tests.helpers import ensure_company


def _set_env(monkeypatch, key, value):
    monkeypatch.setenv(key, value)


def test_auth_me_with_jwt(monkeypatch):
    _set_env(monkeypatch, "SATURN_JWT_SECRET", "test-secret")
    ensure_company("company-1")
    token = jwt.encode(
        {"company_id": "company-1", "user_id": "user-1", "role": "admin"},
        "test-secret",
        algorithm="HS256",
    )
    client = TestClient(app)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["company_id"] == "company-1"
    assert body["data"]["user_id"] == "user-1"
    assert body["meta"]["request_id"]


def test_auth_api_key(monkeypatch):
    token = "sk_test_123"
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ensure_company("company-2")
    with session_scope() as session:
        session.add(
            ApiKey(
                id="api-key-1",
                company_id="company-2",
                name="test",
                key_hash=token_hash,
                scopes=["chat:write"],
                status="active",
            )
        )
    client = TestClient(app)
    response = client.get("/auth/api-key", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["company_id"] == "company-2"
    assert "chat:write" in body["data"]["scopes"]
