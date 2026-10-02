"""The checkers must pass on a report that is actually good.

Without this, a checker that fails on everything satisfies every test in
bad_reports/ -- which is how a claim list that never parsed went unnoticed.
"""

import contextlib
import io
import json
from pathlib import Path

import pytest

from evals import verify_grounding, verify_report

GOOD = Path(__file__).resolve().parent / "good_reports"


def run(checker, path):
    """Run a checker and capture what it printed, so we can assert on the label."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = checker(str(path))
    return code, buf.getvalue()


@pytest.mark.parametrize("fixture", ["well_grounded"])
def test_good_report_passes_verify_report(fixture):
    code, out = run(verify_report.verify, GOOD / f"{fixture}.json")
    assert code == 0, f"{fixture}: expected exit 0\n{out}"
    assert "PASS" in out


@pytest.mark.parametrize("fixture", ["well_grounded"])
def test_good_report_passes_verify_grounding(fixture):
    code, out = run(verify_grounding.verify, GOOD / f"{fixture}.json")
    assert code == 0, f"{fixture}: expected exit 0\n{out}"
    assert "PASS" in out


def test_good_report_is_not_merely_empty():
    """A fixture that lost its claims would make the two tests above vacuous."""
    data = json.loads((GOOD / "well_grounded.json").read_text(encoding="utf-8"))
    claims = data["_meta"]["writer"]["claims"]
    assert len(claims) >= 2
    assert all(c["quote"] for c in claims)