"""Tests for FORScan text copied through the Windows clipboard."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from analysis import analyze_scan_text  # noqa: E402
from parser import parse_scan_session  # noqa: E402


class ClipboardInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_log = (PROJECT_ROOT / "data" / "forscan.txt").read_text(
            encoding="utf-8"
        )

    def test_windows_line_endings_parse_like_the_saved_log(self):
        clipboard_text = self.real_log.replace("\n", "\r\n")

        analysis = analyze_scan_text(clipboard_text)

        self.assertEqual(len(analysis["modules"]), 25)
        self.assertEqual(len(analysis["results"]), 5)
        self.assertEqual(analysis["counts"]["Warning"], 5)

    def test_collapsed_clipboard_entries_are_split_and_parsed(self):
        clipboard_text = " ".join(self.real_log.splitlines())

        session = parse_scan_session(clipboard_text)

        self.assertEqual(len(session["modules"]), 25)
        self.assertEqual(
            [dtc["code"] for dtc in session["dtcs"]],
            ["C1001:01-68", "B115E:55-0A", "B10B9:14-08", "B2312-60", "B2316-60"],
        )

    def test_extra_spaces_tabs_and_blank_lines_are_accepted(self):
        clipboard_text = self.real_log.replace(
            "Found module:  APIM",
            "Found   module:\t    APIM",
        ).replace(
            "DTCs in APIM: C1001:01-68",
            "DTCs   in\tAPIM:    C1001:01-68",
        )
        clipboard_text = f"\n\n  {clipboard_text}\n\n"

        session = parse_scan_session(clipboard_text)

        self.assertEqual(len(session["modules"]), 25)
        self.assertEqual(len(session["dtcs"]), 5)
        self.assertEqual(session["dtcs"][0]["module"], "APIM")


if __name__ == "__main__":
    unittest.main()
