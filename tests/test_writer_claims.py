"""The writer's claim list is what the grounding check runs on."""

import json

from agents.writer import agent as writer

SOURCES = [{"title": "T", "url": "https://x.com", "content": "c", "query": "q"}]


def respond(monkeypatch, content):
    """Point the writer's client at a canned response."""
    completions = type("Completions", (), {})()
    message = type("Message", (), {"content": content})()
    choice = type("Choice", (), {"message": message})()
    completion = type("Completion", (), {"choices": [choice], "usage": None})()
    completions.create = staticmethod(lambda *a, **k: completion)
    monkeypatch.setattr(writer.client.chat, "completions", completions)


def test_write_hands_back_the_claims_the_model_emitted(monkeypatch):
    quote = "the study reported a 12% gain in recall over the baseline"
    respond(monkeypatch, json.dumps({
        "report": "## Summary\nRetrieval won by 12% [1].",
        "claims": [{"claim": "Retrieval won by 12%", "source": 1, "quote": quote}],
    }))

    trace: dict = {}
    report = writer.write("q", SOURCES, trace=trace)

    assert report == "## Summary\nRetrieval won by 12% [1]."
    assert trace["claims"] == [
        {"claim": "Retrieval won by 12%", "source": 1, "quote": quote}
    ]