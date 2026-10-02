"""The verifiers must fail on broken reports and pass on a good one.

Each fixture in tests/bad_reports/ carries exactly one defect, so the test can
assert the specific check it should trip.
"""

import contextlib
import io
from pathlib import Path

import pytest

from evals import verify_grounding, verify_report

BAD = Path(__file__).resolve().parent / "bad_reports"
GOOD = Path(__file__).resolve().parent / "good_reports"


def run(checker, path):
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
    ],
)
def test_broken_report_is_caught(fixture, checker, label):
    code, out = run(checker.verify, BAD / f"{fixture}.json")
    assert code == 1, f"{fixture}: expected exit 1\n{out}"
    assert f"[{label}]" in out, f"{fixture}: expected [{label}]\n{out}"


@pytest.mark.parametrize("fixture", ["well_grounded"])
def test_good_report_passes_verify_report(fixture):
    code, out = run(verify_report.verify, GOOD / f"{fixture}.json")
    assert code == 0, out
    assert "PASS" in out


@pytest.mark.parametrize("fixture", ["well_grounded"])
def test_good_report_passes_verify_grounding(fixture):
    code, out = run(verify_grounding.verify, GOOD / f"{fixture}.json")
    assert code == 0, out
    assert "PASS" in out