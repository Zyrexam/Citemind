import json

from openai import OpenAI

from core.config import settings

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key,
)

PLANNER_PROMPT = """You are a research planning assistant.

Your job: Break down the user's question into 3 to 5 focused search queries.

Rules:
- Each query should be phrased like a search engine query.
- Queries should be diverse and cover different angles of the topic.
- Return ONLY a JSON array of strings. No explanation.

Example output:
["query 1", "query 2", "query 3"]
"""


def plan(query: str) -> list[str]:
    """Break a research question into focused search queries."""
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

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        queries = json.loads(raw)
        if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
            return queries[:5]
    except json.JSONDecodeError:
        pass

    return [query]