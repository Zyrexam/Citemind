"""Structural checks on a finished report. No LLM calls.

    python -m evals.verify_report path/to/report.json
"""

import sys

from evals.checks import (
    canonical_url,
    citations_in,
    has_named_claim,
    has_quantified_claim,
    load_report,
    report_text,
    source_list,
    split_sentences,
)

# failures that indicate a claim the sources do not support. The rest are
# failures that mean a claim the sources do not support. The rest are
# reading prompts, not proven errors.
HARD = {"citation-out-of-range", "uncited-number", "duplicate-source"}

HARD_BLURB = {
    "citation-out-of-range": "the report cites a source that is not in the list",
    "uncited-number": "a number is asserted with no source behind it",
    "duplicate-source": "the source list is padded with one page under several URLs",
}


def verify(path: str) -> int:
    data = load_report(path)
    report = report_text(data)
    sources = source_list(data)

    failures: list[tuple[str, str]] = []

    cited = citations_in(report)
    total = len(sources)

    dangling = sorted({n for n in cited if n < 1 or n > total})
    if dangling:
        failures.append((
            "citation-out-of-range",
            f"citations {dangling} have no source (source list has {total})",
        ))

    orphans = sorted(set(range(1, total + 1)) - set(cited))
    if orphans:
        titles = ", ".join(
            (sources[n - 1].get("title") or "?")[:50] for n in orphans[:6]
        )
        failures.append((
            "uncited-source",
            f"{len(orphans)} source(s) listed but never cited: {titles}",
        ))

    seen: dict[str, int] = {}
    for i, s in enumerate(sources, 1):
        key = canonical_url(s.get("url") or "")
        if not key:
            continue
        if key in seen:
            failures.append((
                "duplicate-source",
                f"[{seen[key]}] and [{i}] are the same page: {key}",
            ))
        else:
            seen[key] = i

    sentences = split_sentences(report)
    quant = [s for s in sentences if has_quantified_claim(s)]
    named = [s for s in sentences if has_named_claim(s)]

    ungrounded_quant = [s for s in quant if not citations_in(s)]
    ungrounded_named = [s for s in named if not citations_in(s)]

    for s in ungrounded_quant:
        failures.append(("uncited-number", s.strip()[:150]))
    for s in ungrounded_named:
        failures.append(("uncited-entity", s.strip()[:150]))

    print(f"file                {path}")
    print(f"sources             {total}")
    print(f"citations           {len(cited)} in {len(set(cited))} distinct sources")
    print(f"unused sources      {total - len(set(cited))}")
    print(f"sentences           {len(sentences)}")
    print(f"quantified claims   {len(quant)}, of which {len(ungrounded_quant)} uncited")
    print(f"named claims        {len(named)}, of which {len(ungrounded_named)} uncited")
    print()

    if not failures:
        print("PASS - no structural failures")
        return 0

    hard = [(k, d) for k, d in failures if k in HARD]
    soft = [(k, d) for k, d in failures if k not in HARD]

    for label, group in (("HARD", hard), ("soft", soft)):
        if not group:
            continue
        by_kind: dict[str, list[str]] = {}
        for kind, detail in group:
            by_kind.setdefault(kind, []).append(detail)
        print(f"{label.upper()} - {len(group)} issue(s)\n")
        for kind, details in by_kind.items():
            print(f"[{kind}] x{len(details)}")
            for d in details[:10]:
                print(f"  - {d}")
            if len(details) > 10:
                print(f"  ... {len(details) - 10} more")
            print()

    if hard:
        kinds = sorted({k for k, _ in hard})
        print(f"FAIL - {len(hard)} hard failure(s): "
              + "; ".join(HARD_BLURB.get(k, k) for k in kinds))
        return 1
    print(f"No hard failures. {len(soft)} soft issue(s) worth reading.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(verify(sys.argv[1]))
