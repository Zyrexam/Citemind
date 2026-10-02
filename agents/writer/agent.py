import json
import logging
import re
import time

from openai import OpenAI

from agents.retriever.agent import Source
from core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key,
)

# Groq enforces input+output per minute, not per request. A full run costs the
# planner ~1k tokens and the writer ~6.8k, nearly the whole 8000 allowance, so the
# window needs a clear minute to refill before a retry stands any chance.
RATE_LIMIT_PAUSE = 65

WRITER_PROMPT = """You are a research report writer.

You will receive a list of sources. Write a clear, structured report answering the user's question.

Structure:
- Open with a short "## Summary" of 3-5 sentences stating the direct answer first.
- Then 2-5 "## Section Title" sections, each making one point.
- Close with "## Sources considered" naming any source you weighed and rejected.

Rules:
- Use markdown headings (## Section Title).
- Cite sources inline using [n] where n is the source index (1-based).
- EVERY number, date or named finding must carry a citation, including in the Summary.
  A figure with no citation is a fabrication.
- If the question assumes something the sources do not support, correct it in the first
  sentence of the Summary. Never build on a premise you could not verify. Do not soften a
  refutation into agreement.
- Do not generalise a narrow result into a broad claim. If one study reports zero errors
  under narrow conditions, say which conditions; never say a method eliminates a problem.
- If the sources disagree, report both positions rather than choosing one. State which
  position each rests on, and do not merge them into a single verdict unless the sources
  agree on the verdict.
- Use markdown tables when comparing options, but never inside a sentence.
- Only use information from the provided sources. Do not invent facts.
- If sources are insufficient, say so explicitly.
- Be concise. Prefer specific findings and numbers over general description.

Return ONLY valid JSON in this shape:
{"report": "markdown content here",
 "claims": [{"claim": "the assertion, in your own words",
             "source": 1,
             "quote": "a verbatim copy of the words in source 1 that support it"}]}

The quote is checked character-for-character against the source text you were given. Copy
it exactly, including its original wording and any numbers. Do not tidy it, do not merge
non-adjacent sentences, do not translate. If a claim rests on several sources, emit one
entry per source. Every quantified or contested claim in the report needs an entry. If you
cannot find a verbatim quote supporting a claim, cut the claim.

Put "report" first and keep the claim list to the load-bearing claims, so that a long
report does not run out of room before the quotes are written.

No explanation, no code fences, just JSON.
"""

CUT_NOTE = (
    "\n\n---\n\n_Note: the source budget was cut to fit this model's request limit, "
    "so this report draws on less evidence than was retrieved._"
)

# The model sometimes runs out of output tokens mid-JSON. The report is written
# first, so it is usually intact; a claim whose quote was never closed is dropped
# rather than guessed at.
_STR = r'((?:[^"\\]|\\.)*)'
_REPORT_RE = re.compile(r'"report"\s*:\s*"' + _STR + r'"')
_OBJECT_RE = re.compile(r"\{[^{}]*\}")


def _unescape(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        return raw


def _field(obj: str, key: str) -> str | None:
    # quote and claim are strings, source is a bare number
    m = re.search(r'"' + key + r'"\s*:\s*(?:"' + _STR + r'"|(-?\d+))', obj)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def _claims(text: str) -> list[dict]:
    out = []
    for obj in _OBJECT_RE.findall(text):
        quote = _field(obj, "quote")
        source = _field(obj, "source")
        if quote and source and source.strip().isdigit():
            out.append({
                "claim": _unescape(_field(obj, "claim") or ""),
                "source": int(source),
                "quote": _unescape(quote),
            })
    return out


def _build_source_block(sources: list[Source], budget: int) -> tuple[str, int]:
    """Render the sources into a character budget, headers included.

    Returns the block and the per-source allowance used, which the quote check
    needs: it must verify against the slice the writer saw, not the full page.
    """
    headers = [f"[{i}] {s['title']} -- {s['url']}" for i, s in enumerate(sources, 1)]
    room = max(0, budget - sum(len(h) + 2 for h in headers))
    per_source = min(settings.writer_context_chars, room // max(1, len(sources)))

    lines: list[str] = []
    for i, s in enumerate(sources, 1):
        lines.append(headers[i - 1])
        lines.append(s.get("content", "")[:per_source])
        lines.append("")
    return "\n".join(lines), per_source


def _parse(raw: str) -> tuple[str, list[dict]]:
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]

    claims = _claims(text)

    try:
        data = json.loads(text.strip())
        report = data.get("report", "")
        if isinstance(report, str) and report.strip():
            return report, claims
    except json.JSONDecodeError:
        pass

    m = _REPORT_RE.search(text)
    return (_unescape(m.group(1)), claims) if m else ("", claims)


def write(query: str, sources: list[Source], trace: dict | None = None) -> str:
    if not sources:
        return "No sources found for this query."

    budget = settings.writer_input_chars
    last_raw = ""
    cut = False
    rate_limited = False

    for _ in range(3):
        source_block, per_source = _build_source_block(sources, budget)
        user_prompt = (
            f"Question: {query}\n\nSources:\n{source_block}\n\nWrite the report."
        )
        try:
            completion = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": WRITER_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=settings.writer_max_tokens,
            )
        except Exception as e:
            if "413" not in str(e) and "rate_limit" not in str(e).lower():
                raise
            budget = budget // 2
            cut = True
            rate_limited = True
            logger.warning(
                "writer request exceeded the token budget, retrying with %d chars "
                "after a %ds pause", budget, RATE_LIMIT_PAUSE,
            )
            time.sleep(RATE_LIMIT_PAUSE)
            continue

        last_raw = completion.choices[0].message.content
        report, claims = _parse(last_raw)
        if report:
            if cut:
                report += CUT_NOTE
            if trace is not None:
                trace.update({
                    "budget": budget,
                    "per_source": per_source,
                    "cut": cut,
                    "claims": claims,
                    "tokens": getattr(completion.usage, "total_tokens", None),
                })
            return report
        logger.warning("writer returned no report, retrying")
        budget = int(budget * 0.8)

    # Falling through here used to return the literal string "No report
    # generated.", or the raw JSON, as though either were a report. A caller
    # cannot tell a failed request from an answer, so it raises instead.
    if rate_limited:
        raise RuntimeError(
            f"writer: rate limited on all 3 attempts, even at {budget} chars"
        )
    raise RuntimeError("writer: model returned no usable report on 3 attempts")