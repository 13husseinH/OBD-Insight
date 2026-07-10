"""Parsing helpers for OBD-Insight scan text."""

import re


DTC_PATTERN = re.compile(r"\b([BPCU][0-3][0-9A-F]{3}(?::[0-9A-F]{2})?(?:-[0-9A-F]{2})?)\b", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^=+\s*([A-Za-z0-9]+)\s+DTC\s+(.+?)\s*=+$", re.IGNORECASE)
DTC_LOG_PATTERN = re.compile(r"\bDTCs\s+in\s+([A-Za-z0-9_]+)\s*:\s*(.+)", re.IGNORECASE)
FOUND_MODULE_PATTERN = re.compile(r"\bFound\s+module\s*:\s*([A-Za-z0-9_]+)\s*-\s*(.+)", re.IGNORECASE)
MODULE_LINE_PATTERN = re.compile(r"^(?:Module\s*:\s*)?([A-Za-z][A-Za-z0-9]{1,8})\b.*?\b([BPCU][0-3][0-9A-F]{3}(?::[0-9A-F]{2})?(?:-[0-9A-F]{2})?)\b", re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(r"^[^\[]*\[\d{2}:\d{2}:\d{2}\.\d{3}\]\s*")


def parse_vehicle_info(text):
    """Extract basic vehicle details when they appear in the scan text."""
    info = {}
    clean_text = "\n".join(_clean_log_line(line) for line in text.splitlines())

    label_patterns = {
        "year": r"\bYear\s*:\s*(.+)",
        "make": r"\bMake\s*:\s*(.+)",
        "model": r"\bModel\s*:\s*(.+)",
        "engine": r"\bEngine\s*:\s*(.+)",
        "vin": r"\bVIN\s*:\s*([A-HJ-NPR-Z0-9*]{11,17})",
    }

    for key, pattern in label_patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            info[key] = match.group(1).strip()

    vehicle_match = re.search(r"\bVehicle\s*:\s*(.+)", clean_text, re.IGNORECASE)
    if vehicle_match:
        vehicle = vehicle_match.group(1).strip()
        info["vehicle"] = re.split(r",\s*VIN\s*:", vehicle, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    return info


def parse_modules(text):
    """Return every module FORScan reports during the scan."""
    modules = []
    seen = set()

    for raw_line in text.splitlines():
        line = _clean_log_line(raw_line)
        module_match = FOUND_MODULE_PATTERN.search(line)
        if not module_match:
            continue

        module_id = module_match.group(1)
        module_name = module_match.group(2).strip()
        if module_id in seen:
            continue

        seen.add(module_id)
        modules.append(
            {
                "id": module_id,
                "name": module_name,
                "raw_line": line,
            }
        )

    return modules


def parse_scan_session(text):
    """Parse one temporary scan session from FORScan text."""
    return {
        "vehicle": parse_vehicle_info(text),
        "modules": parse_modules(text),
        "dtcs": parse_dtcs(text),
    }


def parse_dtcs(text):
    """Return DTC entries with module, code, and raw source line."""
    dtcs = []
    seen = set()
    current_module = None

    for raw_line in text.splitlines():
        line = _clean_log_line(raw_line)
        if not line:
            continue

        dtc_log_match = DTC_LOG_PATTERN.search(line)
        if dtc_log_match:
            module = dtc_log_match.group(1)
            current_module = module
            for code in DTC_PATTERN.findall(dtc_log_match.group(2)):
                _add_dtc(dtcs, seen, module, code, line)
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


def _clean_log_line(line):
    """Remove FORScan log timestamps and surrounding whitespace."""
    return TIMESTAMP_PATTERN.sub("", line).strip()


def _short_module_name(value):
    """Use the first compact token as a fallback module name."""
    match = re.search(r"\b[A-Za-z][A-Za-z0-9]{1,8}\b", value)
    if match:
        return match.group(0)
    return "Unknown"
