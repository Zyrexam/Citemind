"""On-disk cache for search results, keyed by query.

A settings A/B is only meaningful if both arms read the same evidence, so a hit
is served only when it holds at least N results, and a fresh fetch merges behind
what is stored rather than replacing it. That keeps the list prefix-stable:
slicing the first 3 gives what a dedicated 3-result fetch would have returned.
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1] / ".cache"
_WS = re.compile(r"\s+")


def enabled() -> bool:
    return os.environ.get("CITEMIND_CACHE", "1").strip().lower() not in {"0", "off", "false"}


def _key(query: str, depth: str) -> str:
    """Same question, spacing and depth -> same key.

    The planner rephrases the same query across runs, so hash normalised text.
    """
    norm = _WS.sub(" ", query.strip().lower())
    h = hashlib.sha256(f"{depth}\x00{norm}".encode()).hexdigest()[:20]
    return h


def _path(query: str, depth: str) -> Path:
    return ROOT / depth / f"{_key(query, depth)}.json"


def get(query: str, max_results: int, depth: str) -> list[dict] | None:
    """Cached results for this query, or None if it cannot satisfy the request.

    max_results=0 means "whatever is stored", for callers that cache a list
    rather than a ranked result page.
    """
    if not enabled():
        return None
    path = _path(query, depth)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    results = data.get("results") or []
    if max_results <= 0:
        return results or None
    if len(results) < max_results:
        return None
    return results[:max_results]


def store(query: str, depth: str, fresh: list[dict]) -> list[dict]:
    """Merge a fetch into the cache and return the merged pool.

    Existing entries keep their positions so a later narrow slice still
    reproduces what a narrow fetch would have returned.
    """
    path = _path(query, depth)
    pooled: list[dict] = []
    seen: set[str] = set()

    if path.exists():
        try:
            pooled = json.loads(path.read_text(encoding="utf-8")).get("results") or []
        except (json.JSONDecodeError, OSError):
            pooled = []

    for r in pooled + fresh:
        # Tavily entries are keyed by url, planner entries by query. Dedupe on
        # url alone would collapse a replayed plan to a single sub-query.
        key = r.get("url") or r.get("query") or json.dumps(
            r, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        pooled.append(r)

    if enabled():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"query": query, "depth": depth, "results": pooled},
                       ensure_ascii=False),
            encoding="utf-8",
        )
    return pooled


def stats() -> tuple[int, int]:
    """(cached queries, cached results) across every depth."""
    queries = results = 0
    if not ROOT.exists():
        return 0, 0
    for path in ROOT.rglob("*.json"):
        queries += 1
        try:
            results += len(json.loads(path.read_text(encoding="utf-8")).get("results") or [])
        except (json.JSONDecodeError, OSError):
            pass
    return queries, results
