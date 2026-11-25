"""
Statement date parsing.

Indian bank statements write numeric dates day-first (DD/MM/YYYY). A date such as
01/10/2026 is ambiguous on its own, so the order is decided per file:
- if any date in the file has a first number above 12 (e.g. 25/03/2026), the file is day-first;
- if any date has a second number above 12 and none has a first number above 12
  (e.g. 03/25/2026), the file is month-first;
- otherwise (all ambiguous, or conflicting evidence) day-first is assumed.

Year-first dates (2026-10-01) and dates with month names (01 Oct 2026) are never ambiguous.
"""

import datetime
from typing import Iterable, Optional
import re

import pandas as pd

# DD/MM/YYYY, MM/DD/YYYY or 2-digit years, separated by "/", "-", "." or spaces, with an optional time part
_NUMERIC_DATE = re.compile(r"^\s*(\d{1,2})\s*[/.\- ]\s*(\d{1,2})\s*[/.\- ]\s*(\d{4}|\d{2})(?=$|[\sT])")


def detect_day_first(raw_dates: Iterable[object]) -> bool:
    """Decides whether the numeric dates in one file are day-first (True) or month-first (False)."""
    day_first_evidence = False
    month_first_evidence = False
    for raw in raw_dates:
        match = _NUMERIC_DATE.match(str(raw))
        if not match:
            continue
        first, second = int(match.group(1)), int(match.group(2))
        if first > 12 and second <= 12:
            day_first_evidence = True
        elif second > 12 and first <= 12:
            month_first_evidence = True
    return not (month_first_evidence and not day_first_evidence)


def parse_statement_date(raw: object, day_first: bool = True) -> Optional[str]:
    """Returns the date as YYYY-MM-DD, or None if it is not a valid date."""
    text = str(raw).strip()
    if not text or text.lower() in ("nan", "nat", "none"):
        return None

    match = _NUMERIC_DATE.match(text)
    if match:
        first, second, year_text = int(match.group(1)), int(match.group(2)), match.group(3)
        year = int(year_text) + 2000 if len(year_text) == 2 else int(year_text)
        day, month = (first, second) if day_first else (second, first)
        try:
            return datetime.date(year, month, day).isoformat()
        except ValueError:
            return None

    # Year-first (ISO) dates, Excel timestamps and dates with month names are unambiguous
    parsed = pd.to_datetime(text, errors="coerce")
    return parsed.strftime("%Y-%m-%d") if pd.notnull(parsed) else None
