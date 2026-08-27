import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_analyze_endpoint():
    payload = {
        "transaction_id": "tx_test_01",
        "raw_text": "URGENT: Please wire $2,500 immediately to account 987654321 to claim your lottery prize!" # u can use your own
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "tx_test_01"
    assert "$2,500" in data["sanitized_text"]
    assert "[ACCOUNT_REDACTED]" in data["sanitized_text"]
    assert "risk_level" in data