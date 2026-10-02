"""Verify each claim is backed by a quote that occurs in its passage. No judge.

    python -m evals.verify_grounding path/to/report.json
"""

import re
import sys

from evals.checks import load_report, source_list

# typography the model gets wrong, plus the elision it uses for long quotes
_FOLD = str.maketrans({
    "‐": "-", "‑": "-", "‒": "-", "–": "-",
    "—": "-", "―": "-", "−": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...",
})
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")

# under this a match proves nothing: "measured separately" is in every RAG paper
MIN_QUOTE_WORDS = 8

_WORD = re.compile(r"\w")


def normalise(text: str) -> str:
    text = text.translate(_FOLD).lower()
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def quote_found(quote: str, haystack: str) -> bool:
    """True if the quote occurs in the passage. Split before normalising."""
    hay = normalise(haystack)
    if normalise(quote) in hay:
        return True

    fragments = [f for f in re.split(r"\.\.\.|…", quote)
                 if len(normalise(f).split()) > 1]
    if not fragments:
        return False
    return all(normalise(f) in hay for f in fragments)


def _ends_at_word_boundary(needle: str, hay: str) -> bool:
    """True if some occurrence of `needle` ends on a word boundary."""
    start, width = 0, len(needle)
    while True:
        i = hay.find(needle, start)
        if i < 0:
            return False
        tail = hay[i + width: i + width + 1]
        if not tail or not _WORD.match(tail):
            return True
        start = i + 1


def quote_defects(quote: str, haystack: str) -> list[str]:
    """Ways a quote can occur and still be worthless. Needs quote_found to pass."""
    defects = []

    words = len(normalise(quote).split())
    if words < MIN_QUOTE_WORDS:
        defects.append(f"quote-too-short ({words} words, minimum {MIN_QUOTE_WORDS})")

    frags = [f for f in re.split(r"\.\.\.|…", quote) if normalise(f)] or [quote]
    tail = normalise(frags[-1])
    if tail and not _ends_at_word_boundary(tail, normalise(haystack)):
        defects.append(f"quote-cut-mid-word (ends on '{tail.split()[-1]}')")

    return defects


def verify(path: str) -> int:
    data = load_report(path)
    sources = source_list(data)
    meta = data.get("_meta", {}) if isinstance(data, dict) else {}
    claims = (meta.get("writer") or {}).get("claims", [])
    per_source = (meta.get("writer") or {}).get("per_source")
    total = len(sources)

    if not claims:
        print(f"file                {path}\n"
              f"claims              0 -- the writer returned no claim list, "
              f"so nothing can be verified.\n")
        return 1

    failures: list[tuple[str, str]] = []
    verbatim = 0
    usable = 0
    for c in claims:
        try:
            n = int(c["source"])
        except (TypeError, ValueError):
            failures.append(("quote-out-of-range", f"source {c['source']!r} is not a number"))
            continue
        if n < 1 or n > total:
            failures.append(("quote-out-of-range",
                             f"claim cites source [{n}] but there are {total} sources"))
            continue

        passage = sources[n - 1].get("content", "")
        if per_source:
            passage = passage[:per_source]
        if not quote_found(c["quote"], passage):
            failures.append((
                "quote-not-found",
                f"[{n}] {c['claim'][:90]}\n      quoted: {c['quote'][:110]}",
            ))
            continue

        verbatim += 1
        defects = quote_defects(c["quote"], passage)
        if defects:
            failures.append((
                defects[0].split(" ")[0],
                f"[{n}] {c['claim'][:90]}\n      {defects[0]}",
            ))
            continue
        usable += 1

    print(f"file                {path}")
    print(f"sources             {total}")
    print(f"claims              {len(claims)}")
    print(f"quotes verbatim     {verbatim}/{len(claims)} "
          f"({100 * verbatim // max(1, len(claims))}%)")
    print(f"quotes usable       {usable}/{len(claims)} "
          f"({100 * usable // max(1, len(claims))}%)  "
          f"verbatim, >= {MIN_QUOTE_WORDS} words, ends on a word boundary")
    if per_source:
        print(f"verified against    first {per_source} chars of each source")
    print()

    if failures:
        for kind, detail in failures[:12]:
            print(f"[{kind}] {detail}")
        if len(failures) > 12:
            print(f"... {len(failures) - 12} more")
        print()
        print(f"FAIL - {len(failures)} claim(s) not backed by a usable verbatim quote.")
        return 1

    print("PASS - every claim has a quote that occurs in its cited passage.")
    print("NOTE: this proves the quote exists, not that it supports the claim.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(verify(sys.argv[1]))