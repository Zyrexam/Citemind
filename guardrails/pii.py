import re

PATTERNS = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone": r"\b\d{10}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


def scrub_pii(text: str) -> str:
    for name, pat in PATTERNS.items():
        text = re.sub(pat, f"[{name.upper()}_REDACTED]", text)
    return text
