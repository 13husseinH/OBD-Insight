"""Simple severity rules for V1."""


CRITICAL_MODULES = {"ABS", "RCM", "SRS", "TCM", "PCM"}
WARNING_MODULES = {"BDYCM", "DSM", "DDM", "PDM", "HVAC", "APIM", "IPC"}
INFORMATIONAL_WORDS = ("stored", "historical", "intermittent", "previously cleared", "not present")
CRITICAL_WORDS = ("misfire", "brake", "airbag", "srs", "transmission", "powertrain")


def classify_severity(module, code, raw_line=None):
    """Classify a DTC as Critical, Warning, or Informational."""
    module_upper = (module or "").upper()
    code_upper = (code or "").upper()
    line_lower = (raw_line or "").lower()

    if _line_suggests_informational(line_lower):
        return "Informational"

    if _looks_critical(module_upper, code_upper, line_lower):
        return "Critical"

    if module_upper in WARNING_MODULES:
        return "Warning"

    return "Warning"


def _line_suggests_informational(line_lower):
    return any(word in line_lower for word in INFORMATIONAL_WORDS)


def _looks_critical(module, code, line_lower):
    if module in CRITICAL_MODULES:
        return True

    if code.startswith("P03"):
        return True

    if any(word in line_lower for word in CRITICAL_WORDS):
        return True

    return False
