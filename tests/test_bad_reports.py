"""The checkers must fail on reports that are broken on purpose.

A verifier that passes everything is worse than no verifier, because it is
trusted. Each fixture in tests/bad_reports/ carries exactly one defect; the
test asserts the specific check that defect should trip, so a checker that goes
quiet stops the build rather than quietly passing bad reports forever.
"""

import contextlib
import io
from pathlib import Path

import pytest

from evals import verify_grounding, verify_report

BAD = Path(__file__).resolve().parent / "bad_reports"


def run(checker, path):
    """Run a checker and capture what it printed, so we can assert on the label."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = checker(str(path))
    return code, buf.getvalue()


@pytest.mark.parametrize(
    "fixture, checker, label",
    [
        ("uncited_number", verify_report, "uncited-number"),
        ("dangling_citation", verify_report, "citation-out-of-range"),
        ("duplicate_url", verify_report, "duplicate-source"),
        ("fabricated_quote", verify_grounding, "quote-not-found"),
        ("truncated_quote", verify_grounding, "quote-cut-mid-word"),
        ("truncated_quote", verify_grounding, "quote-too-short"),
    ],
)
def test_broken_report_is_caught(fixture, checker, label):
    code, out = run(checker.verify, BAD / f"{fixture}.json")
    assert code == 1, f"{fixture}: checker exited {code}, expected 1\n{out}"
    assert f"[{label}]" in out, f"{fixture}: expected [{label}], got:\n{out}"


@pytest.mark.parametrize(
    "fixture",
    ["uncited_number", "dangling_citation", "duplicate_url",
     "fabricated_quote", "truncated_quote"],
)
def test_both_checkers_run_clean_on_nothing(fixture):
    """No fixture may crash a checker. A traceback is not a verdict."""
    for checker in (verify_report, verify_grounding):
        code, out = run(checker.verify, BAD / f"{fixture}.json")
        assert "Traceback" not in out, f"{fixture}: {checker.__name__} crashed:\n{out}"


@pytest.mark.parametrize(
    "sentence, quantified",
    [
        ("It cuts errors by 43% whenever the retriever is right.", True),
        ("It cuts errors by 43 % of the time.", True),
        ("Latency fell 43%year over year.", True),
        ("The gain was 10x over the baseline.", True),
        ("The study ran 500ms per query.", True),
        ("Revenue reached 3.5 billion dollars.", True),
        ("The model is called BERT.", False),
        ("Version 2 was released in 2024.", False),  # a year alone is not a quantity
        ("Section 4 describes the method.", False),
    ],
)
def test_quantified_claim_detection(sentence, quantified):
    from evals.checks import has_quantified_claim

    assert has_quantified_claim(sentence) is quantified


@pytest.mark.parametrize(
    "quote, haystack, defects",
    [
        # complete and long enough
        ("ranked highly are actually relevant to the question",
         "the passages that are ranked highly are actually relevant to the question being asked",
         []),
        # stops mid-word ("releva" of "relevant"), still long enough to matter
        ("retrieved passages that are ranked highly are actually releva",
         "the retrieved passages that are ranked highly are actually relevant "
         "to the question asked",
         ["quote-cut-mid-word"]),
        # too short to be evidence
        ("actually relevant",
         "the passages that are ranked highly are actually relevant to the question being asked",
         ["quote-too-short"]),
        # cut off mid-word on the first occurrence, complete on the second:
        # the phrase exists intact somewhere, so the quote is not truncated
        ("the first and last passage in the ranking",
         "the first and last passage in the rankings are audited, and separately "
         "the first and last passage in the ranking is audited twice",
         []),
    ],
)
def test_quote_completeness(quote, haystack, defects):
    from evals.verify_grounding import quote_defects

    assert [d.split(" ")[0] for d in quote_defects(quote, haystack)] == defects
