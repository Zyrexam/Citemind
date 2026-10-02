import logging
from typing import TypedDict

from core import search_cache
from core.config import settings
from core.urls import canonical_url

logger = logging.getLogger(__name__)

DEPTH = "advanced"


class Source(TypedDict):
    title: str
    url: str
    content: str
    query: str
    published_date: str


_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from tavily import TavilyClient

        if settings.tavily_api_key:
            _client = TavilyClient(api_key=settings.tavily_api_key)
        else:
            _client = TavilyClient()
            logger.info("tavily running in keyless mode")
    except Exception as e:
        logger.warning("tavily client init failed: %s", e)
        _client = None
    return _client


def _search(client, q: str, max_results: int) -> list[dict]:
    """Results for one query, from the cache when it holds enough of them.

    The cache answers only if it can serve the full requested count; a partial
    hit would silently change which sources a run sees.
    """
    hit = search_cache.get(q, max_results, DEPTH)
    if hit is not None:
        logger.info("cache hit for: %s (%d results)", q[:60], len(hit))
        return hit

    resp = client.search(
        query=q,
        max_results=max_results,
        search_depth=DEPTH,
        include_answer=False,
    )
    fresh = resp.get("results", [])
    # Stored before dedupe: the cache is the raw pool, and the canonical-URL
    # dedupe below is a retrieval-time concern that a wider run may resolve
    # differently.
    search_cache.store(q, DEPTH, fresh)
    return search_cache.get(q, max_results, DEPTH) or fresh[:max_results]


def retrieve(queries: list[str], max_results: int = 6) -> list[Source]:
    client = _get_client()
    if client is None:
        return []
    results: list[Source] = []
    seen: set[str] = set()
    for q in queries:
        try:
            raw = _search(client, q, max_results)
        except Exception as e:
            logger.warning("tavily search failed for '%s': %s", q[:60], e)
            continue
        for r in raw:
            url = r.get("url") or ""
            key = canonical_url(url)
            if not key or key in seen:
                continue
            seen.add(key)
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("content", ""),
                    "query": q,
                    "published_date": r.get("published_date") or "",
                }
            )
        logger.info("retrieved %d results for: %s", len(raw), q[:60])
    return results
