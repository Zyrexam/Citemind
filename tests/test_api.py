from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_agent_run_stub():
    r = client.post("/agent/run", json={"query": "What is RAG?"})
    assert r.status_code == 200
    body = r.json()
    assert "report" in body
    assert body["query"] == "What is RAG?"
