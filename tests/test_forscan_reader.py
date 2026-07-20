"""Tests for read-only FORScan window detection helpers."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from forscan_reader import ControlInfo, ForscanInspection  # noqa: E402
from forscan_reader import is_forscan_window_title, looks_like_forscan_log  # noqa: E402


class ForscanReaderTests(unittest.TestCase):
    def test_forscan_window_title_is_recognized(self):
        self.assertTrue(is_forscan_window_title("FORScan 2.3.64 release"))
        self.assertFalse(is_forscan_window_title("OBD-Insight"))
        self.assertFalse(is_forscan_window_title("Notepad"))

    def test_log_markers_are_recognized(self):
        self.assertTrue(looks_like_forscan_log("Vehicle: Lincoln MKX"))
        self.assertTrue(looks_like_forscan_log("Found module: APIM - Interface"))
        self.assertTrue(looks_like_forscan_log("DTCs in DSM: B2312-60"))
        self.assertFalse(looks_like_forscan_log("Connection established"))

    def test_inspection_returns_only_log_candidates(self):
        log_control = ControlInfo(1, "Document", "", "log", "", "Vehicle: MKX")
        button_control = ControlInfo(2, "Button", "", "scan", "Scan", "Scan")
        inspection = ForscanInspection("uia", "FORScan", [log_control, button_control])

        self.assertEqual(inspection.log_candidates, [log_control])


if __name__ == "__main__":
    unittest.main()
