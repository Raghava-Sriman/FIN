"""
Monthly AI Insights Service for finMan
Dynamic, non-vague, mathematically grounded monthly diagnostic audits.
Generates 3 to 5 material observations tailored to the specific month's unique reality.
"""

import os
import json
import requests
import pandas as pd
from typing import Dict, Any, List, Optional

def extract_month_context(df: pd.DataFrame, year_month: str) -> Optional[Dict[str, Any]]:
    """Extracts deterministic financial telemetry for the specified month."""
    if df is None or df.empty:
        return None

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
    df_copy['year_month'] = df_copy['date'].dt.to_period('M').astype(str)
    
    m_df = df_copy[df_copy['year_month'] == year_month].copy()
    if m_df.empty:
        return None

    inflow = float(m_df['credit'].sum())
    outflow = float(m_df['debit'].sum())
    net_burn = inflow - outflow
    savings_rate = round((net_burn / inflow) * 100, 1) if inflow > 0 else 0.0

    debits = m_df[m_df['debit'] > 0].copy()
    if "sub_category" not in debits.columns:
        debits["sub_category"] = debits.get("category", "Discretionary")

    # Category Breakdown
    subcats = debits.groupby('sub_category')['debit'].sum().sort_values(ascending=False).reset_index()
    category_breakdown = []
    for _, row in subcats.iterrows():
        cat_name = str(row['sub_category'])
        cat_amt = round(float(row['debit']), 2)
        pct = round((cat_amt / outflow * 100), 1) if outflow > 0 else 0.0
        category_breakdown.append({
            "name": cat_name,
            "amount": cat_amt,
            "percentage": pct
        })

    # Top single expenses
    top_debits = debits.sort_values(by='debit', ascending=False).head(6)
    top_single_expenses = []
    for _, row in top_debits.iterrows():
        dt_str = row['date'].strftime('%Y-%m-%d') if pd.notnull(row['date']) else str(row.get('date', ''))
        merchant_name = str(row.get('merchant') or row.get('narration') or 'Unknown')
        top_single_expenses.append({
            "date": dt_str,
            "amount": round(float(row['debit']), 2),
            "recipient": merchant_name,
            "category": str(row.get('sub_category', 'General'))
        })

    # Spike days detection
    daily = debits.groupby(debits['date'].dt.strftime('%Y-%m-%d'))['debit'].sum().reset_index()
    daily.columns = ['date', 'amount']
    mean_daily = daily['amount'].mean() if not daily.empty else 0
    spike_threshold = max(mean_daily * 1.5, 3000.0)
    spikes = daily[daily['amount'] >= spike_threshold].sort_values(by='amount', ascending=False)
    
    spike_days = []
    for _, row in spikes.iterrows():
        s_date = row['date']
        s_amt = round(float(row['amount']), 2)
        day_txs = debits[debits['date'].dt.strftime('%Y-%m-%d') == s_date].sort_values(by='debit', ascending=False)
        top_cause = ""
        if not day_txs.empty:
            top_cause = str(day_txs.iloc[0].get('merchant') or day_txs.iloc[0].get('narration') or '')
        spike_days.append({
            "date": s_date,
            "daily_spend": s_amt,
            "primary_cause": top_cause
        })

    # Micro-spending velocity (< Rs 1000 debits)
    small_spends = debits[debits['debit'] < 1000]
    small_count = len(small_spends)
    small_total = round(float(small_spends['debit'].sum()), 2)
    avg_ticket = round(small_total / small_count, 2) if small_count > 0 else 0.0

    return {
        "month": year_month,
        "inflow": round(inflow, 2),
        "outflow": round(outflow, 2),
        "net_burn": round(net_burn, 2),
        "savings_rate": savings_rate,
        "transaction_count": len(m_df),
        "categories": category_breakdown,
        "top_expenses": top_single_expenses,
        "spike_days": spike_days,
        "micro_spending": {
            "count": small_count,
            "total": small_total,
            "avg_ticket": avg_ticket
        }
    }


