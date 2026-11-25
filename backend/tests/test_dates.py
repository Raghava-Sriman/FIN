"""
Date parsing tests for the generic CSV/Excel statement parser.
Run from backend/: python -m unittest discover -s tests -v
"""

import os
import tempfile
import unittest

import pandas as pd

from app.services.parser.dates import detect_day_first, parse_statement_date
from app.services.parser.universal_parser import parse_statement_file


class DetectDayFirstTests(unittest.TestCase):
    def test_all_ambiguous_defaults_to_day_first(self):
        self.assertTrue(detect_day_first(["01/10/2026", "05/10/2026", "12/11/2026"]))

    def test_day_above_12_means_day_first(self):
        self.assertTrue(detect_day_first(["01/03/2026", "25/03/2026"]))

    def test_second_number_above_12_means_month_first(self):
        self.assertFalse(detect_day_first(["01/10/2026", "03/25/2026"]))

    def test_conflicting_evidence_defaults_to_day_first(self):
        self.assertTrue(detect_day_first(["25/03/2026", "03/25/2026"]))

    def test_iso_and_named_month_dates_are_ignored(self):
        self.assertTrue(detect_day_first(["2026-03-25", "Oct 13, 2026", None, "nan"]))


class ParseStatementDateTests(unittest.TestCase):
    def test_ambiguous_date_is_day_first(self):
        self.assertEqual(parse_statement_date("01/10/2026"), "2026-10-01")

    def test_unambiguous_day_first_date(self):
        self.assertEqual(parse_statement_date("25/03/2026"), "2026-03-25")

    def test_month_first_when_file_is_month_first(self):
        self.assertEqual(parse_statement_date("01/10/2026", day_first=False), "2026-01-10")
        self.assertEqual(parse_statement_date("03/25/2026", day_first=False), "2026-03-25")

    def test_mixed_separators(self):
        for raw in ("01/10/2026", "01-10-2026", "01.10.2026", "01 10 2026", "1/10/2026", "01/10/26", "01 / 10 / 2026"):
            with self.subTest(raw=raw):
                self.assertEqual(parse_statement_date(raw), "2026-10-01")

    def test_time_component_is_ignored(self):
        self.assertEqual(parse_statement_date("05-10-2026 14:32"), "2026-10-05")
        self.assertEqual(parse_statement_date("05/10/2026T09:00:00"), "2026-10-05")

    def test_year_first_and_named_month_dates(self):
        self.assertEqual(parse_statement_date("2026-10-01"), "2026-10-01")
        self.assertEqual(parse_statement_date("2026-10-01 00:00:00"), "2026-10-01")
        self.assertEqual(parse_statement_date("01 Oct 2026"), "2026-10-01")
        self.assertEqual(parse_statement_date("Oct 01, 2026"), "2026-10-01")

    def test_invalid_and_empty_dates(self):
        for raw in ("31/02/2026", "13/13/2026", "", "nan", None, "not a date"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_statement_date(raw))


class GenericParserFileTests(unittest.TestCase):
    """End to end through parse_statement_file, as an upload would be parsed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _statement(self, dates):
        return pd.DataFrame({
            "Date": dates,
            "Narration": [f"UPI/MERCHANT {i}" for i in range(len(dates))],
            "Debit": [100.0] * len(dates),
            "Credit": [0.0] * len(dates),
            "Balance": [10000.0 - 100.0 * (i + 1) for i in range(len(dates))],
        })

    def _parse_csv(self, dates):
        path = os.path.join(self.tmp.name, "statement.csv")
        self._statement(dates).to_csv(path, index=False)
        return [t["date"] for t in parse_statement_file(path)]

    def test_csv_with_only_ambiguous_dates_is_day_first(self):
        self.assertEqual(self._parse_csv(["01/10/2026", "05/10/2026"]), ["2026-10-01", "2026-10-05"])

    def test_csv_with_unambiguous_day_first_dates(self):
        self.assertEqual(self._parse_csv(["01/03/2026", "25/03/2026"]), ["2026-03-01", "2026-03-25"])

    def test_csv_detected_as_month_first(self):
        self.assertEqual(self._parse_csv(["01/10/2026", "03/25/2026"]), ["2026-01-10", "2026-03-25"])

    def test_csv_with_mixed_separators(self):
        self.assertEqual(
            self._parse_csv(["01-10-2026", "02.10.2026", "03/10/2026"]),
            ["2026-10-01", "2026-10-02", "2026-10-03"],
        )

    def test_xlsx_with_text_dates_is_day_first(self):
        path = os.path.join(self.tmp.name, "statement.xlsx")
        self._statement(["01/10/2026", "05/10/2026"]).to_excel(path, index=False)
        self.assertEqual([t["date"] for t in parse_statement_file(path)], ["2026-10-01", "2026-10-05"])

    def test_xlsx_with_real_date_cells(self):
        path = os.path.join(self.tmp.name, "statement.xlsx")
        self._statement(pd.to_datetime(["2026-10-01", "2026-10-05"])).to_excel(path, index=False)
        self.assertEqual([t["date"] for t in parse_statement_file(path)], ["2026-10-01", "2026-10-05"])


if __name__ == "__main__":
    unittest.main()
