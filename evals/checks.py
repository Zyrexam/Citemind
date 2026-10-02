"""Shared helpers for report verification. No LLM calls."""

import json
import re

from core.urls import canonical_url

CITE_RE = re.compile(r"[【\[]\s*(\d{1,2})\s*(?:†[^】\]]*)?[】\]]")

# headings, table rows, sources list
_STRUCT = re.compile(r"^\s*(?:#{1,6}\s|>|\|).*$", re.M)
_MD = re.compile(r"(\*\*|__|`|\[([^\]]*)\]\([^)]*\))")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z【\[*])|\n+")

DATE_RE = re.compile(r"\b(19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
PROPER_RE = re.compile(r"(?<![.!?]\s)\b[A-Z][a-z]{2,}\b")


def strip_markdown(md: str) -> str:
    return _MD.sub(" ", md)


def split_sentences(text: str) -> list[str]:
    """Prose sentences only; headings and table rows dropped."""
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
    # the trailing \b belongs to the word alternatives only. Inside the group,
    # "43% whenever" fails - % and the space after it are both non-word
    r"\b\d[\d,.]*(?:\s*(?:%|percent|x|ms|s|bn|b|m|k|gb|mb|billion|million|thousand)\b|\s*%)",
    re.I,
)


def has_quantified_claim(sentence: str) -> bool:
    """A sentence stating a measured quantity. Must carry a citation."""
    return bool(QUANT_RE.search(sentence))


def has_named_claim(sentence: str) -> bool:
    """A sentence naming a study, system or org. Weaker signal than a quantity."""
    return bool(DATE_RE.search(sentence) or ACRONYM_RE.search(sentence)
                or PROPER_RE.search(sentence))


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
    """True if the report declines to answer."""
    head = split_sentences(text)[:4]
    return any(REFUSAL_RE.search(s) for s in head)


def load_report(path: str) -> dict:
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
