import json
import logging

from openai import OpenAI

from agents.retriever.agent import Source
from core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key,
)

WRITER_PROMPT = """You are a research report writer.

You will receive a list of sources. Write a clear, structured report answering the user's question.

Structure:
- Open with a short "## Summary" of 3-5 sentences stating the direct answer first.
- Then 2-5 "## Section Title" sections, each making one point.
- Close with "## Sources considered" naming any source you weighed and rejected.

Rules:
- Use markdown headings (## Section Title).
- Cite sources inline using [n] where n is the source index (1-based).
- Use markdown tables when comparing options, but never inside a sentence.
- Only use information from the provided sources. Do not invent facts.
- If sources are insufficient, say so explicitly.
- Be concise. Prefer specific findings and numbers over general description.
- Return ONLY valid JSON in this shape:
{"report": "markdown content here"}

No explanation, no code fences, just JSON.
"""


def _build_source_block(sources: list[Source]) -> str:
    lines: list[str] = []
    for i, s in enumerate(sources, 1):
        lines.append(f"[{i}] {s['title']} -- {s['url']}")
        lines.append(s.get("content", "")[:2500])
        lines.append("")
    return "\n".join(lines)


def _parse_report(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]
    text = text.strip()
    try:
        data = json.loads(text)
        report = data.get("report", "")
        if isinstance(report, str) and report.strip():
            return report
    except json.JSONDecodeError:
        pass
    return ""


def write(query: str, sources: list[Source]) -> str:
    if not sources:
        return "No sources found for this query."

    source_block = _build_source_block(sources)
    user_prompt = f"Question: {query}\n\nSources:\n{source_block}\n\nWrite the report."

    last_raw = ""
    for _ in range(3):
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": WRITER_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=8000,
        )
        last_raw = completion.choices[0].message.content
        report = _parse_report(last_raw)
        if report:
            return report
        logger.warning("writer parse failed, retrying")
        user_prompt += "\n\nReturn ONLY valid JSON. Your last output was not parseable."

    return last_raw or "No report generated."
