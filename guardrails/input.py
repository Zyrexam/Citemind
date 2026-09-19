import re

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"you are now",
    r"system prompt",
]


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
