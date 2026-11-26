"""
FinSight evaluation suite: categorization accuracy (synthetic and real), rules-only vs
rules + Gemini, review flags, and Finneas grounding. Writes a markdown report and the raw
results as JSON to evals/reports/ (gitignored).

Everything runs in a temporary data directory through the app's own functions; nothing is
written to vault_storage, and no web server or deployed service is involved. Gemini is used
through the key in backend/.env (read by the app itself). The per-account daily AI limit is
not involved, because the services are called directly.

Usage (from backend/):
  python evals/run_evals.py                         # synthetic categorization + Finneas, 3 AI runs
  python evals/run_evals.py --real evals/private/real_labeled.csv --only real
  python evals/run_evals.py --runs 1 --skip-finneas
  python evals/run_evals.py --skip-ai               # rules only, no Gemini calls
"""

import argparse
import atexit
import collections
import datetime as dt
import json
import os
import re
import shutil
import statistics
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
sys.path.insert(0, HERE)

# Isolated storage before the app is imported (config reads it at import time)
EVAL_ROOT = tempfile.mkdtemp(prefix="finsight_eval_")
os.environ["FINSIGHT_DATA_DIR"] = EVAL_ROOT
os.environ["FINSIGHT_SKIP_DEMO_WARMUP"] = "1"
os.environ.pop("FINSIGHT_ENV", None)
atexit.register(shutil.rmtree, EVAL_ROOT, ignore_errors=True)

import pandas as pd  # noqa: E402
import requests  # noqa: E402

from main import ingest_statement_file, rebuild_active_ledger, save_manifest, get_current_df  # noqa: E402
from app.services.categorizer.merchant_intelligence import (  # noqa: E402
    SUB_TO_MACRO, load_merchant_dictionary, normalize_merchant_key,
)
from app.services.chat.agent import COULD_NOT_ANSWER_REPLY, run_finneas_chat  # noqa: E402
import finneas_questions as FQ  # noqa: E402

DATA_DIR = os.path.join(HERE, "data")
REPORTS_DIR = os.path.join(HERE, "reports")
STATEMENT = os.path.join(DATA_DIR, "student_statement.csv")
LABELS = os.path.join(DATA_DIR, "student_labels.csv")
HARD_CASES = ["allowance", "friends", "refund_cashback", "cryptic"]
HARD_CASE_NAMES = {
    "allowance": "Pocket money / allowance counted as income",
    "friends": "Transfers to and from friends",
    "refund_cashback": "Refunds and cashbacks",
    "cryptic": "Cryptic merchant narrations",
}

# ---------------- Gemini call accounting (counts only; URLs carry the key and are never logged) ----------------

GEMINI = collections.Counter()
_original_post = requests.post


def _counting_post(url, *args, **kwargs):
    is_gemini = "generativelanguage.googleapis.com" in str(url)
    try:
        resp = _original_post(url, *args, **kwargs)
    except Exception:
        if is_gemini:
            GEMINI["calls"] += 1
            GEMINI["errors"] += 1
            GEMINI["exception"] += 1
        raise
    if is_gemini:
        GEMINI["calls"] += 1
        if resp.status_code != 200:
            GEMINI["errors"] += 1
            GEMINI[f"http_{resp.status_code}"] += 1
    return resp


requests.post = _counting_post


def gemini_delta(before):
    return {k: GEMINI[k] - before.get(k, 0) for k in GEMINI if GEMINI[k] - before.get(k, 0)}


# ---------------- categorization ----------------

KEY = ["date", "narration", "debit", "credit"]


