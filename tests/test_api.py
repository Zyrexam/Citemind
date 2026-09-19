from fastapi.testclient import TestClient

from apps.api import routes
from apps.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_agent_run_stub(monkeypatch):
    class FakeMessage:
        content = "fake report"

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletions:
        @staticmethod
        def create(*args, **kwargs):
            return type("Completion", (), {"choices": [FakeChoice()]})()

    monkeypatch.setattr(routes.client.chat, "completions", FakeCompletions())

    r = client.post("/agent/run", json={"query": "What is RAG?"})
    assert r.status_code == 200
    body = r.json()
    assert body["report"] == "fake report"
    assert body["query"] == "What is RAG?"
