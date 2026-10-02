"""Run the fixed question set through the pipeline and verify each result.

    python -m evals.verify_suite --limit 3

Runs in-process so the full fetched page text is captured -- that is what lets
the grounding check run at all. Grades nothing; prints structural and grounding
numbers and leaves answer quality to a human.
"""

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.planner.agent import plan  # noqa: E402
from agents.retriever.agent import retrieve  # noqa: E402
from agents.writer.agent import write  # noqa: E402
from core.config import settings  # noqa: E402
from evals import verify_grounding, verify_report  # noqa: E402
from evals.checks import CITE_RE, looks_like_refusal  # noqa: E402
from guardrails import scrub_pii, validate_input  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
TESTS = Path(__file__).resolve().parents[1] / "tests"
SETS = {"eval": "questions.json", "heldout": "heldout.json"}


def run_one(q: str) -> dict:
    clean = scrub_pii(q)
    sub = plan(clean)[: settings.sub_queries]
    sources = retrieve(sub, max_results=settings.results_per_query)
    trace: dict = {}
    report = write(clean, sources, trace=trace)
    return {
        "query": q,
        "report": report,
        "citations": [
            {
                "title": s["title"],
                "url": s["url"],
                "snippet": (s.get("content") or "")[:600],
                "content": s.get("content") or "",
                "query": s.get("query", ""),
            }
            for s in sources
        ],
        "_meta": {
            "sub_queries": len(sub),
            "sources": len(sources),
            "report_chars": len(report),
            "writer": trace,
            "settings": {
                "sub_queries": settings.sub_queries,
                "results_per_query": settings.results_per_query,
                "writer_context_chars": settings.writer_context_chars,
                "writer_max_tokens": settings.writer_max_tokens,
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="set_", default="eval", choices=("eval", "heldout"))
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--only", nargs="*", help="question ids, e.g. n1 n4")
    ap.add_argument("--kind", help="normal | unanswerable | false_premise | disagreement | hard")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--repeat", type=int, default=1, help="runs per question, for variance")
    ap.add_argument("--pace", type=int, default=65,
                    help="seconds between runs; the model rate-limits per minute")
    args = ap.parse_args()

    spec = json.loads((TESTS / SETS[args.set_]).read_text(encoding="utf-8"))
    items = spec["questions"]
    if args.only:
        items = [q for q in items if q["id"] in args.only]
    if args.kind:
        items = [q for q in items if q["kind"] == args.kind]
    if args.limit:
        items = items[: args.limit]

    RESULTS.mkdir(exist_ok=True)
    print(f"depth: {settings.sub_queries} sub-queries x "
          f"{settings.results_per_query} results, "
          f"{settings.writer_context_chars} chars/source, "
          f"{settings.writer_max_tokens} max tokens\n")

    rows = []
    for item in items:
        for attempt in range(args.repeat):
            ok, err = validate_input(item["q"])
            if not ok:
                print(f"skip {item['id']}: {err}")
                continue

            t0 = time.time()
            try:
                data = run_one(item["q"])
            except Exception as e:
                # One rate-limited question used to abort the whole suite and
                # lose every question after it, which is the most expensive
                # possible outcome for a run that cost minutes to reach.
                print(f"  {item['id']} FAILED after {time.time() - t0:.0f}s: "
                      f"{type(e).__name__}: {str(e)[:120]}", flush=True)
                rows.append({
                    "id": item["id"], "kind": item["kind"], "sources": 0, "cites": 0,
                    "chars": 0, "struct": "ERROR", "ground": "ERROR",
                    "refuse": "ERROR", "claims": 0, "cut": "-", "tok": None,
                    "sec": round(time.time() - t0),
                })
                continue
            elapsed = time.time() - t0

            suffix = f"_r{attempt + 1}" if args.repeat > 1 else ""
            path = RESULTS / f"{args.tag}_{item['id']}{suffix}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                struct_ok = verify_report.verify(str(path)) == 0
                ground_ok = verify_grounding.verify(str(path)) == 0

            rows.append({
                "id": item["id"], "kind": item["kind"],
                "sources": data["_meta"]["sources"],
                "cites": len(CITE_RE.findall(data["report"])),
                "chars": data["_meta"]["report_chars"],
                "struct": "pass" if struct_ok else "FAIL",
                "ground": "pass" if ground_ok else "flag",
                "refuse": "REFUSED" if looks_like_refusal(data["report"]) else "-",
                "claims": len(data["_meta"]["writer"].get("claims", [])),
                "cut": "CUT" if data["_meta"]["writer"].get("cut") else "-",
                "tok": data["_meta"]["writer"].get("tokens"),
                "sec": round(elapsed),
            })
            print(f"  {path.name}  {data['_meta']['sources']} src  "
                  f"{data['_meta']['report_chars']} chars  {elapsed:.0f}s", flush=True)

            if len(items) * args.repeat > 1:
                time.sleep(args.pace)

    if not rows:
        print("nothing ran")
        return 1

    hdr = (f"{'id':5} {'kind':14} {'src':>4} {'cite':>5} {'chars':>6} {'claim':>6} "
           f"{'quote':>6} {'struct':>7} {'refuse':>8} {'cut':>4} {'tok':>6} {'sec':>4}")
    print("\n" + hdr + "\n" + "-" * len(hdr))
    for r in rows:
        print(f"{r['id']:5} {r['kind']:14} {r['sources']:>4} {r['cites']:>5} "
              f"{r['chars']:>6} {r['claims']:>6} {r['ground']:>6} {r['struct']:>7} "
              f"{r['refuse']:>8} {r['cut']:>4} {r['tok'] or 0:>6} {r['sec']:>4}")

    refused = [r["id"] for r in rows if r["refuse"] == "REFUSED"]
    cut = [r["id"] for r in rows if r["cut"] == "CUT"]
    errored = [r["id"] for r in rows if r["struct"] == "ERROR"]
    # A run that emitted no claims has nothing to grade. Scoring it as a quote
    # failure reads as "the quotes are bad" when the truth is "there were none",
    # which is how a dead measurement gets mistaken for a bad result.
    silent = [r["id"] for r in rows if r["claims"] == 0]
    graded = len(rows) - len(silent)

    print(f"\n{len(rows)} run(s). "
          f"struct pass {sum(1 for r in rows if r['struct'] == 'pass')}/{len(rows)}, "
          f"quote clean {sum(1 for r in rows if r['ground'] == 'pass')}/{graded} graded.")
    if errored:
        print(f"ERROR: {', '.join(errored)} -- the pipeline raised; these are not results.")
    if silent:
        print(f"NO CLAIMS: {', '.join(silent)} -- the writer emitted no claim list, so "
              f"nothing was grounded. Excluded from the quote-clean denominator; "
              f"this is a writer failure, not a quote verdict.")
    if refused:
        print(f"REFUSED: {', '.join(refused)} -- expected for unanswerable, "
              f"over-refusal for kind=hard/normal.")
    if cut:
        print(f"CUT: {', '.join(cut)} -- request hit the token cap, context was reduced.")
    over = [r["tok"] for r in rows if r["tok"] and r["tok"] > 8000]
    if over:
        print(f"WARNING: {len(over)} run(s) reported over 8000 total tokens.")
    print("Answer quality is not graded here. Read the reports yourself.")
    print(f"Raw output: {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
