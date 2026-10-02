import json
import logging

from openai import OpenAI

from core import search_cache
from core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key,
)

# shares the search cache; the planner rephrases between runs
PLAN_DEPTH = "plan"

PLANNER_PROMPT = """You are a research planning assistant.

Your job: Break down the user's question into 6 to 8 focused search queries.

Rules:
- Phrase each query like a Google Scholar search: name the specific method,
  system or dataset under discussion, and include a year where recency matters.
- Queries should be diverse and cover different angles of the topic.
- Return ONLY a JSON array of strings. No explanation.

Example output:
["query 1", "query 2", "query 3"]
"""


def plan(query: str) -> list[str]:
    cached = search_cache.get(query, 0, PLAN_DEPTH)
    if cached:
        queries = [r.get("query", "") for r in cached]
        logger.info("plan cache hit for: %s (%d queries)", query[:60], len(queries))
        return queries[: settings.sub_queries]

    completion = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    raw = completion.choices[0].message.content.strip()
    queries = _parse(raw, query)

    search_cache.store(query, PLAN_DEPTH, [{"query": q} for q in queries])
    return queries[: settings.sub_queries]


def _parse(raw: str, query: str) -> list[str]:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
            return parsed[:8]
    except json.JSONDecodeError:
        pass

    return [query]