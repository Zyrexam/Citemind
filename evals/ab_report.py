import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.checks import looks_like_refusal  # noqa: E402
from evals.verify_grounding import quote_defects, quote_found  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


def arm(tag: str) -> dict:
    paths = sorted(RESULTS.glob(f"{tag}_*.json"))
    reports = claims = found = usable = 0
    refused = 0
    sources: list[int] = []
    slices: list[int] = []
    chars: list[int] = []
    urls: list[set[str]] = []

    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        srcs = data.get("citations") or []
        w = (data.get("_meta") or {}).get("writer") or {}
        cl = w.get("claims") or []
        per_source = w.get("per_source")

        reports += 1
        sources.append(len(srcs))
        chars.append(len(data.get("report", "")))
        if per_source:
            slices.append(per_source)
        if looks_like_refusal(data.get("report", "")):
            refused += 1
        urls.append({s.get("url", "") for s in srcs})

        for c in cl:
            claims += 1
            try:
                n = int(c["source"])
            except (TypeError, ValueError, KeyError):
                continue
            if n < 1 or n > len(srcs):
                continue
            passage = srcs[n - 1].get("content", "")
            if per_source:
                passage = passage[:per_source]
            if not quote_found(c["quote"], passage):
                continue
            found += 1
            if not quote_defects(c["quote"], passage):
                usable += 1

    return {
        "tag": tag, "reports": reports, "claims": claims, "found": found,
        "usable": usable, "refused": refused, "urls": urls,
        "avg_sources": sum(sources) / max(1, len(sources)),
        "avg_slice": sum(slices) / max(1, len(slices)),
        "avg_chars": sum(chars) / max(1, len(chars)),
    }


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    a, b = arm(sys.argv[1]), arm(sys.argv[2])
    if not a["reports"] or not b["reports"]:
        print("one of the arms has no stored reports; nothing to compare")
        return 1

    # pool overlap, matched by question id rather than by position
    amap = {p.stem.split("_", 1)[1]: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(RESULTS.glob(f"{a['tag']}_*.json"))}
    bmap = {p.stem.split("_", 1)[1]: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(RESULTS.glob(f"{b['tag']}_*.json"))}
    shared = sorted(set(amap) & set(bmap))
    ratios = []
    for k in shared:
        ua = {s.get("url") for s in amap[k].get("citations", [])}
        ub = {s.get("url") for s in bmap[k].get("citations", [])}
        ratios.append(len(ua & ub) / max(1, len(ua)))

    print(f"pool overlap        {len(ratios)} question(s) matched by id")
    print(f"  {a['tag']} sources found inside {b['tag']} sources: "
          + (", ".join(f"{r:.0%}" for r in ratios) if ratios else "n/a"))
    print()

    hdr = f"{'metric':28} {a['tag']:>8} {b['tag']:>8}"
    print(hdr)
    print("-" * len(hdr))
    rows = [
        ("reports", a["reports"], b["reports"]),
        ("avg sources/report", f"{a['avg_sources']:.1f}", f"{b['avg_sources']:.1f}"),
        ("avg chars/source slice", f"{a['avg_slice']:.0f}", f"{b['avg_slice']:.0f}"),
        ("avg report chars", f"{a['avg_chars']:.0f}", f"{b['avg_chars']:.0f}"),
        ("claims", a["claims"], b["claims"]),
        ("quotes containing", f"{a['found']}/{a['claims']}", f"{b['found']}/{b['claims']}"),
        ("quote pass rate (containment)",
         f"{100 * a['found'] // max(1, a['claims'])}%",
         f"{100 * b['found'] // max(1, b['claims'])}%"),
        ("quote pass rate (usable)",
         f"{100 * a['usable'] // max(1, a['claims'])}%",
         f"{100 * b['usable'] // max(1, b['claims'])}%"),
        ("refusals", a["refused"], b["refused"]),
    ]
    for name, x, y in rows:
        print(f"{name:28} {str(x):>8} {str(y):>8}")

    print()
    print("Answer quality is still not graded. Read the reports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
