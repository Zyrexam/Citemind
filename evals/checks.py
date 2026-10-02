"""Shared deterministic helpers for report verification.

No LLM calls anywhere in this module or its importers. Every check is a
reproducible function of the report text and the source list.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.urls import canonical_url  # noqa: E402

CITE_RE = re.compile(r"[【\[]\s*(\d{1,2})\s*(?:†[^】\]]*)?[】\]]")

# structural lines carry no claims: headings, table rows, the sources-considered list
_STRUCT = re.compile(r"^\s*(?:#{1,6}\s|>|\|).*$", re.M)
_MD = re.compile(r"(\*\*|__|`|\[([^\]]*)\]\([^)]*\))")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z【\[*])|\n+")

DATE_RE = re.compile(r"\b(19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
PROPER_RE = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b")


def strip_markdown(md: str) -> str:
    return _MD.sub(" ", md)


def split_sentences(text: str) -> list[str]:
    """Prose sentences only.

    Headings, table rows and the sources-considered list are dropped first: they
    are structural, and checking them produces false positives.
    """
    out = []
    for chunk in _SENT.split(strip_markdown(_STRUCT.sub(" ", text))):
        cleaned = chunk.strip(" -*•\t")
        if not cleaned or cleaned.lower().startswith("rejected:"):
            continue
        out.append(cleaned)
    return out


def citations_in(text: str) -> list[int]:
    return [int(m.group(1)) for m in CITE_RE.finditer(text)]


QUANT_RE = re.compile(
    # The trailing \b belongs to the word alternatives only. After the group it
    # failed to match -- % and the following space are both non-word, so there is
    # no boundary to assert -- and every percentage in every report slipped past.
    r"\b\d[\d,.]*(?:\s*(?:%|percent|x|ms|s|bn|b|m|k|gb|mb|billion|million|thousand)\b|\s*%)",
    re.I,
)


def has_quantified_claim(sentence: str) -> bool:
    """A sentence stating a measured quantity. These must carry a citation.

    This is where fabrication shows up, so it is the strict tier. A bare year
    or a study name is not enough on its own.
    """
    return bool(QUANT_RE.search(sentence))


def has_named_claim(sentence: str) -> bool:
    """A sentence naming a specific study, system, or organisation.

    Weaker signal. Naming something is not the same as asserting a fact about
    it, so a missing citation here is worth reading, not necessarily an error.
    """
    body = sentence.split(" ", 1)[1] if " " in sentence else sentence
    return bool(DATE_RE.search(sentence) or ACRONYM_RE.search(sentence) or PROPER_RE.search(body))


REFUSAL_RE = re.compile(
    r"cannot be (?:determined|answered|stated|derived|established|known|found)"
    r"|can(?:not|'t) be answered"
    r"|unable to (?:answer|determine|establish)"
    r"|insufficient (?:evidence|information|sources|context)"
    r"|sources? (?:are|were) insufficient"
    r"|(?:sources|evidence|materials?|documents?|passages?|context)\s+"
    r"(?:do|does|did)\s+not\s+(?:provide|contain|include|specify|mention|support|offer)"
    r"|(?:is|are) not (?:provided|available|specified|reported|discussed) in any of the"
    r"|no (?:information|data|specific) (?:about|on) (?:this|that|it)",
    re.I,
)


def looks_like_refusal(text: str) -> bool:
    """True if the report declines to answer rather than answering.

    An answerable question that gets this treatment is a failure even when every
    structural check passes. Matches the body only, so a report citing this
    phrasing while discussing it is not counted.
    """
    head = split_sentences(text)[:4]
    return any(REFUSAL_RE.search(s) for s in head)


def load_report(path: str) -> dict:
    import json
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def report_text(data: dict) -> str:
    return data.get("report", "") if isinstance(data, dict) else str(data)


def source_list(data: dict) -> list[dict]:
    return data.get("citations", []) if isinstance(data, dict) else []


__all__ = [
    "CITE_RE", "canonical_url", "citations_in",
    "has_named_claim", "has_quantified_claim", "load_report", "looks_like_refusal",
    "report_text", "split_sentences", "source_list", "strip_markdown",
]
