"""
Strategic Multi-Month Financial Audit & Pattern Intelligence Service
Uses 2-stage lossless pattern extraction (deterministic cadence + clustering in Python)
and Gemini 3.5 Flash Lite synthesis for macro lifestyle drift, EMI vs subscription classification,
and capital outlier analysis.
"""

import os
import json
import requests
import pandas as pd
from typing import Dict, Any, List, Optional

def extract_multi_month_dossier(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Lossless feature extraction across the user's multi-month unified ledger."""
    if df is None or df.empty:
        return None

    df_clean = df.copy()
    df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
    df_clean = df_clean.sort_values(by='date')
    df_clean['ym'] = df_clean['date'].dt.to_period('M').astype(str)

    debits = df_clean[df_clean['debit'] > 0].copy()
    credits = df_clean[df_clean['credit'] > 0].copy()

    total_inflow = float(credits['credit'].sum()) if not credits.empty else 0.0
    total_outflow = float(debits['debit'].sum()) if not debits.empty else 0.0
    net_drain = total_inflow - total_outflow

    # 1. Month-over-month trajectory
    monthly = df_clean.groupby('ym').agg(
        debit=('debit', 'sum'),
        credit=('credit', 'sum'),
        count=('debit', 'count')
    ).reset_index()

    trajectory = []
    for _, row in monthly.iterrows():
        trajectory.append({
            "month": str(row['ym']),
            "spend": round(float(row['debit']), 2),
            "income": round(float(row['credit']), 2),
            "tx_count": int(row['count'])
        })

    # 2. Cumulative category breakdown
    if "sub_category" not in debits.columns:
        debits["sub_category"] = debits.get("category", "General")

    cats = debits.groupby('sub_category')['debit'].agg(['sum', 'count']).sort_values(by='sum', ascending=False).reset_index()
    top_categories = []
    for _, row in cats.head(6).iterrows():
        c_amt = round(float(row['sum']), 2)
        pct = round((c_amt / total_outflow * 100), 1) if total_outflow > 0 else 0.0
        top_categories.append({
            "name": str(row['sub_category']),
            "amount": c_amt,
            "count": int(row['count']),
            "percentage": pct
        })

    # 3. Mathematical Cadence Mining (Zero Loss of Recurring Patterns)
    grouped = debits.groupby('narration')
    cadences = []
    for name, group in grouped:
        if len(group) >= 2:
            dates = group['date'].sort_values()
            intervals = dates.diff().dt.days.dropna()
            mean_int = intervals.mean() if len(intervals) > 0 else 0.0
            std_int = intervals.std() if len(intervals) > 1 else 0.0
            months_spanned = group['date'].dt.to_period('M').nunique()
            mean_amt = float(group['debit'].mean())
            std_amt = float(group['debit'].std()) if len(group) > 1 else 0.0
            total_spent = float(group['debit'].sum())

            # Infer candidate classification hint based on cadence and narration
            hint = "Recurring Peer Obligation"
            name_lower = str(name).lower()
            if any(k in name_lower for k in ["loan", "emi", "hdfc bank", "icici", "sbi loan", "account", "xxxxxxxx"]):
                hint = "Fixed Debt / Recurring EMI"
            elif any(k in name_lower for k in ["spotify", "netflix", "youtube", "apple", "google", "prime", "amazon prime", "valume", "gym", "cult"]):
                hint = "Software / Subscription"

            cadences.append({
                "merchant": str(name),
                "inferred_hint": hint,
                "tx_count": len(group),
                "months_spanned": months_spanned,
                "mean_amount": round(mean_amt, 2),
                "std_amount": round(std_amt, 2),
                "avg_interval_days": round(float(mean_int), 1),
                "std_interval_days": round(float(std_int), 1),
                "total_spent": round(total_spent, 2)
            })

    cadences = sorted(cadences, key=lambda x: x['total_spent'], reverse=True)[:6]

    # 4. Top Capital Outliers (Zero Loss of Large Shock Events)
    top_debits = debits.sort_values(by='debit', ascending=False).head(8)
    capital_outliers = []
    for _, row in top_debits.iterrows():
        dt_str = row['date'].strftime('%Y-%m-%d') if pd.notnull(row['date']) else str(row.get('date', ''))
        capital_outliers.append({
            "date": dt_str,
            "amount": round(float(row['debit']), 2),
            "recipient": str(row.get('merchant') or row.get('narration') or 'Unknown'),
            "category": str(row.get('sub_category', 'General'))
        })

    # 5. Micro-Spending Velocity (< Rs 1,000)
    small_spends = debits[debits['debit'] < 1000]
    small_count = len(small_spends)
    small_total = round(float(small_spends['debit'].sum()), 2)
    avg_small_ticket = round(small_total / small_count, 2) if small_count > 0 else 0.0
    pct_small_txs = round((small_count / len(debits) * 100), 1) if not debits.empty else 0.0

    min_date = df_clean['date'].min()
    max_date = df_clean['date'].max()
    period_str = f"{min_date.strftime('%b %Y')} – {max_date.strftime('%b %Y')}" if pd.notnull(min_date) and pd.notnull(max_date) else "Multi-Month Audit"

    return {
        "period": period_str,
        "total_months": len(monthly),
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "net_drain": round(net_drain, 2),
        "total_tx_count": len(df_clean),
        "monthly_trajectory": trajectory,
        "top_categories": top_categories,
        "recurring_cadences": cadences,
        "top_capital_outliers": capital_outliers,
        "micro_spending_velocity": {
            "count": small_count,
            "total": small_total,
            "pct_of_all_txs": pct_small_txs,
            "avg_ticket": avg_small_ticket
        }
    }


def generate_fallback_strategic_audit(dossier: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic rule-based fallback with identical schema."""
    period = dossier.get("period", "Audit Period")
    net_drain = dossier.get("net_drain", 0.0)
    outflow = dossier.get("total_outflow", 0.0)
    inflow = dossier.get("total_inflow", 0.0)
    cadences = dossier.get("recurring_cadences", [])
    cats = dossier.get("top_categories", [])
    micro = dossier.get("micro_spending_velocity", {})

    is_deficit = net_drain < 0

    headline = (
        f"Multi-Month Net Deficit of **₹{abs(net_drain):,.2f}** across **{period}**"
        if is_deficit
        else f"Disciplined Net Surplus of **+₹{net_drain:,.2f}** across **{period}**"
    )

    summary = (
        f"Total expenditures reached **₹{outflow:,.2f}** against cumulative inflows of **₹{inflow:,.2f}**. "
        f"Outflows were heavily concentrated in the top spending categories."
    )

    recurring = []
    for c in cadences[:4]:
        recurring.append({
            "entity": c["merchant"],
            "type_label": c["inferred_hint"],
            "severity": "danger" if c["total_spent"] > 20000 else "warning",
            "cadence_detail": f"Observed across **{c['months_spanned']}** distinct months totaling **₹{c['total_spent']:,.2f}** (average **₹{c['mean_amount']:,.2f}**).",
            "monthly_runrate": f"**₹{c['mean_amount']:,.0f}/mo**"
        })

    patterns = []
    if cats:
        top_cat = cats[0]
        patterns.append({
            "tag": "Capital Concentration",
            "severity": "danger" if top_cat["percentage"] > 40 else "warning",
            "title": f"{top_cat['name']} Led Multi-Month Spend",
            "detail": f"Consumed **₹{top_cat['amount']:,.2f}** (**{top_cat['percentage']}%** of all outflow across {dossier.get('total_months', 0)} months)."
        })

    if micro.get("count", 0) > 0:
        patterns.append({
            "tag": "Micro-Velocity Friction",
            "severity": "info",
            "title": f"{micro['count']} Micro-Transactions Under ₹1,000",
            "detail": f"Accounted for **{micro['pct_of_all_txs']}%** of all transactions, totaling **₹{micro['total']:,.2f}** with an average ticket of **₹{micro['avg_ticket']:,.2f}**."
        })

    recom = (
        "Audit unlabelled recurring account transfers and cap discretionary dining velocity to prevent compound reserve depletion."
    )

    return {
        "period": period,
        "executive_headline": headline,
        "macro_summary": summary,
        "recurring_commitments": recurring,
        "behavioral_patterns": patterns,
        "strategic_recommendation": recom,
        # Backward compatibility for any legacy code:
        "items": [
            {
                "badge": r["type_label"].upper(),
                "type": r["severity"],
                "title": r["entity"],
                "details": r["cadence_detail"],
                "metric_label": "Monthly Run-Rate:",
                "metric_value": r["monthly_runrate"]
            }
            for r in recurring
        ]
    }


def generate_strategic_audit(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates multi-month strategic financial audit using Gemini 3.5 Flash Lite
    grounded in lossless deterministic telemetry.
    """
    dossier = extract_multi_month_dossier(df)
    if not dossier:
        return {
            "period": "No Statements",
            "executive_headline": "No Multi-Month Ledger Data Available",
            "macro_summary": "Upload statements covering at least one month to view strategic intelligence.",
            "recurring_commitments": [],
            "behavioral_patterns": [],
            "strategic_recommendation": "Upload statements to begin automated financial auditing.",
            "items": []
        }

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        return generate_fallback_strategic_audit(dossier)

    system_prompt = """You are FinSight's Chief Strategic Wealth Auditor.
Analyze the user's multi-month behavioral dossier and deliver an executive diagnostic audit across their multi-month financial life.

GROUND RULES:
1. DISTINGUISH RECURRING OBLIGATIONS PROPERLY:
   - Differentiate fixed capital obligations / EMIs / Loan installments (e.g. transfers to Account numbers or Banks) from consumer subscriptions and irregular peer transfers.
   - Never call an account transfer or personal peer contact a 'software subscription'.
2. MARKDOWN BOLDING:
   - Wrap all rupee amounts (e.g. **₹75,000**), percentages (e.g. **54.8%**), merchant/recipient names (e.g. **SRM hotel**, **Sweety**, **Account ...4581**), and timeframes in markdown double-asterisks (**) for instant visual scanning.
   - IMPORTANT: Only use markdown asterisks INSIDE body narrative sentences (cadence_detail, detail, macro_summary, strategic_recommendation).
   - NEVER put markdown asterisks in 'entity', 'type_label', 'tag', or 'title' fields (they must be clean plain text without any asterisks).
3. LONG-TERM TRAJECTORY:
   - Point out how their burn rate evolved across months (e.g., burn accelerating from Q2 to Q3), category concentration, and micro-transaction friction.
4. BE CRISP & FIDUCIARY: Ground every claim in exact figures from the dossier. No generic platitudes like 'save 20%'.

Respond strictly with a valid JSON object matching this schema:
{
  "executive_headline": "Punchy multi-month diagnosis with key figures in **bold**",
  "macro_summary": "1-2 sentence core conclusion of their financial trajectory over the entire statement period with amounts in **bold**",
  "recurring_commitments": [
    {
      "entity": "Entity / recipient name",
      "type_label": "Fixed Debt / Recurring EMI | Software / Subscription | Recurring Peer Obligation",
      "severity": "danger | warning | info",
      "cadence_detail": "Explanation of recurrence with amounts and frequency in **bold**",
      "monthly_runrate": "e.g. **₹15,000/mo**"
    }
  ],
  "behavioral_patterns": [
    {
      "tag": "Natural Contextual Tag (e.g. Lifestyle Burn Acceleration, Capital Drain Dominance, Micro-Velocity Friction, etc.)",
      "severity": "danger | warning | info",
      "title": "Observation title",
      "detail": "Exact narrative with amounts and entities in **bold**"
    }
  ],
  "strategic_recommendation": "1-2 prioritized macro-level actions for their complete financial portfolio with key terms in **bold**."
}"""

    prompt = f"""Multi-Month Financial Dossier:
{json.dumps(dossier, indent=2)}"""

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.15,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            candidates = result.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = json.loads(raw_text)
                parsed["period"] = dossier["period"]

                # Clean any accidental asterisks in structural title/tag/entity fields
                def _strip_stars(v: Any) -> str:
                    return str(v).replace("**", "").strip() if v is not None else ""

                for r in parsed.get("recurring_commitments", []):
                    r["entity"] = _strip_stars(r.get("entity", ""))
                    r["type_label"] = _strip_stars(r.get("type_label", ""))

                for p in parsed.get("behavioral_patterns", []):
                    p["tag"] = _strip_stars(p.get("tag", ""))
                    p["title"] = _strip_stars(p.get("title", ""))

                # Provide backward-compatibility items array
                if "items" not in parsed:
                    parsed["items"] = [
                        {
                            "badge": r.get("type_label", "RECURRING").upper(),
                            "type": r.get("severity", "info"),
                            "title": r.get("entity", "Recurring Charge"),
                            "details": r.get("cadence_detail", ""),
                            "metric_label": "Monthly Run-Rate:",
                            "metric_value": r.get("monthly_runrate", "")
                        }
                        for r in parsed.get("recurring_commitments", [])
                    ]
                return parsed
        print(f"[finMan Strategic Audit] Gemini returned status {resp.status_code}. Using deterministic fallback.")
        return generate_fallback_strategic_audit(dossier)
    except Exception as e:
        print(f"[finMan Strategic Audit] Gemini call failed: {e}. Using deterministic fallback.")
        return generate_fallback_strategic_audit(dossier)
