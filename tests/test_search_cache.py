"""The cache must not change what a run sees.

The settings A/B is only meaningful if both arms read the same pool, which
rests on one property: slicing the first N of a wide fetch equals what a
dedicated N-result fetch would have returned. These tests pin that down.
"""

import pytest

from core import search_cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(search_cache, "ROOT", tmp_path / ".cache")
    monkeypatch.setenv("CITEMIND_CACHE", "1")
    return tmp_path / ".cache"


def results(n, tag="a"):
    return [{"url": f"https://example.com/{tag}{i}", "title": f"{tag}{i}"}
            for i in range(n)]


def test_miss_when_cache_holds_fewer_than_requested(isolated_cache):
    search_cache.store("rag chunking", "advanced", results(3))
    assert search_cache.get("rag chunking", 5, "advanced") is None
    assert search_cache.get("rag chunking", 3, "advanced") is not None


def test_slice_of_wide_fetch_equals_narrow_fetch(isolated_cache):
    """The property the A/B rests on."""
    search_cache.store("rag chunking", "advanced", results(5))

    wide = search_cache.get("rag chunking", 5, "advanced")
    narrow = search_cache.get("rag chunking", 3, "advanced")

    assert narrow == wide[:3]
    assert [r["url"] for r in narrow] == [
        "https://example.com/a0", "https://example.com/a1", "https://example.com/a2",
    ]


def test_refetch_keeps_existing_entries_in_front(isolated_cache):
    """A later wider fetch must not reshuffle what an earlier narrow run saw."""
    search_cache.store("q", "advanced", results(3))
    before = search_cache.get("q", 3, "advanced")

    search_cache.store("q", "advanced", results(5, tag="b"))
    after = search_cache.get("q", 3, "advanced")

    assert after == before


def test_key_is_stable_across_spacing_and_case(isolated_cache):
    search_cache.store("RAG   Chunking", "advanced", results(5))
    assert search_cache.get("rag chunking", 5, "advanced") is not None


def test_key_separates_depths(isolated_cache):
    search_cache.store("q", "advanced", results(5))
    assert search_cache.get("q", 5, "basic") is None


def test_planner_plan_round_trips(isolated_cache):
    plan = [{"query": "rag chunking"}, {"query": "context precision"}]
    search_cache.store("When does RAG beat fine-tuning?", "plan", plan)

    got = search_cache.get("When does RAG beat fine-tuning?", 0, "plan")
    assert [r["query"] for r in got] == ["rag chunking", "context precision"]


def test_max_results_zero_returns_everything_stored(isolated_cache):
    search_cache.store("q", "advanced", results(5))
    assert len(search_cache.get("q", 0, "advanced")) == 5


def test_disabled_cache_never_hits(isolated_cache, monkeypatch):
    search_cache.store("q", "advanced", results(5))
    monkeypatch.setenv("CITEMIND_CACHE", "0")
    assert search_cache.get("q", 5, "advanced") is None


def test_corrupt_entry_is_a_miss_not_a_crash(isolated_cache):
    search_cache.store("q", "advanced", results(5))
    path = next(isolated_cache.rglob("*.json"))
    path.write_text("{not json", encoding="utf-8")
    assert search_cache.get("q", 5, "advanced") is None
