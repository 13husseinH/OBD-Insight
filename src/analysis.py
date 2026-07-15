"""Reusable scan-analysis workflow for the terminal and desktop app."""

from parser import parse_scan_session
from severity import classify_severity


def analyze_scan_text(scan_text):
    """Parse FORScan text and return DTC results with severity totals."""
    session = parse_scan_session(scan_text)
    results = []

    for dtc in session["dtcs"]:
        severity = classify_severity(
            dtc["module"],
            dtc["code"],
            raw_line=dtc["raw_line"],
        )
        results.append({**dtc, "severity": severity})

    counts = {
        "Critical": 0,
        "Warning": 0,
        "Informational": 0,
    }
    for result in results:
        counts[result["severity"]] += 1

    return {
        **session,
        "results": results,
        "counts": counts,
    }
