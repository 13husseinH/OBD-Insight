"""Parsing helpers for OBD-Insight scan text."""

import re


DTC_PATTERN = re.compile(r"\b([BPCU][0-3][0-9A-F]{3}(?::[0-9A-F]{2})?(?:-[0-9A-F]{2})?)\b", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^=+\s*([A-Za-z0-9]+)\s+DTC\s+(.+?)\s*=+$", re.IGNORECASE)
MODULE_LINE_PATTERN = re.compile(r"^(?:Module\s*:\s*)?([A-Za-z][A-Za-z0-9]{1,8})\b.*?\b([BPCU][0-3][0-9A-F]{3}(?::[0-9A-F]{2})?(?:-[0-9A-F]{2})?)\b", re.IGNORECASE)


def parse_vehicle_info(text):
    """Extract basic vehicle details when they appear in the scan text."""
    info = {}

    label_patterns = {
        "year": r"\bYear\s*:\s*(.+)",
        "make": r"\bMake\s*:\s*(.+)",
        "model": r"\bModel\s*:\s*(.+)",
        "engine": r"\bEngine\s*:\s*(.+)",
        "vin": r"\bVIN\s*:\s*([A-HJ-NPR-Z0-9]{11,17})",
    }

    for key, pattern in label_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info[key] = match.group(1).strip()

    vehicle_match = re.search(r"\bVehicle\s*:\s*(.+)", text, re.IGNORECASE)
    if vehicle_match:
        info["vehicle"] = vehicle_match.group(1).strip()

    return info


def parse_dtcs(text):
    """Return DTC entries with module, code, and raw source line."""
    dtcs = []
    seen = set()
    current_module = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            current_module = heading_match.group(1)
            code_match = DTC_PATTERN.search(heading_match.group(2))
            if code_match:
                _add_dtc(dtcs, seen, current_module, code_match.group(1), line)
            continue

        module_label = re.match(r"^Module\s*:\s*(.+)", line, re.IGNORECASE)
        if module_label and not DTC_PATTERN.search(line):
            current_module = _short_module_name(module_label.group(1))
            continue

        if line.lower().startswith("code:"):
            code_match = DTC_PATTERN.search(line)
            if code_match:
                _add_dtc(dtcs, seen, current_module or "Unknown", code_match.group(1), line)
            continue

        module_line_match = MODULE_LINE_PATTERN.match(line)
        if module_line_match:
            module = module_line_match.group(1)
            code = module_line_match.group(2)
            current_module = module
            _add_dtc(dtcs, seen, module, code, line)
            continue

        code_match = DTC_PATTERN.search(line)
        if code_match:
            _add_dtc(dtcs, seen, current_module or "Unknown", code_match.group(1), line)

    return dtcs


def _add_dtc(dtcs, seen, module, code, raw_line):
    code = code.upper()
    key = (module, code)
    if key in seen:
        return

    base_key = (module, _code_base(code))
    for index, existing in enumerate(dtcs):
        existing_base_key = (existing["module"], _code_base(existing["code"]))
        if existing_base_key == base_key:
            if len(code) > len(existing["code"]):
                seen.discard((existing["module"], existing["code"]))
                dtcs[index] = {
                    "module": module,
                    "code": code,
                    "raw_line": raw_line,
                }
                seen.add(key)
            return

    seen.add(key)
    dtcs.append(
        {
            "module": module,
            "code": code,
            "raw_line": raw_line,
        }
    )


def _code_base(code):
    return re.split(r"[:-]", code, maxsplit=1)[0]


def _short_module_name(value):
    """Use the first compact token as a fallback module name."""
    match = re.search(r"\b[A-Za-z][A-Za-z0-9]{1,8}\b", value)
    if match:
        return match.group(0)
    return "Unknown"