def normalise_keys(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["narration"] = df["narration"].astype(str)
    for c in ("debit", "credit"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).round(2)
    return df


def run_pipeline(statement_path, use_ai):
    """Ingests a statement exactly like an upload, in a fresh vault. Returns (ledger, dictionary, vault, gemini stats)."""
    vault = tempfile.mkdtemp(prefix="vault_", dir=EVAL_ROOT)
    before = dict(GEMINI)
    gate = None if use_ai else (lambda: False)  # False = what the app does when AI is unavailable or over the limit
    meta = ingest_statement_file(statement_path, "eval statement", vault, ai_gate=gate)
    if not meta:
        raise RuntimeError(f"Statement could not be parsed: {statement_path}")
    save_manifest([meta], vault)
    rebuild_active_ledger(vault)
    ledger = get_current_df(vault)
    return ledger, load_merchant_dictionary(vault), vault, gemini_delta(before)


def compare(ledger, labels, dictionary):
    led = normalise_keys(ledger)
    lab = normalise_keys(labels)
    m = lab.merge(led[KEY + ["merchant", "category", "sub_category"]], on=KEY, how="left")
    m["predicted_sub"] = m["sub_category"].fillna("(missing from ledger)")
    m["predicted_cat"] = m["category"].fillna("(missing from ledger)")
    m["sub_ok"] = m["predicted_sub"] == m["expected_sub_category"]
    m["cat_ok"] = m["predicted_cat"] == m["expected_category"]

    def decided_by(row):
        if pd.isna(row["merchant"]):
            return "missing"
        entry = dictionary.get(normalize_merchant_key(str(row["merchant"])))
        if entry and entry.get("sub_category") == row["predicted_sub"]:
            return {"rule": "merchant rule", "llm": "AI", "fallback": "review fallback", "user": "user edit"}.get(
                entry.get("source"), entry.get("source", "dictionary"))
        return "narration rules"

    m["decided_by"] = m.apply(decided_by, axis=1)
    m["merchant_key"] = m["merchant"].fillna("").astype(str).map(normalize_merchant_key)
    return m


def acc(series):
    return round(100.0 * float(series.mean()), 1) if len(series) else None


def metrics(m):
    per_cat = []
    for sub, g in m.groupby("expected_sub_category"):
        wrong = g.loc[~g["sub_ok"], "predicted_sub"].value_counts()
        per_cat.append({"category": sub, "n": len(g), "sub_acc": acc(g["sub_ok"]), "macro_acc": acc(g["cat_ok"]),
                        "most_common_wrong": f"{wrong.index[0]} ({int(wrong.iloc[0])})" if len(wrong) else ""})
    hard = {}
    for h in HARD_CASES:
        g = m[m["hard_case"].fillna("") == h]
        if len(g):
            hard[h] = {"n": len(g), "sub_acc": acc(g["sub_ok"]), "macro_acc": acc(g["cat_ok"])}
    return {
        "n": len(m),
        "sub_acc": acc(m["sub_ok"]),
        "macro_acc": acc(m["cat_ok"]),
        "missing": int((m["decided_by"] == "missing").sum()),
        "per_category": sorted(per_cat, key=lambda r: -r["n"]),
        "hard_cases": hard,
        "decided_by": m["decided_by"].value_counts().to_dict(),
        "acc_by_decider": {k: acc(g["sub_ok"]) for k, g in m.groupby("decided_by")},
    }


def review_flags(m, dictionary):
    flagged = [k for k, e in dictionary.items() if e.get("needs_review")]
    amb_by_key = m.groupby("merchant_key")["ambiguous"].apply(lambda s: bool((s.fillna("no") == "yes").any())).to_dict()
    genuinely = [k for k in flagged if amb_by_key.get(k)]
    amb_keys = {k for k, v in amb_by_key.items() if v}
    return {
        "merchants_total": len(dictionary),
        "flagged": len(flagged),
        "flagged_genuinely_ambiguous": len(genuinely),
        "flagged_clear": len(flagged) - len(genuinely),
        "ambiguous_merchants": len(amb_keys),
        "ambiguous_not_flagged": len(amb_keys - set(flagged)),
        "flagged_keys": sorted(flagged),
        "ambiguous_not_flagged_keys": sorted(amb_keys - set(flagged)),
    }


# ---------------- real data ----------------

REAL_COLUMNS = ["date", "narration", "debit", "credit", "correct_category", "ambiguous"]
BUSINESS_WORDS = re.compile(r"\b(PVT|LTD|LIMITED|LLP|TECHNOLOGIES|TECH|INDIA|STORES?|ENTERPRISES?|SERVICES|MART|CAFE|"
                            r"RESTAURANT|HOTEL|FOODS?|PHARMA|MEDICAL|TRADERS|AGENC(Y|IES)|CORP|INC|BANK|PAY|RETAIL)\b", re.I)


def parse_date(value):
    """ISO dates as written; anything else day-first (Indian bank format)."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", value):
        return pd.to_datetime(value[:10], format="%Y-%m-%d", errors="coerce")
    return pd.to_datetime(value, dayfirst=True, errors="coerce")


def load_real(path):
    raw = pd.read_csv(path, dtype=str).fillna("")
    raw.columns = [c.strip().lower() for c in raw.columns]
    missing = [c for c in REAL_COLUMNS if c not in raw.columns]
    if missing:
        raise SystemExit(f"Real-data CSV is missing columns: {', '.join(missing)} (see evals/README.md)")
    raw = raw[raw["narration"].str.strip() != ""].copy()
    raw["date"] = raw["date"].str.strip().map(parse_date)
    bad_dates = int(raw["date"].isna().sum())
    raw = raw.dropna(subset=["date"])
    for c in ("debit", "credit"):
        raw[c] = pd.to_numeric(raw[c].str.replace(",", "").str.strip(), errors="coerce").fillna(0.0).round(2)
    raw["correct_category"] = raw["correct_category"].str.strip()
    invalid = raw.loc[~raw["correct_category"].isin(SUB_TO_MACRO), "correct_category"].value_counts().to_dict()
    raw = raw[raw["correct_category"].isin(SUB_TO_MACRO)]
    labels = pd.DataFrame({
        "date": raw["date"].dt.strftime("%Y-%m-%d"), "narration": raw["narration"], "debit": raw["debit"],
        "credit": raw["credit"], "expected_sub_category": raw["correct_category"],
        "expected_category": raw["correct_category"].map(SUB_TO_MACRO),
        "hard_case": raw["hard_case"].str.strip().str.lower() if "hard_case" in raw.columns else "",
        "ambiguous": raw["ambiguous"].str.strip().str.lower().map(lambda v: "yes" if v in ("yes", "y", "1", "true") else "no"),
    })
    dupes = int(labels.duplicated(KEY).sum())
    labels = labels.drop_duplicates(KEY)
    stmt_dir = tempfile.mkdtemp(prefix="real_", dir=EVAL_ROOT)
    stmt_path = os.path.join(stmt_dir, "real_statement.csv")
    pd.DataFrame({
        "Date": pd.to_datetime(labels["date"]).dt.strftime("%d/%m/%Y"), "Narration": labels["narration"],
        "Withdrawal Amt.": labels["debit"].map(lambda v: f"{v:.2f}" if v else ""),
        "Deposit Amt.": labels["credit"].map(lambda v: f"{v:.2f}" if v else ""),
    }).to_csv(stmt_path, index=False)
    notes = {"rows_used": len(labels), "bad_dates_dropped": bad_dates, "duplicate_rows_dropped": dupes,
             "invalid_labels_dropped": invalid}
    return stmt_path, labels, notes


def anonymize(narration, debit, credit):
    """Describes a transaction's shape without names, handles, reference numbers or exact amounts."""
    n = str(narration).upper().strip()
    channel = next((c for p, c in [("UPI", "UPI"), ("NEFT", "NEFT"), ("IMPS", "IMPS"), ("RTGS", "RTGS"), ("POS", "card"),
                                   ("ME DC", "card"), ("ATM", "ATM"), ("ACH", "ACH"), ("NACH", "NACH"), ("REV", "reversal")]
                    if n.startswith(p)), "other")
    parts = [p.strip() for p in re.split(r"[-/]", n) if p.strip()]
    filler = re.compile(r"(DR|CR|P2A|P2M|UPI|NEFT|IMPS|RTGS|NEFT CR|NEFT DR|[A-Z]{4}0[A-Z0-9]{6}|\d+)")
    names = [p for p in parts[1:] if not filler.fullmatch(p)]
    payee = names[0] if names else " ".join(parts[:3])
    if re.search(r"\d{4,}|\.|QR", payee):
        kind = "a QR/merchant code"
    elif BUSINESS_WORDS.search(payee):
        kind = "a business name"
    elif re.fullmatch(r"[A-Z ]{2,40}", payee.strip()) and 1 <= len(payee.split()) <= 3:
        kind = "a short name (person-like)"
    else:
        kind = "an unclear payee"
    amount = debit or credit
    bucket = next(b for lim, b in [(100, "under ₹100"), (500, "₹100–500"), (2000, "₹500–2k"), (10000, "₹2k–10k"),
                                   (float("inf"), "over ₹10k")] if amount < lim)
    keywords = [k for k in ("REFUND", "CASHBACK", "REVERSAL", "SALARY", "STIPEND", "RENT", "EMI", "INTEREST", "RECHARGE")
                if k in n]
    return f"{channel} {'debit' if debit else 'credit'} to/from {kind}, {bucket}" + (f", keyword {'/'.join(keywords).lower()}" if keywords else "")


# ---------------- Finneas ----------------

def run_finneas(ledger, labels, vault, delay):
    truth = normalise_keys(labels)
    led = normalise_keys(ledger)
    led["balance"] = pd.to_numeric(ledger["balance"], errors="coerce")
    results = []
    for q in FQ.QUESTIONS + FQ.OUT_OF_SCOPE:
        exp = q["compute"](led, truth) if "compute" in q else {}
        before = dict(GEMINI)
        t0 = time.time()
        try:
            out = run_finneas_chat(f"eval_{q['id']}_{time.time_ns()}", q["text"], get_current_df(vault), user_vault_dir=vault)
            answer = out["assistant_message"]["content"]
            tools = [t.get("tool_name") for t in out["assistant_message"].get("executed_tools", [])]
        except Exception as e:  # the eval records crashes instead of stopping
            answer, tools = f"(error: {type(e).__name__}: {e})", []
        stats = gemini_delta(before)
        g = FQ.grade(q, exp, answer)
        degraded = COULD_NOT_ANSWER_REPLY in answer or (q["kind"] != "decline" and not stats.get("calls"))
        results.append({
            "id": q["id"], "question": q["text"], "kind": q["kind"], "category_dependent": q.get("category_dependent", False),
            "expected": exp.get("expected"), "names": exp.get("names"), "truth": exp.get("truth"),
            "answer": answer, "tools": tools, "pass": g["pass"], "why": g["why"], "gemini": stats,
            "degraded": degraded, "seconds": round(time.time() - t0, 1),
        })
        time.sleep(delay)
    return results


# ---------------- report ----------------

def rng_str(values, suffix="%"):
    vals = [v for v in values if v is not None]
    if not vals:
        return "n/a"
    if len(vals) == 1 or min(vals) == max(vals):
        return f"{vals[0]}{suffix}"
    return f"{min(vals)}–{max(vals)}{suffix} (median {statistics.median(vals)})"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def categorization_section(title, rules, ai_runs, anonymized=False):
    L = [f"### {title}", ""]
    rm, am = rules["metrics"] if rules else None, [r["metrics"] for r in ai_runs]
    rows = []
    if rm:
        rows.append(["Rules only", rm["n"], f"{rm['sub_acc']}%", f"{rm['macro_acc']}%"])
    if am:
        rows.append([f"Rules + Gemini ({len(am)} run{'s' if len(am) > 1 else ''})", am[0]["n"],
                     rng_str([m["sub_acc"] for m in am]), rng_str([m["macro_acc"] for m in am])])
    L += [md_table(["Pipeline", "Transactions", "Sub-category accuracy", "Top-level category accuracy"], rows), ""]
    if (rm and rm["missing"]) or any(m["missing"] for m in am):
        L += [f"Rows missing from the ledger: rules {rm['missing'] if rm else 'n/a'}, AI runs {[m['missing'] for m in am]}.", ""]

    # per category
    cats = [c["category"] for c in (rm or am[0])["per_category"]]
    rows = []
    for c in cats:
        r = next(x for x in rm["per_category"] if x["category"] == c) if rm else None
        a = [next(x for x in m["per_category"] if x["category"] == c) for m in am]
        rows.append([c, (r or a[0])["n"], f"{r['sub_acc']}%" if r else "n/a", rng_str([x["sub_acc"] for x in a]),
                     (a[0]["most_common_wrong"] if a else r["most_common_wrong"]) or "–"])
    L += ["**Accuracy per category** (sub-category level; the support column is the number of transactions with that true label)", "",
          md_table(["True category", "n", "Rules only", "Rules + Gemini", "Most common wrong prediction (AI run 1)"], rows), ""]

    # hard cases
    hc = [h for h in HARD_CASES if (rm or am[0])["hard_cases"].get(h)]
    if hc:
        rows = []
        for h in hc:
            r = rm["hard_cases"].get(h) if rm else None
            a = [m["hard_cases"].get(h) for m in am]
            rows.append([HARD_CASE_NAMES[h], (r or a[0])["n"],
                         f"{r['sub_acc']}% / {r['macro_acc']}%" if r else "n/a",
                         f"{rng_str([x['sub_acc'] for x in a])} / {rng_str([x['macro_acc'] for x in a])}" if a else "n/a"])
        L += ["**Hard cases** (sub-category accuracy / top-level category accuracy). For allowance, the top-level number answers "
              "\"was it counted as income?\".", "",
              md_table(["Hard case", "n", "Rules only", "Rules + Gemini"], rows), ""]

    # decided by
    rows = []
    for name, run in ([("Rules only", rules)] if rules else []) + [(f"AI run {i}", r) for i, r in enumerate(ai_runs, 1)]:
        m = run["metrics"]
        rows.append([name] + [f"{m['decided_by'].get(k, 0)} ({m['acc_by_decider'].get(k, '–')}%)"
                              for k in ("narration rules", "merchant rule", "AI", "review fallback")])
    L += ["**Which step decided each transaction** (count, and accuracy of that step's decisions)", "",
          md_table(["Run", "Narration rules", "Merchant rule", "AI", "Review fallback"], rows), ""]

    # review flags
    rows = []
    for name, run in ([("Rules only", rules)] if rules else []) + [(f"AI run {i}", r) for i, r in enumerate(ai_runs, 1)]:
        f = run["flags"]
        rows.append([name, f["merchants_total"], f["flagged"], f["flagged_genuinely_ambiguous"], f["flagged_clear"],
                     f"{f['ambiguous_not_flagged']} of {f['ambiguous_merchants']}"])
    L += ["**Review flags** (merchants, not transactions). \"Genuinely ambiguous\" means at least one of the merchant's "
          "transactions is labelled ambiguous: its category can't be told from the narration and amount.", "",
          md_table(["Run", "Merchants", "Flagged for review", "Genuinely ambiguous", "Clear but flagged",
                    "Ambiguous merchants not flagged"], rows), ""]
    return "\n".join(L)


def mismatch_section(title, rules, ai_runs, anonymized=False):
    L = [f"### {title}", ""]
    frames = []
    if rules:
        frames.append(("rules", rules["compare"]))
    for i, r in enumerate(ai_runs, 1):
        frames.append((f"ai{i}", r["compare"]))
    base = frames[0][1]
    wide = base[KEY + ["expected_sub_category", "hard_case", "ambiguous"] + (["note"] if "note" in base else [])].copy()
    for name, f in frames:
        wide[f"{name}_pred"] = f["predicted_sub"].values
        wide[f"{name}_by"] = f["decided_by"].values
        wide[f"{name}_ok"] = f["sub_ok"].values
    ok_cols = [f"{n}_ok" for n, _ in frames]
    wrong = wide[~wide[ok_cols].all(axis=1)]
    L.append(f"{len(wrong)} transactions were wrong in at least one run (of {len(wide)}).")
    L.append("")
    run_names = [n for n, _ in frames]
    if anonymized:
        groups = collections.Counter()
        for _, r in wrong.iterrows():
            desc = anonymize(r["narration"], r["debit"], r["credit"])
            preds = "; ".join(f"{n}: {r[f'{n}_pred']} ({r[f'{n}_by']})" for n in run_names if not r[f"{n}_ok"])
            groups[(desc, r["expected_sub_category"], preds)] += 1
        rows = [[d, e, p, c] for (d, e, p), c in groups.most_common()]
        L.append(md_table(["Transaction shape (anonymized)", "Expected", "Predicted (decided by), per wrong run", "Count"], rows))
    else:
        rows = []
        for _, r in wrong.iterrows():
            amount = r["debit"] or r["credit"]
            preds = [("✓" if r[f"{n}_ok"] else f"{r[f'{n}_pred']} ({r[f'{n}_by']})") for n in run_names]
            rows.append([r["date"], r["narration"], f"{'-' if r['debit'] else '+'}{amount:,.0f}", r["expected_sub_category"],
                         r["hard_case"] or "", r["ambiguous"]] + preds)
        headers = ["Date", "Narration", "Amount", "Expected", "Hard case", "Ambiguous"] + \
                  [{"rules": "Rules only"}.get(n, f"AI run {n[2:]}") for n in run_names]
        L.append(md_table(headers, rows))
    L.append("")
    # patterns
    pat = collections.Counter()
    for name, f in frames:
        for _, r in f[~f["sub_ok"]].iterrows():
            pat[(name, r["expected_sub_category"], r["predicted_sub"], r["decided_by"])] += 1
    rows = [[{"rules": "Rules only"}.get(k[0], f"AI run {k[0][2:]}"), k[1], k[2], k[3], c] for k, c in pat.most_common()]
    L += ["**Failure patterns** (expected → predicted, grouped by the step that decided)", "",
          md_table(["Run", "Expected", "Predicted", "Decided by", "Count"], rows), ""]
    return "\n".join(L)


def finneas_section(finneas_runs):
    L = ["## 4. Finneas grounding", ""]
    n_runs = len(finneas_runs)
    ids = [r["id"] for r in finneas_runs[0]]
    by_id = {i: [run[k] for run in finneas_runs] for k, i in enumerate(ids)}
    in_scope = [i for i in ids if not i.startswith("X")]
    oos = [i for i in ids if i.startswith("X")]

    def score(run, subset):
        rows = [r for r in run if r["id"] in subset]
        return sum(r["pass"] for r in rows), len(rows), sum(r["degraded"] for r in rows)

    rows = []
    for k, run in enumerate(finneas_runs, 1):
        p, n, d = score(run, in_scope)
        p2, n2, d2 = score(run, oos)
        rows.append([f"Run {k}", f"{p}/{n}", f"{p2}/{n2}", d + d2])
    L += [md_table(["Run", "In-scope questions passed", "Out-of-scope declined", "Degraded answers (gave up after retries, or no AI call)"], rows), ""]
    p_in = [score(run, in_scope)[0] for run in finneas_runs]
    p_out = [score(run, oos)[0] for run in finneas_runs]
    L += [f"Range over {n_runs} run(s): in-scope {rng_str(p_in, '')} of {len(in_scope)}, out-of-scope {rng_str(p_out, '')} of {len(oos)}.", ""]

    rows = []
    for i in ids:
        rs = by_id[i]
        r0 = rs[0]
        exp = ", ".join(f"{v:,.2f}" if isinstance(v, (int, float)) else str(v) for v in (r0["expected"] or [])) or "decline"
        if r0.get("names") and r0["kind"] == "number":
            exp += " in " + ", ".join(r0["names"])
        truth = ""
        if r0["category_dependent"] and r0["truth"] != r0["expected"]:
            truth = ", ".join(f"{v:,.2f}" if isinstance(v, (int, float)) else str(v) for v in r0["truth"])
        marks = " ".join(("PASS" if r["pass"] else "FAIL") + ("*" if r["degraded"] else "") for r in rs)
        rows.append([i, r0["question"], exp, truth or "same", marks])
    L += ["**Per question** (expected = computed from the app's ledger for that run, shown for run 1; truth = from the "
          "generator's labels, only when different. `*` marks a degraded answer.)", "",
          md_table(["ID", "Question", "Expected (run 1)", "True value", "Result per run"], rows), ""]

    # expected values that changed between runs (category-dependent questions)
    changed = [i for i in ids if len({json.dumps(r["expected"]) for r in by_id[i]}) > 1]
    if changed:
        L += ["Expected values that differ between runs, because the AI categorized differently: " + ", ".join(changed) + ".", ""]

    L += ["### Full answers", ""]
    for i in ids:
        for k, r in enumerate(by_id[i], 1):
            L += [f"<details><summary><b>{i} run {k}: {'PASS' if r['pass'] else 'FAIL'}</b>{' (degraded)' if r['degraded'] else ''}: "
                  f"{r['question']}</summary>", "",
                  f"- Grading: {r['why']}",
                  f"- Tools called: {', '.join(t for t in r['tools'] if t) or 'none'}",
                  f"- Gemini: {r['gemini'] or 'no calls'}; {r['seconds']} s",
                  "", "```text", r["answer"].strip(), "```", "", "</details>", ""]
    return "\n".join(L)


def build_report(args, synth, real, finneas_runs, gemini_total, started):
    L = [f"# FinSight evaluation report", "",
         f"Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} (took {round((time.time() - started) / 60, 1)} min). "
         f"AI runs: {args.runs if not args.skip_ai else 0}. Gemini calls: {gemini_total.get('calls', 0)}, "
         f"errors: {gemini_total.get('errors', 0)} {({k: v for k, v in gemini_total.items() if k.startswith('http_') or k == 'exception'}) or ''}.", "",
         "## What was tested", "",
         "1. **Categorization accuracy, synthetic.** A generated 12-month student statement with ground-truth labels "
         "(`evals/data/`) is ingested through the real upload pipeline and every transaction's category is compared with its label.",
         "2. **Categorization accuracy, real.** The same comparison on your own labelled transactions" + ("." if real else " (not run in this report)."),
         "3. **Rules vs AI.** Each set is run with AI off (rules only: unknown merchants get the review fallback, as when the "
         "daily AI limit is reached) and with Gemini on, and review flags are counted.",
         "4. **Finneas grounding.** 20 questions whose answers are computed from the ledger, plus 5 out-of-scope questions it should decline.",
         "5. **Variation.** AI-dependent parts run several times; ranges are reported.", "",
         "## Method", "",
         "- The statement goes through `ingest_statement_file` (parser, `clean_narration`, merchant intelligence) and "
         "`rebuild_active_ledger`, in a fresh temporary data directory per run. No HTTP server, no account, no daily AI limit.",
         "- Ledger rows are matched to labels on (date, narration, debit, credit).",
         "- **Sub-category accuracy** compares the app's sub-category with the label; **top-level accuracy** compares the "
         "macro category (Income, Discretionary, ...). \"Decided by\" is inferred from the merchant dictionary: if the "
         "dictionary entry for the transaction's merchant produced the prediction, its source (merchant rule, AI, review "
         "fallback) is shown; otherwise the narration rules decided.",
         "- **Rules only** passes an AI gate that always refuses; **Rules + Gemini** uses the real classifier with the key in `backend/.env`.",
         "- **Finneas** is called with `run_finneas_chat`, one fresh thread per question, on that run's ledger. Grading rules are in "
         "`evals/finneas_questions.py`: amounts must match to the whole rupee; counts and names must appear exactly. "
         "An answer is marked *degraded* when Finneas gave up after its retries or no AI call was made. Gemini errors that a retry recovered from are counted in the Gemini column but do not make an answer degraded.",
         "- **Limitations.** The synthetic statement and its labels were written by the same assistant that worked on this "
         "codebase. The generator was written without opening the categorization rules, but the assistant had read them "
         "earlier in the same session (to document the project), so some narrations could unconsciously suit the rules. "
         "The real-data set is the independent check. Labels marked `ambiguous` are a judgement that the category can't be "
         "told from narration and amount alone.", ""]

    L += ["## Results", "", "## 1 and 3. Categorization", ""]
    if synth:
        L += [categorization_section("Synthetic student statement", synth.get("rules"), synth.get("ai", [])), ""]
    if real:
        notes = real["notes"]
        L += [categorization_section("Real transactions (aggregates only)", real.get("rules"), real.get("ai", [])), "",
              f"Data notes: {notes['rows_used']} rows used; {notes['bad_dates_dropped']} dropped for unreadable dates; "
              f"{notes['duplicate_rows_dropped']} exact duplicates dropped (the ledger merges identical same-day rows); "
              f"invalid labels dropped: {notes['invalid_labels_dropped'] or 'none'}.", ""]
    if not synth and not real:
        L += ["(not run)", ""]
    if finneas_runs:
        L += [finneas_section(finneas_runs), ""]

    L += ["## Failures", ""]
    if synth:
        L += [mismatch_section("Synthetic: every mismatch", synth.get("rules"), synth.get("ai", [])), ""]
    if real:
        L += [mismatch_section("Real: mismatches (anonymized)", real.get("rules"), real.get("ai", []), anonymized=True), ""]
    if finneas_runs:
        rows = []
        for k, run in enumerate(finneas_runs, 1):
            for r in run:
                if not r["pass"]:
                    rows.append([f"{r['id']} run {k}", r["question"], r["why"], "yes" if r["degraded"] else "no"])
        L += ["### Finneas: failed questions", "", md_table(["Question", "Text", "Why it failed", "Degraded"], rows) if rows else "None.", ""]
    L += ["## What the failures suggest fixing", "",
          "_Written after reviewing the results; see the section appended below._", ""]
    return "\n".join(L)


# ---------------- main ----------------

def strip_for_json(result):
    out = {k: v for k, v in result.items() if k not in ("compare", "vault", "ledger")}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=3, help="number of AI runs (default 3)")
    ap.add_argument("--real", help="path to your labelled real-transactions CSV (never committed)")
    ap.add_argument("--only", choices=["synthetic", "real"], help="run only one data set")
    ap.add_argument("--skip-ai", action="store_true", help="rules only; no Gemini calls")
    ap.add_argument("--skip-finneas", action="store_true")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between Finneas questions")
    args = ap.parse_args()
    started = time.time()
    if args.skip_ai:
        args.skip_finneas = True

    synth = real = None
    finneas_runs = []

    if args.only != "real":
        labels = pd.read_csv(LABELS, dtype={"hard_case": str}).fillna({"hard_case": "", "note": ""})
        synth = {"ai": []}
        led, d, vault, g = run_pipeline(STATEMENT, use_ai=False)
        c = compare(led, labels, d)
        synth["rules"] = {"metrics": metrics(c), "flags": review_flags(c, d), "gemini": g, "compare": c}
        print(f"[synthetic] rules only: {synth['rules']['metrics']['sub_acc']}%")
        if not args.skip_ai:
            for k in range(1, args.runs + 1):
                led, d, vault, g = run_pipeline(STATEMENT, use_ai=True)
                c = compare(led, labels, d)
                synth["ai"].append({"metrics": metrics(c), "flags": review_flags(c, d), "gemini": g, "compare": c})
                print(f"[synthetic] AI run {k}: {synth['ai'][-1]['metrics']['sub_acc']}% (gemini {g})")
                if not args.skip_finneas:
                    finneas_runs.append(run_finneas(led, labels, vault, args.delay))
                    passed = sum(r["pass"] for r in finneas_runs[-1])
                    print(f"[finneas] run {k}: {passed}/{len(finneas_runs[-1])} passed")

    if args.real and args.only != "synthetic":
        stmt_path, labels, notes = load_real(args.real)
        real = {"ai": [], "notes": notes}
        led, d, vault, g = run_pipeline(stmt_path, use_ai=False)
        c = compare(led, labels, d)
        real["rules"] = {"metrics": metrics(c), "flags": review_flags(c, d), "gemini": g, "compare": c}
        print(f"[real] rules only: {real['rules']['metrics']['sub_acc']}%")
        if not args.skip_ai:
            for k in range(1, args.runs + 1):
                led, d, vault, g = run_pipeline(stmt_path, use_ai=True)
                c = compare(led, labels, d)
                real["ai"].append({"metrics": metrics(c), "flags": review_flags(c, d), "gemini": g, "compare": c})
                print(f"[real] AI run {k}: {real['ai'][-1]['metrics']['sub_acc']}%")
        for part in [real["rules"]] + real["ai"]:  # merchant keys can contain names: keep only counts for real data
            for key in ("flagged_keys", "ambiguous_not_flagged_keys"):
                part["flags"].pop(key, None)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORTS_DIR, f"eval_report_{stamp}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(build_report(args, synth, real, finneas_runs, dict(GEMINI), started))
    raw = {
        "synthetic": None if not synth else {"rules": strip_for_json(synth["rules"]), "ai": [strip_for_json(r) for r in synth["ai"]]},
        "real": None if not real else {"notes": real["notes"], "rules": strip_for_json(real["rules"]),
                                       "ai": [strip_for_json(r) for r in real["ai"]]},
        "finneas": finneas_runs,
        "gemini_total": dict(GEMINI),
    }
    with open(os.path.join(REPORTS_DIR, f"eval_results_{stamp}.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, default=str)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
