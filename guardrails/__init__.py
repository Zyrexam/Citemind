import re

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"you are now",
    r"system prompt",
]

PII_PATTERNS = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone": r"\b\d{10}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


def validate_input(query: str) -> tuple[bool, str]:
    stripped = query.strip()
    if len(stripped) < 3:
        return False, "Query too short"
    if len(query) > 2000:
        return False, "Query too long"
    for pat in INJECTION_PATTERNS:
        if re.search(pat, query, re.IGNORECASE):
            return False, "Potential prompt injection detected"
    return True, ""


def scrub_pii(text: str) -> str:
    for name, pat in PII_PATTERNS.items():
        text = re.sub(pat, f"[{name.upper()}_REDACTED]", text)
    return text


def validate_output(report: str) -> tuple[bool, str]:
    if not report or len(report.strip()) < 20:
        return False, "Report too short"
    if len(report) > 20000:
        return False, "Report too long"
    return True, ""
