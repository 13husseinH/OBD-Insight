"""Regression tests for the sanitized real FORScan log."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from parser import parse_scan_session  # noqa: E402


class RealForscanLogTests(unittest.TestCase):
    def test_real_log_vehicle_modules_and_dtcs(self):
        log_path = PROJECT_ROOT / "data" / "forscan.txt"
        scan_text = log_path.read_text(encoding="utf-8")

        session = parse_scan_session(scan_text)

        self.assertEqual(
            session["vehicle"],
            {
                "vin": "2LM*********18750",
                "vehicle": "Lincoln MKX TiVCT 3.7L 2012 ( 2012 MY )",
            },
        )
        self.assertEqual(len(session["modules"]), 25)
        self.assertEqual(
            [
                (dtc["module"], dtc["module_name"], dtc["code"])
                for dtc in session["dtcs"]
            ],
            [
                ("APIM", "Accessory Protocol Interface Module", "C1001:01-68"),
                ("BdyCM", "Body Control Module", "B115E:55-0A"),
                ("HVAC", "Heating Ventilation Air Conditioning", "B10B9:14-08"),
                ("DSM", "Driver's Seat Module", "B2312-60"),
                ("DSM", "Driver's Seat Module", "B2316-60"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
