"""
Rows with an amount but a missing or unreadable date are not imported, and are
reported back (count + raw rows) instead of being dropped silently.
Run from backend/: python -m unittest discover -s tests -v
"""

import asyncio
import io
import os
import tempfile
import unittest
from unittest import mock

import pandas as pd
from fastapi import UploadFile
from starlette.requests import Request

import _env  # noqa: F401  (must come before importing main: keeps storage in a temp dir)
import main
from app.services.parser.universal_parser import parse_statement_file

CSV_WITH_BAD_ROWS = (
    "Date,Narration,Debit,Credit,Balance\n"
    "01/10/2026,UPI/SWIGGY ORDER,450,,49550\n"     # line 2: ok
    "31/02/2026,UPI/BLINKIT GROCERY,1200,,48350\n"  # line 3: impossible date -> reported
    ",NEFT SALARY ACME,,90000,138350\n"             # line 4: empty date with amount -> reported
    "not a date,Opening balance,,,138350\n"        # line 5: no amount -> silently ignored
    "05/10/2026,ACH NETFLIX,649,,137701\n"         # line 6: ok
)


class ParserSkippedRowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, text):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_csv_reports_rows_with_unreadable_dates(self):
        skipped = []
        rows = parse_statement_file(self._write("s.csv", CSV_WITH_BAD_ROWS), skipped)
        self.assertEqual([r["date"] for r in rows], ["2026-10-01", "2026-10-05"])
        self.assertEqual([s["row_number"] for s in skipped], [3, 4])
        self.assertEqual([s["raw_date"] for s in skipped], ["31/02/2026", ""])
        self.assertEqual(skipped[0]["values"]["Narration"], "UPI/BLINKIT GROCERY")
        self.assertEqual(skipped[1]["values"]["Credit"], "90000.0")

    def test_row_numbers_account_for_lines_above_the_header(self):
        skipped = []
        preamble = "Account statement\nAccount: XXXX1234\n"
        parse_statement_file(self._write("s.csv", preamble + CSV_WITH_BAD_ROWS), skipped)
        self.assertEqual([s["row_number"] for s in skipped], [5, 6])

    def test_clean_file_reports_nothing(self):
        skipped = []
        clean = "Date,Narration,Debit,Credit,Balance\n01/10/2026,UPI/SWIGGY,450,,49550\n"
        parse_statement_file(self._write("s.csv", clean), skipped)
        self.assertEqual(skipped, [])

    def test_collector_is_optional(self):
        rows = parse_statement_file(self._write("s.csv", CSV_WITH_BAD_ROWS))
        self.assertEqual(len(rows), 2)

    def test_xlsx_reports_rows_with_unreadable_dates(self):
        path = os.path.join(self.tmp.name, "s.xlsx")
        pd.read_csv(io.StringIO(CSV_WITH_BAD_ROWS), dtype=str).to_excel(path, index=False)
        skipped = []
        rows = parse_statement_file(path, skipped)
        self.assertEqual(len(rows), 2)
        self.assertEqual([s["raw_date"] for s in skipped], ["31/02/2026", ""])


class UploadEndpointSkippedRowTests(unittest.TestCase):
    """Calls the real upload endpoint with the vault redirected to a temp folder and Gemini stubbed out."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patches = [
            mock.patch.object(main, "resolve_vault", return_value=self.tmp.name),
            mock.patch.object(main, "resolve_unknown_merchants_with_intelligence", return_value=None),
            mock.patch.object(main, "get_authenticated_user", return_value={"id": "skippedrowstest", "is_demo": False}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def _upload(self, *named_contents):
        files = [UploadFile(file=io.BytesIO(text.encode("utf-8")), filename=name) for name, text in named_contents]
        request = Request({"type": "http", "headers": []})
        return asyncio.run(main.upload_statement(request=request, files=files, file=None))

    def test_response_includes_count_and_raw_rows(self):
        res = self._upload(("october.csv", CSV_WITH_BAD_ROWS))
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["transactions_parsed"], 2)
        self.assertEqual(res["skipped_rows_count"], 2)
        self.assertEqual([r["filename"] for r in res["skipped_rows"]], ["october.csv", "october.csv"])
        self.assertEqual([r["row_number"] for r in res["skipped_rows"]], [3, 4])

    def test_skipped_rows_reported_even_when_nothing_is_imported(self):
        only_bad = "Date,Narration,Debit,Credit,Balance\n31/02/2026,UPI/BLINKIT,1200,,48350\n"
        res = self._upload(("bad.csv", only_bad))
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["skipped_rows_count"], 1)
        self.assertEqual(res["skipped_rows"][0]["raw_date"], "31/02/2026")

    def test_clean_upload_reports_zero(self):
        clean = "Date,Narration,Debit,Credit,Balance\n01/10/2026,UPI/SWIGGY,450,,49550\n"
        res = self._upload(("clean.csv", clean))
        self.assertEqual(res["skipped_rows_count"], 0)
        self.assertEqual(res["skipped_rows"], [])

    def test_returned_rows_are_capped_but_count_is_exact(self):
        bad_rows = "".join(f"99/99/2026,ROW {i},10,,1000\n" for i in range(main.MAX_SKIPPED_ROWS_RETURNED + 5))
        text = "Date,Narration,Debit,Credit,Balance\n01/10/2026,UPI/SWIGGY,450,,49550\n" + bad_rows
        res = self._upload(("many.csv", text))
        self.assertEqual(res["skipped_rows_count"], main.MAX_SKIPPED_ROWS_RETURNED + 5)
        self.assertEqual(len(res["skipped_rows"]), main.MAX_SKIPPED_ROWS_RETURNED)


if __name__ == "__main__":
    unittest.main()
