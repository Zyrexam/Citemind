"""Re-check stored quotes against the current rules. No LLM calls.

    python -m evals.quote_audit
"""

import json
from pathlib import Path

from evals.verify_grounding import MIN_QUOTE_WORDS, quote_defects, quote_found

RESULTS = Path(__file__).resolve().parent / "results"


def audit(paths) -> dict:
    total = found = usable = 0
    reasons: dict[str, list[str]] = {}
    per_file: list[tuple[str, int, int, int]] = []

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        sources = data.get("citations") or []
        meta = (data.get("_meta") or {}).get("writer") or {}
        claims = meta.get("claims") or []
        per_source = meta.get("per_source")
        if not claims:
            continue

        f_total = f_usable = 0
        for c in claims:
            total += 1
            f_total += 1
            try:
                n = int(c["source"])
            except (TypeError, ValueError, KeyError):
                reasons.setdefault("bad-source-index", []).append(f"{path.name}: {c}")
                continue
            if n < 1 or n > len(sources):
                reasons.setdefault("bad-source-index", []).append(
                    f"{path.name}: [{n}] of {len(sources)}")
                continue

            passage = sources[n - 1].get("content", "")
            if per_source:
                passage = passage[:per_source]

            if not quote_found(c["quote"], passage):
                reasons.setdefault("quote-not-found", []).append(
                    f"{path.name} [{n}] {c['quote'][:70]}")
                continue
            found += 1

            defects = quote_defects(c["quote"], passage)
            if defects:
                for d in defects:
                    reasons.setdefault(d.split(" ")[0], []).append(
                        f"{path.name} [{n}] {d}")
            else:
                usable += 1
                f_usable += 1

        per_file.append((path.name, f_total, f_usable, f_total - f_usable))

    return {"total": total, "found": found, "usable": usable,
            "reasons": reasons, "per_file": per_file}


def main() -> int:
    paths = sorted(RESULTS.glob("*.json"))
    if not paths:
        print(f"no stored reports under {RESULTS}")
        return 1

    a = audit(paths)
    total = a["total"]
    # absent quotes were already failing before the new rules; keep them apart
    pre_existing = len(a["reasons"].get("quote-not-found", []))
    newly = {k: v for k, v in a["reasons"].items() if k != "quote-not-found"}

    print(f"stored reports          {len(a['per_file'])}")
    print(f"stored quotes           {total}")
    print(f"pass containment        {a['found']}/{total} ({100 * a['found'] // max(1, total)}%)")
    print(f"pass new rules too      {a['usable']}/{total} ({100 * a['usable'] // max(1, total)}%)")
    print(f"new rule                 >= {MIN_QUOTE_WORDS} words AND ends on a word boundary")
    print()
    print(f"already failing before  {pre_existing}  (quote never occurred in its source)")
    print(f"newly failing now       {sum(len(v) for v in newly.values())}  "
          f"({pre_existing + sum(len(v) for v in newly.values())} failing in total)")
    print()

    if not a["reasons"]:
        print("nothing fails.")
        return 0

    print("by reason")
    for reason, items in sorted(a["reasons"].items(), key=lambda kv: -len(kv[1])):
        tag = "pre-existing" if reason == "quote-not-found" else "NEW RULE"
        print(f"  {reason:20} {len(items):4}  {tag}")
        for it in items[:4]:
            print(f"      {it}")
        if len(items) > 4:
            print(f"      ... {len(items) - 4} more")
    print()

    print("worst files")
    for name, t, u, bad in sorted(a["per_file"], key=lambda r: -(r[3] / max(1, r[1])))[:10]:
        if bad:
            print(f"  {name:26} {u}/{t} usable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
