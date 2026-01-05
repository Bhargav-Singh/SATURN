from fastapi.testclient import TestClient

from app.main import app


def test_health_includes_request_id():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert "request_id" in body["meta"]
