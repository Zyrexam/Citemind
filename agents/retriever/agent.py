import logging
from typing import TypedDict

from core.config import settings

logger = logging.getLogger(__name__)


class Source(TypedDict):
    title: str
    url: str
    content: str
    query: str


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


def retrieve(queries: list[str], max_results: int = 6) -> list[Source]:
    client = _get_client()
    if client is None:
        return []
    results: list[Source] = []
    seen: set[str] = set()
    for q in queries:
        try:
            resp = client.search(
                query=q,
                max_results=max_results,
                search_depth="advanced",
                include_answer=False,
            )
        except Exception as e:
            logger.warning("tavily search failed for '%s': %s", q[:60], e)
            continue
        for r in resp.get("results", []):
            url = r.get("url") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("content", ""),
                    "query": q,
                }
            )
        logger.info("retrieved %d results for: %s", len(resp.get("results", [])), q[:60])
    return results
