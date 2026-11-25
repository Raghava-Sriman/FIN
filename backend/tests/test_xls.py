"""
Legacy Excel (.xls) statement parsing, end to end through parse_statement_file.
The fixtures are synthetic 4-row statements written with xlwt: one stores dates
as DD/MM/YYYY text, the other as real Excel date cells.
Run from backend/: python -m unittest discover -s tests -v
"""

import os
import unittest

from app.services.parser.universal_parser import parse_statement_file

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
EXPECTED = [
    ("2026-10-01", 450.0, 0.0),
    ("2026-10-05", 0.0, 90000.0),
    ("2026-10-12", 1280.5, 0.0),
    ("2026-10-25", 649.0, 0.0),
]


class XlsStatementTests(unittest.TestCase):
    def _parse(self, name):
        rows = parse_statement_file(os.path.join(FIXTURES, name))
        return [(r["date"], r["debit"], r["credit"]) for r in rows]

    def test_xls_with_text_dates(self):
        self.assertEqual(self._parse("statement_text_dates.xls"), EXPECTED)

    def test_xls_with_date_cells(self):
        self.assertEqual(self._parse("statement_date_cells.xls"), EXPECTED)


if __name__ == "__main__":
    unittest.main()
