"""Terminal entry point for the OBD-Insight V1 prototype."""

import sys
from pathlib import Path

from parser import parse_scan_session
from severity import classify_severity


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_SCAN_PATH = BASE_DIR / "sample_scan.txt"


def main():
    scan_log_path = get_scan_log_path(sys.argv)
    scan_text = scan_log_path.read_text(encoding="utf-8")
    session = parse_scan_session(scan_text)

    results = []
    for dtc in session["dtcs"]:
        severity = classify_severity(
            dtc["module"],
            dtc["code"],
            raw_line=dtc["raw_line"],
        )
        results.append({**dtc, "severity": severity})

    print_summary(session, results)


def get_scan_log_path(args):
    """Use a provided FORScan log file path, or fall back to the sample log."""
    if len(args) == 1:
        return SAMPLE_SCAN_PATH

    if len(args) > 2:
        print("Usage: python src/main.py [forscan_log_file]")
        sys.exit(1)

    scan_log_path = Path(args[1])
    if not scan_log_path.exists():
        print(f"Error: scan log file not found: {scan_log_path}")
        sys.exit(1)

    if not scan_log_path.is_file():
        print(f"Error: scan log path is not a file: {scan_log_path}")
        sys.exit(1)

    return scan_log_path


def print_summary(session, results):
    vehicle_info = session["vehicle"]
    modules = session["modules"]
    counts = {
        "Critical": 0,
        "Warning": 0,
        "Informational": 0,
    }

    for result in results:
        counts[result["severity"]] += 1

    print("Vehicle:")
    print(format_vehicle(vehicle_info))
    if vehicle_info.get("vin"):
        print(f"VIN: {vehicle_info['vin']}")

    print()
    print("Modules Found:")
    print(len(modules))

    print()
    print("Scan Summary:")
    print(f"{len(results)} DTCs found")
    print(f"{counts['Critical']} Critical")
    print(f"{counts['Warning']} Warning")
    print(f"{counts['Informational']} Informational")

    print()
    print("Results:")
    if not results:
        print("No DTCs found.")
        return

    module_width = max(len(result["module"]) for result in results)
    module_name_width = max(len(result.get("module_name") or "Unknown module") for result in results)
    for result in results:
        severity = result["severity"].upper()
        module = result["module"].ljust(module_width)
        module_name = (result.get("module_name") or "Unknown module").ljust(module_name_width)
        print(f"{severity:<13} | {module} | {module_name} | {result['code']}")


def format_vehicle(vehicle_info):
    if vehicle_info.get("vehicle"):
        return vehicle_info["vehicle"]

    parts = [
        vehicle_info.get("year"),
        vehicle_info.get("make"),
        vehicle_info.get("model"),
        vehicle_info.get("engine"),
    ]
    vehicle = " ".join(part for part in parts if part)
    return vehicle or "Unknown vehicle"


if __name__ == "__main__":
    main()