def generate_fallback_insights(context: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback if Gemini is offline, formatted dynamically."""
    month = context["month"]
    net_burn = context["net_burn"]
    outflow = context["outflow"]
    inflow = context["inflow"]
    cats = context.get("categories", [])
    top_expenses = context.get("top_expenses", [])
    spike_days = context.get("spike_days", [])
    micro = context.get("micro_spending", {})

    is_deficit = net_burn < 0
    headline = (
        f"Net Deficit of **₹{abs(net_burn):,.2f}** with Outflow of **₹{outflow:,.2f}**"
        if is_deficit
        else f"Net Surplus of **+₹{net_burn:,.2f}** Saved from **₹{inflow:,.2f}** Inflow"
    )

    observations = []

    # Category concentration
    if cats:
        top_cat = cats[0]
        observations.append({
            "tag": f"{top_cat['name']} Outlay",
            "severity": "danger" if top_cat["percentage"] > 40 else "warning",
            "title": f"Dominant Outflow in {top_cat['name']}",
            "detail": f"Accounted for **₹{top_cat['amount']:,.2f}** (**{top_cat['percentage']}%** of all spending this month)."
        })

    # Spike Decoded
    if spike_days:
        top_spike = spike_days[0]
        observations.append({
            "tag": "Daily Spend Surge",
            "severity": "warning",
            "title": f"Single-Day Surge on {top_spike['date']}",
            "detail": f"Spent **₹{top_spike['daily_spend']:,.2f}** on **{top_spike['date']}**, driven primarily by payments to **{top_spike['primary_cause']}**."
        })

    # Cashflow Disparity
    if is_deficit:
        observations.append({
            "tag": "Cashflow Deficit",
            "severity": "danger",
            "title": "Inflow vs Outflow Deficit",
            "detail": f"Total income of **₹{inflow:,.2f}** was heavily outpaced by **₹{outflow:,.2f}** in outflows, creating a **-₹{abs(net_burn):,.2f}** liquidity drain."
        })

    # Micro habits
    if micro.get("count", 0) > 0:
        observations.append({
            "tag": "Lifestyle Velocity",
            "severity": "info",
            "title": "Everyday Micro-Transactions",
            "detail": f"Logged **{micro['count']}** micro-transactions under ₹1,000 totaling **₹{micro['total']:,.2f}**, with an average ticket of **₹{micro['avg_ticket']:,.2f}**."
        })

    summary = (
        f"Total outflow of **₹{outflow:,.2f}** against an inflow of **₹{inflow:,.2f}**. "
        f"{'Account served primarily as a net spending drain funded from cash reserves.' if is_deficit else 'Maintained disciplined positive cashflow.'}"
    )

    recom = (
        f"Audit top transfers including **₹{top_expenses[0]['amount']:,.2f}** to **{top_expenses[0]['recipient']}** to verify reimbursable balances."
        if top_expenses
        else "Maintain spending velocity below daily average to protect cash surplus."
    )

    return {
        "executive_headline": headline,
        "verdict_summary": summary,
        "observations": observations,
        "fiduciary_recommendation": recom
    }


def generate_monthly_insights(df: pd.DataFrame, year_month: str) -> Dict[str, Any]:
    """
    Generates dynamic, non-vague personal finance insights using Gemini 3.5 Flash Lite
    with deterministic ground-truth telemetry and markdown bold highlighting.
    """
    context = extract_month_context(df, year_month)
    if not context:
        return {
            "executive_headline": f"No Data Found for {year_month}",
            "verdict_summary": "No transactions were recorded in the active ledger for this month.",
            "observations": [],
            "fiduciary_recommendation": "Upload bank statement covering this period to view insights."
        }

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        return generate_fallback_insights(context)

    system_prompt = """You are FinSight's Chief Personal Financial Auditor.
Analyze this month's financial telemetry and extract the 3 to 5 most important, high-impact observations.

GROUND RULES:
1. NO COOKIE-CUTTER TEMPLATES: Do NOT force a rigid predetermined 4-category structure. Identify what ACTUALLY makes THIS specific month unique.
2. DYNAMIC 3 TO 5 POINTS: Provide between 3 to 5 observations, ordered strictly by financial materiality (highest impact first).
3. MARKDOWN BOLDING: You MUST wrap all rupee amounts (e.g. **₹38,470**), merchant/recipient names (e.g. **naa**, **Amruth (IITM EE24)**, **SRM hotel**), percentages (e.g. **48.9%**), and specific dates (e.g. **Oct 15**) in markdown double-asterisks (**) so the UI can highlight them for instant scannability.
4. NATURAL TAGS: Provide a natural, human contextual tag (e.g. 'Peer Capital Drain', 'Academic Outlay', 'Hospitality Spike', 'Daily Lifestyle Velocity', 'Cashflow Deficit') rather than robotic boilerplate.
5. NO VAGUE PLATITUDES: Never say 'save 20%' or 'cook at home'. Cite exact facts and numbers.

Respond strictly with a valid JSON object matching this schema:
{
  "executive_headline": "Concise headline with key amounts in **bold**",
  "verdict_summary": "1-2 sentence core conclusion with key figures in **bold**",
  "observations": [
    {
      "tag": "Natural Contextual Tag",
      "severity": "danger | warning | info | success",
      "title": "Clear observation title",
      "detail": "Exact narrative with amounts, merchants, and dates wrapped in **bold**."
    }
  ],
  "fiduciary_recommendation": "Concrete operational step with key entities in **bold**."
}"""

    prompt = f"""Analyze the financial data for {year_month}:
{json.dumps(context, indent=2)}"""

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
        resp = requests.post(endpoint, json=payload, timeout=12)
        if resp.status_code == 200:
            result = resp.json()
            candidates = result.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = json.loads(raw_text)
                # Ensure observations key exists
                if "observations" not in parsed and "key_findings" in parsed:
                    parsed["observations"] = parsed.pop("key_findings")

                # Clean any accidental asterisks in structural title/tag fields
                for obs in parsed.get("observations", []):
                    if "tag" in obs and obs["tag"]:
                        obs["tag"] = str(obs["tag"]).replace("**", "").strip()
                    if "title" in obs and obs["title"]:
                        obs["title"] = str(obs["title"]).replace("**", "").strip()

                if "executive_headline" in parsed and "observations" in parsed:
                    return parsed
        print(f"[finMan Insights] Gemini returned status {resp.status_code}. Using deterministic fallback.")
        return generate_fallback_insights(context)
    except Exception as e:
        print(f"[finMan Insights] Gemini call failed: {e}. Using deterministic fallback.")
        return generate_fallback_insights(context)
