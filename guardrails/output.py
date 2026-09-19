def validate_output(report: str) -> tuple[bool, str]:
    if not report or len(report.strip()) < 20:
        return False, "Report too short"
    if len(report) > 20000:
        return False, "Report too long"
    return True, ""
