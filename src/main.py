"""Terminal entry point for the OBD-Insight V1 prototype."""

import json
from pathlib import Path

from parser import parse_dtcs, parse_vehicle_info
from severity import classify_severity


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
SAMPLE_SCAN_PATH = BASE_DIR / "sample_scan.txt"
CODES_PATH = PROJECT_DIR / "data" / "codes.json"


def main():
    scan_text = SAMPLE_SCAN_PATH.read_text(encoding="utf-8")
    codes_db = load_codes()

    vehicle_info = parse_vehicle_info(scan_text)
    dtcs = parse_dtcs(scan_text)

    results = []
    for dtc in dtcs:
        severity = classify_severity(
            dtc["module"],
            dtc["code"],
            raw_line=dtc["raw_line"],
            codes_db=codes_db,
        )
        results.append({**dtc, "severity": severity})

    print_summary(vehicle_info, results)


def load_codes():
    if not CODES_PATH.exists():
        return {}
    with CODES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def print_summary(vehicle_info, results):
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
    for result in results:
        severity = result["severity"].upper()
        module = result["module"].ljust(module_width)
        print(f"{severity:<13} | {module} | {result['code']}")


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
