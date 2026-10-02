"""The four pieces that were each wrong at least once."""

import json

import pytest

from agents.writer import agent as writer
from core import search_cache
from core.urls import canonical_url
from evals.checks import has_named_claim


def test_write_hands_back_the_claims_the_model_emitted(monkeypatch):
    quote = "the study reported a 12% gain in recall over the baseline"
    message = type("Message", (), {"content": json.dumps({
        "report": "## Summary\nRetrieval won by 12% [1].",
        "claims": [{"claim": "Retrieval won by 12%", "source": 1, "quote": quote}],
    })})()
    choice = type("Choice", (), {"message": message})()
    completion = type("Completion", (), {"choices": [choice], "usage": None})()
    completions = type("Completions", (), {})()
    completions.create = staticmethod(lambda *a, **k: completion)
    monkeypatch.setattr(writer.client.chat, "completions", completions)

    trace: dict = {}
    sources = [{"title": "T", "url": "https://x.com", "content": "c", "query": "q"}]
    report = writer.write("q", sources, trace=trace)

    assert report == "## Summary\nRetrieval won by 12% [1]."
    assert trace["claims"] == [
        {"claim": "Retrieval won by 12%", "source": 1, "quote": quote}
    ]


def test_old_style_arxiv_versions_collapse():
    """hep-th/9901001 -- every pre-2007 id carries a category slash."""
    assert canonical_url("https://arxiv.org/abs/hep-th/9901001v1") == canonical_url(
        "https://arxiv.org/abs/hep-th/9901001v2"
    )


@pytest.mark.parametrize(
    "sentence, named",
    [
        ("Smith et al. showed a 12% gain.", True),
        ("retrieval is a technique that combines search and generation", False),
    ],
)
def test_named_claim_detection(sentence, named):
    assert has_named_claim(sentence) is named


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(search_cache, "ROOT", tmp_path / ".cache")
    monkeypatch.setenv("CITEMIND_CACHE", "1")
    return tmp_path / ".cache"


def test_slice_of_wide_fetch_equals_narrow_fetch(isolated_cache):
    """The property the settings A/B rests on."""
    results = [{"url": f"https://example.com/{i}", "title": str(i)}
               for i in range(5)]
    search_cache.store("rag chunking", "advanced", results)

    wide = search_cache.get("rag chunking", 5, "advanced")
    narrow = search_cache.get("rag chunking", 3, "advanced")
    assert narrow == wide[:3]


def test_corrupt_entry_is_a_miss_not_a_crash(isolated_cache):
    search_cache.store("q", "advanced", [{"url": "https://x.com"}])
    path = next(isolated_cache.rglob("*.json"))
    path.write_text("{not json", encoding="utf-8")
    assert search_cache.get("q", 1, "advanced") is None