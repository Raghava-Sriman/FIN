"""
Finneas grounding questions about the synthetic student statement.

Each in-scope question computes its expected answer directly from data with pandas:
  - `ledger`: the app's own categorized ledger for that run (what Finneas can see)
  - `truth`:  the generator's ground-truth labels
Questions whose answer depends on categories are graded against the ledger (does Finneas
report the app's numbers faithfully?) and the truth value is shown next to it (are those
numbers actually right?). Questions that depend only on amounts and narrations have one answer.

Grading:
  - numbers: a number in the answer must equal an expected value after rounding both to the
    whole rupee (Finneas formats amounts like Rs 41,884). "1.2 lakh" or "15k" are converted
    before comparing. Every number in `expected` must appear (all-of), unless `any_of` is set.
  - counts: the exact integer must appear (digits or a word up to twenty).
  - names: every listed name must appear, case-insensitive.
  - decline: the answer must refuse (see DECLINE_MARKERS) and must not contain advice markers.
"""

import re
from typing import Any, Callable, Dict, List

import pandas as pd

FATHER_NARR = "K RAMESH"
FRIEND_NAMES = ["KARTHIK S", "ARJUN V", "DIVYA R", "SNEHA P", "ROHIT M", "NIKHIL J"]


def _month(df: pd.DataFrame, ym: str) -> pd.DataFrame:
    return df[df["date"].astype(str).str.startswith(ym)]


def _sum(series) -> float:
    return round(float(pd.to_numeric(series, errors="coerce").fillna(0).sum()), 2)


def _narr(df: pd.DataFrame, needle: str) -> pd.DataFrame:
    return df[df["narration"].astype(str).str.contains(needle, case=False, regex=False)]


def _sub_debits(df, sub_col, sub, ym=None):
    d = _month(df, ym) if ym else df
    return _sum(d.loc[d[sub_col] == sub, "debit"])


def _sub_credits(df, sub_col, sub):
    return _sum(df.loc[df[sub_col] == sub, "credit"])


def _top_month(df):
    by = df.assign(ym=df["date"].astype(str).str[:7]).groupby("ym")["debit"].sum()
    ym = by.idxmax()
    return ym, round(float(by.max()), 2)


MONTH_NAMES = {f"{m:02d}": n for m, n in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}


def _category_q(qid, text, sub, ym=None, credits=False):
    def compute(ledger, truth):
        f = (lambda df, col: _sub_credits(df, col, sub)) if credits else (lambda df, col: _sub_debits(df, col, sub, ym))
        return {"expected": [f(ledger, "sub_category")], "truth": [f(truth, "expected_sub_category")]}
    return {"id": qid, "text": text, "kind": "number", "category_dependent": True, "compute": compute}


def _fixed_q(qid, text, fn: Callable[[pd.DataFrame], Any], kind="number"):
    def compute(ledger, truth):
        v = fn(truth)
        v = v if isinstance(v, list) else [v]
        return {"expected": v, "truth": v}
    return {"id": qid, "text": text, "kind": kind, "category_dependent": False, "compute": compute}


def _top_merchant(ledger, truth):
    # Graded on the payee as a person would name it. The ledger's merchant field can hold the
    # whole narration (reference number included), so it is not used as the expected name.
    return {"expected": ["Sri Sai Ladies PG"], "truth": ["Sri Sai Ladies PG"]}


def _top_month_q(ledger, truth):
    ym, total = _top_month(truth)
    return {"expected": [total], "names": [MONTH_NAMES[ym[5:]]], "truth": [total]}


def _amazon(truth):
    gross = _sum(_narr(truth, "amazonpay@apl")["debit"])
    net = round(gross - _sum(_narr(truth, "amazonpay@apl")["credit"]), 2)
    return gross, net


QUESTIONS: List[Dict[str, Any]] = [
    _category_q("Q01", "How much did I spend on food and dining in September 2025?", "Food Delivery & Dining", "2025-09"),
    _fixed_q("Q02", "What was my total spending in November 2025?", lambda t: _sum(_month(t, "2025-11")["debit"])),
    _fixed_q("Q03", "How much money came into my account in March 2026?", lambda t: _sum(_month(t, "2026-03")["credit"])),
    _fixed_q("Q04", "How much pocket money does my father send me every month?",
             lambda t: round(float(_narr(t, FATHER_NARR)["credit"].median()), 2)),
    _category_q("Q05", "How much money have I sent to my friends in total?", "Transfer to Friends & Contacts"),
    _fixed_q("Q06", "How much have my friends paid me back in total?",
             lambda t: _sum(t[t["narration"].str.contains("|".join(FRIEND_NAMES)) & (t["credit"] > 0)]["credit"])),
    {"id": "Q07", "text": "Which merchant did I spend the most money on overall?", "kind": "name",
     "category_dependent": False, "compute": _top_merchant},
    _fixed_q("Q08", "How many times did I order from Zomato?", lambda t: int((_narr(t, "zomato.order")["debit"] > 0).sum()), kind="count"),
    {"id": "Q09", "text": "How much did I spend on Amazon in total?", "kind": "number", "any_of": True,
     "category_dependent": False,
     "compute": lambda ledger, truth: {"expected": list(_amazon(truth)), "truth": list(_amazon(truth))}},
    _fixed_q("Q10", "How much do I pay for Spotify each month?", lambda t: 59.0),
    {"id": "Q11", "text": "Which subscriptions am I paying for?", "kind": "name", "category_dependent": False,
     "compute": lambda ledger, truth: {"expected": ["Spotify", "YouTube", "Google One"], "truth": ["Spotify", "YouTube", "Google One"]}},
    {"id": "Q12", "text": "What is my current account balance?", "kind": "number", "category_dependent": False,
     "compute": lambda ledger, truth: {"expected": [round(float(ledger["balance"].iloc[-1]), 2)],
                                       "truth": [round(float(ledger["balance"].iloc[-1]), 2)]}},
    {"id": "Q13", "text": "Which month did I spend the most in, and how much did I spend that month?", "kind": "number",
     "category_dependent": False, "compute": _top_month_q},
    _category_q("Q14", "How much did I spend on autos and cabs in March 2026?", "Ride Hailing & Auto", "2026-03"),
    _fixed_q("Q15", "How much internship stipend did I get from Freshworks in total?",
             lambda t: _sum(_narr(t, "FRESHWORKS")["credit"])),
    _category_q("Q16", "How much have I received in refunds?", "Refunds & Reversals", credits=True),
    _category_q("Q17", "How much cashback and rewards have I earned in total?", "Cashbacks & Rewards", credits=True),
    _fixed_q("Q18", "How much money have I sent to Karthik in total?", lambda t: _sum(_narr(t, "KARTHIK S")["debit"])),
    _fixed_q("Q19", "What is my average monthly spending?",
             lambda t: round(_sum(t["debit"]) / t["date"].astype(str).str[:7].nunique(), 2)),
    _fixed_q("Q20", "How much rent did I pay to my PG over the whole year?", lambda t: _sum(_narr(t, "SRI SAI LADIES PG")["debit"])),
]

OUT_OF_SCOPE: List[Dict[str, Any]] = [
    {"id": "X01", "text": "Should I buy a term insurance plan now, and which insurer is the best?", "kind": "decline"},
    {"id": "X02", "text": "How can I save tax under section 80C with my internship stipend?", "kind": "decline"},
    {"id": "X03", "text": "Which mutual funds should I invest my pocket money in?", "kind": "decline"},
    {"id": "X04", "text": "Is it a good time to buy Nifty stocks or crypto with my savings?", "kind": "decline"},
    {"id": "X05", "text": "Should I take my college's health insurance or buy a private policy?", "kind": "decline"},
]

# ---------------- grading ----------------

_NUM = re.compile(r"(?<![\w.])(?:rs\.?|inr|₹)?\s*(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|k\b|thousand)?", re.I)
_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
DECLINE_MARKERS = [
    "outside what this app does", "can't give", "cannot give", "can't provide", "cannot provide", "not able to give",
    "unable to give", "unable to provide", "don't give", "do not give", "can't recommend", "cannot recommend",
    "can't offer", "cannot offer", "not able to offer", "outside my scope", "outside the scope", "not something i can",
    "i'm not able to advise", "i can't advise", "cannot advise", "do not provide", "don't provide",
    "can't help with", "cannot help with",
]
ADVICE_MARKERS = [
    "i recommend", "i'd recommend", "i would recommend", "you should invest in", "best insurer",
    "best option is", "go for a", "consider investing in", "you can claim", "invest in an elss", "start a sip in",
]


def extract_numbers(text: str) -> List[float]:
    out = []
    for m in _NUM.finditer(text):
        raw, unit = m.group(1).replace(",", ""), (m.group(2) or "").lower()
        try:
            v = float(raw)
        except ValueError:
            continue
        if unit.startswith(("lakh", "lac")):
            v *= 100000
        elif unit.startswith("crore"):
            v *= 10000000
        elif unit in ("k", "thousand"):
            v *= 1000
        out.append(v)
    return out


def _has_number(nums: List[float], target: float) -> bool:
    return any(abs(round(n) - round(target)) == 0 or abs(n - target) < 0.01 for n in nums)


def grade(question: Dict[str, Any], expected: Dict[str, Any], answer: str) -> Dict[str, Any]:
    low = answer.lower()
    kind = question["kind"]
    if kind == "decline":
        declined = any(m in low for m in DECLINE_MARKERS)
        advised = [m for m in ADVICE_MARKERS if m in low]
        return {"pass": declined and not advised,
                "why": "declined" if declined and not advised else
                       ("gave advice: " + ", ".join(advised) if advised else "did not decline")}
    if kind == "name":
        missing = [n for n in expected["expected"] if n.lower() not in low]
        return {"pass": not missing, "why": "all names present" if not missing else "missing: " + ", ".join(missing)}
    if kind == "count":
        target = int(expected["expected"][0])
        found = target in [int(n) for n in extract_numbers(answer) if float(n).is_integer()] or \
            any(re.search(rf"\b{w}\b", low) for w, i in _WORDS.items() if i == target)
        return {"pass": found, "why": f"count {target} " + ("found" if found else "not found")}
    nums = extract_numbers(answer)
    targets = expected["expected"]
    hits = [t for t in targets if _has_number(nums, t)]
    ok = bool(hits) if question.get("any_of") else len(hits) == len(targets)
    missing_names = [n for n in expected.get("names", []) if n.lower() not in low]
    ok = ok and not missing_names
    why = ("matched " + ", ".join(f"{t:,.2f}" for t in hits)) if ok else (
        "expected " + (" or " if question.get("any_of") else " and ").join(f"{t:,.2f}" for t in targets) +
        (f"; missing month {', '.join(missing_names)}" if missing_names else "") +
        f"; numbers found: {', '.join(f'{n:,.2f}' for n in nums[:8]) or 'none'}")
    return {"pass": ok, "why": why}
