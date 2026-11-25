"""
Finneas Agent Tool Calling Engine.
Provides deterministic, statement-grounded financial analysis tools for Finneas.
Every tool operates directly on the user's authentic statement ledger and vault storage.
"""

import re
from typing import Dict, Any, List, Optional
import pandas as pd

from app.services.goals.engine import get_cashflow_context, simulate_goal_trajectory

# ----------------- DETERMINISTIC TOOL FUNCTIONS -----------------

def search_transactions_tool(
    df: Optional[pd.DataFrame],
    query: str,
    months_back: Optional[int] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    transaction_type: Optional[str] = "all"
) -> Dict[str, Any]:
    """
    Searches user's transaction ledger by merchant name or keyword query.
    Filters optionally by category, recency (months), minimum amount, or transaction type (debit/credit/all).
    """
    if df is None or df.empty:
        return {"found": False, "message": "No transaction statement ledger loaded in vault."}

    work_df = df.copy()
    if 'debit' not in work_df.columns:
        work_df['debit'] = 0.0
    if 'credit' not in work_df.columns:
        work_df['credit'] = 0.0

    ttype = (transaction_type or "all").lower()
    if ttype == "debit":
        records = work_df[work_df['debit'] > 0].copy()
        records['amount'] = records['debit']
        records['tx_type'] = 'debit'
    elif ttype == "credit":
        records = work_df[work_df['credit'] > 0].copy()
        records['amount'] = records['credit']
        records['tx_type'] = 'credit'
    else:
        # all (debit or credit > 0)
        records = work_df[(work_df['debit'] > 0) | (work_df['credit'] > 0)].copy()
        records['amount'] = records.apply(lambda r: r['debit'] if r['debit'] > 0 else r['credit'], axis=1)
        records['tx_type'] = records.apply(lambda r: 'debit' if r['debit'] > 0 else 'credit', axis=1)

    if records.empty:
        return {"found": False, "message": "No transactions matching criteria recorded."}

    # Keyword search across narration and merchant
    clean_query = query.strip()
    mask = records['narration'].str.contains(re.escape(clean_query), case=False, na=False)
    
    # Also check merchant/sub_category if available
    if 'sub_category' in records.columns:
        mask = mask | records['sub_category'].str.contains(re.escape(clean_query), case=False, na=False)
    if 'category' in records.columns:
        mask = mask | records['category'].str.contains(re.escape(clean_query), case=False, na=False)
    if 'merchant' in records.columns:
        mask = mask | records['merchant'].str.contains(re.escape(clean_query), case=False, na=False)

    filtered = records[mask].copy()

    if category and 'category' in filtered.columns:
        filtered = filtered[filtered['category'].str.contains(re.escape(category), case=False, na=False)]

    if min_amount is not None:
        filtered = filtered[filtered['amount'] >= float(min_amount)]

    # Filter by dates if months_back is given
    if 'date' in filtered.columns:
        filtered['parsed_date'] = pd.to_datetime(filtered['date'], errors='coerce')
        filtered = filtered.sort_values(by='parsed_date', ascending=False)
        if months_back and months_back > 0:
            latest_date = filtered['parsed_date'].max()
            if pd.notnull(latest_date):
                cutoff_date = latest_date - pd.DateOffset(months=months_back)
                filtered = filtered[filtered['parsed_date'] >= cutoff_date]

    count = len(filtered)
    if count == 0:
        return {
            "found": False,
            "query": query,
            "message": f"No transactions matching '{query}' found in your statement ledger."
        }

    total_amount = float(filtered['amount'].sum())
    avg_ticket = round(total_amount / count, 2)
    highest_tx = float(filtered['amount'].max())

    # Monthly distribution breakdown
    monthly_breakdown = {}
    if 'parsed_date' in filtered.columns and not filtered['parsed_date'].dropna().empty:
        filtered['ym'] = filtered['parsed_date'].dt.strftime('%b %Y')
        grouped_months = filtered.groupby('ym')['amount'].sum()
        for ym, amount in grouped_months.items():
            monthly_breakdown[str(ym)] = round(float(amount), 2)

    # Top sample transactions for citations
    sample_txs = []
    for _, row in filtered.head(15).iterrows():
        sample_txs.append({
            "date": str(row.get('date', 'Unknown')),
            "narration": str(row.get('narration', '')),
            "amount": float(row.get('amount', 0.0)),
            "type": str(row.get('tx_type', 'debit')),
            "category": str(row.get('category', '')),
            "sub_category": str(row.get('sub_category', ''))
        })

    return {
        "found": True,
        "query": query,
        "matches_count": count,
        "total_amount": round(total_amount, 2),
        "total_spent": round(total_amount, 2),
        "average_ticket": avg_ticket,
        "highest_transaction": round(highest_tx, 2),
        "monthly_breakdown": monthly_breakdown,
        "transactions_sample": sample_txs
    }

def get_salary_and_inflows_tool(
    df: Optional[pd.DataFrame],
    month: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyzes salary credits, employer deposits, and total inflows for a specific month or overall.
    """
    if df is None or df.empty:
        return {"has_data": False, "message": "No transaction statement ledger loaded in vault."}

    work_df = df.copy()
    if 'credit' not in work_df.columns:
        return {"has_data": False, "message": "No credit column found in ledger."}

    credits = work_df[work_df['credit'] > 0].copy()
    if credits.empty:
        return {
            "has_data": True,
            "salary_detected": False,
            "total_credits": 0.0,
            "message": "No incoming credit transactions recorded in this statement ledger."
        }

    credits['parsed_date'] = pd.to_datetime(credits['date'], errors='coerce')
    credits = credits.dropna(subset=['parsed_date'])
    if credits.empty:
        return {
            "has_data": True,
            "salary_detected": False,
            "total_credits": 0.0,
            "message": "Credit dates could not be parsed."
        }

    credits['month_name'] = credits['parsed_date'].dt.strftime('%B')
    credits['month_short'] = credits['parsed_date'].dt.strftime('%b')
    credits['year_val'] = credits['parsed_date'].dt.year
    credits['ym'] = credits['parsed_date'].dt.strftime('%Y-%m')

    # Salary detection keywords
    salary_keywords = [
        "SALARY", "SAL ", "BY SAL", "SAL/CR", "PAYROLL", "WAGES", "STIPEND",
        "MONTHLY SAL", "CORP PAY", "EMPLOYER", "DIR DEP", "DIRECT DEP", "NEFT/SAL"
    ]

    def is_likely_salary(row) -> bool:
        narr = str(row.get('narration', '')).upper()
        cat = str(row.get('category', '')).upper()
        subcat = str(row.get('sub_category', '')).upper()
        if any(kw in narr for kw in salary_keywords):
            return True
        if "SALARY" in cat or "SALARY" in subcat or "PAYROLL" in cat or "PAYROLL" in subcat:
            return True
        return False

    if month:
        clean_m = str(month).strip().lower()
        if re.match(r'^\d{4}-\d{2}$', clean_m):
            matched = credits[credits['ym'].str.lower() == clean_m]
        else:
            m_prefix = clean_m[:3]
            match_mask = (credits['month_name'].str.lower().str.startswith(m_prefix)) | \
                         (credits['month_short'].str.lower() == m_prefix)
            if year:
                match_mask = match_mask & (credits['year_val'] == int(year))
            matched = credits[match_mask]

        if matched.empty:
            all_available = sorted(credits['parsed_date'].dt.strftime('%B %Y').unique().tolist())
            return {
                "has_data": True,
                "month_queried": month,
                "found_for_month": False,
                "message": f"No credit transactions recorded in {month}. Available statement months: {', '.join(all_available)}",
                "available_months": all_available
            }

        salary_rows = []
        other_credits = []
        total_month_credits = float(matched['credit'].sum())

        for _, r in matched.iterrows():
            tx_info = {
                "date": str(r.get('date', '')),
                "narration": str(r.get('narration', '')),
                "amount": round(float(r.get('credit', 0.0)), 2),
                "category": str(r.get('category', 'Income')),
                "sub_category": str(r.get('sub_category', 'Credit'))
            }
            if is_likely_salary(r):
                salary_rows.append(tx_info)
            else:
                other_credits.append(tx_info)

        salary_detected = len(salary_rows) > 0
        total_salary = sum(s["amount"] for s in salary_rows)

        # Categorize other credits (P2P, Refunds, Interest, etc.)
        subcat_summary = {}
        for r in other_credits:
            subc = r.get("sub_category") or r.get("category") or "Other Inflow"
            subcat_summary[subc] = round(subcat_summary.get(subc, 0.0) + r["amount"], 2)

        return {
            "has_data": True,
            "month_queried": month,
            "found_for_month": True,
            "salary_detected": salary_detected,
            "total_salary_amount": round(total_salary, 2),
            "salary_credits": salary_rows,
            "total_month_inflow": round(total_month_credits, 2),
            "other_credits_count": len(other_credits),
            "other_credits_total": round(total_month_credits - total_salary, 2),
            "credit_sources_breakdown": subcat_summary,
            "all_credits_sample": [
                {
                    "date": str(r.get('date', '')),
                    "narration": str(r.get('narration', '')),
                    "amount": round(float(r.get('credit', 0.0)), 2),
                    "sub_category": str(r.get('sub_category', 'Credit'))
                }
                for _, r in matched.head(15).iterrows()
            ]
        }
    else:
        # Full monthly trend
        monthly_groups = credits.groupby(credits['parsed_date'].dt.strftime('%b %Y'))
        summary_list = []
        for ym, grp in monthly_groups:
            sal_grp = grp[grp.apply(is_likely_salary, axis=1)]
            sal_amt = float(sal_grp['credit'].sum())
            tot_amt = float(grp['credit'].sum())
            summary_list.append({
                "month": str(ym),
                "salary_detected": len(sal_grp) > 0,
                "salary_amount": round(sal_amt, 2),
                "total_inflow": round(tot_amt, 2),
                "credits_count": len(grp)
            })
        return {
            "has_data": True,
            "all_months_inflow_trend": summary_list
        }

def get_category_trends_tool(
    df: Optional[pd.DataFrame],
    category: str,
    period_months: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyzes historical spending velocity and monthly trends for a specific budget category.
    """
    if df is None or df.empty:
        return {"found": False, "message": "No transaction statement ledger loaded in vault."}

    work_df = df.copy()
    debits = work_df[work_df['debit'] > 0].copy()

    # Search in category or sub_category
    clean_cat = category.strip()
    mask = debits['category'].str.contains(re.escape(clean_cat), case=False, na=False)
    if 'sub_category' in debits.columns:
        mask = mask | debits['sub_category'].str.contains(re.escape(clean_cat), case=False, na=False)

    filtered = debits[mask].copy()
    if filtered.empty:
        # Fallback keyword search
        mask2 = debits['narration'].str.contains(re.escape(clean_cat), case=False, na=False)
        filtered = debits[mask2].copy()

    if filtered.empty:
        return {
            "found": False,
            "category": category,
            "message": f"No expenses found matching category or keyword '{category}'."
        }

    total_spent = float(filtered['debit'].sum())
    
    # Date breakdown
    monthly_trend = []
    if 'date' in filtered.columns:
        filtered['parsed_date'] = pd.to_datetime(filtered['date'], errors='coerce')
        filtered['ym'] = filtered['parsed_date'].dt.strftime('%Y-%m')
        grouped = filtered.groupby('ym')['debit'].agg(['sum', 'count']).reset_index()
        grouped = grouped.sort_values(by='ym')
        
        if period_months and period_months > 0:
            grouped = grouped.tail(period_months)

        for _, row in grouped.iterrows():
            monthly_trend.append({
                "month": str(row['ym']),
                "total_spend": round(float(row['sum']), 2),
                "transactions_count": int(row['count'])
            })

    # Top sub-merchants in this category
    top_merchants = []
    if 'sub_category' in filtered.columns:
        top_sub = filtered.groupby('sub_category')['debit'].sum().sort_values(ascending=False).head(5)
        for name, amt in top_sub.items():
            top_merchants.append({"name": str(name), "total_spend": round(float(amt), 2)})

    return {
        "found": True,
        "category": category,
        "total_category_spent": round(total_spent, 2),
        "monthly_trend": monthly_trend,
        "top_sub_categories": top_merchants
    }

def get_cashflow_summary_tool(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Returns authentic baseline cashflow metrics: monthly income, living burn, true surplus, and ending balance.
    """
    if df is None or df.empty:
        return {"has_data": False, "message": "No bank statement loaded."}

    context = get_cashflow_context(df)
    
    # Ending balance
    end_balance = 0.0
    if 'balance' in df.columns and not df['balance'].dropna().empty:
        try:
            end_balance = float(df['balance'].dropna().iloc[-1])
        except Exception:
            end_balance = 0.0

    return {
        "has_data": True,
        "avg_monthly_income": context.get("avg_monthly_income", 0.0),
        "avg_monthly_expense": context.get("avg_monthly_expense", 0.0),
        "avg_monthly_surplus": context.get("avg_monthly_surplus", 0.0),
        "mandatory_monthly_burn": context.get("mandatory_monthly_burn", 0.0),
        "ending_liquid_balance": round(end_balance, 2),
        "emergency_fund_3mo": context.get("emergency_fund_3mo", 0.0),
        "emergency_fund_6mo": context.get("emergency_fund_6mo", 0.0),
        "discretionary_spend_categories": context.get("discretionary_categories", [])
    }

def evaluate_loan_affordability_tool(
    df: Optional[pd.DataFrame],
    requested_loan_amount: float,
    monthly_emi: float,
    tenure_months: Optional[int] = 36,
    loan_purpose: Optional[str] = "Personal/Asset Loan"
) -> Dict[str, Any]:
    """
    Audits whether a requested loan amount and monthly EMI can be safely supported
    by the user's authentic monthly statement surplus without risking insolvency.
    """
    context = get_cashflow_context(df)
    surplus = context.get("avg_monthly_surplus", 0.0)
    income = context.get("avg_monthly_income", 0.0)
    burn = context.get("avg_monthly_expense", 0.0)
    
    emi = float(monthly_emi)
    loan_amt = float(requested_loan_amount)

    # Debt-to-surplus ratio
    debt_to_surplus_pct = round((emi / surplus) * 100, 1) if surplus > 0 else 999.0
    dti_pct = round((emi / income) * 100, 1) if income > 0 else 0.0

    remaining_surplus_after_emi = round(surplus - emi, 2)

    if surplus <= 0 or emi > surplus:
        verdict = "UNSAFE - DEFICIT INDUCING"
        feasibility = "CRITICAL_DEFICIT"
        advice = f"Your current net monthly statement surplus is ₹{surplus:,.0f}/mo. An EMI of ₹{emi:,.0f}/mo will exceed your savings capacity by ₹{abs(remaining_surplus_after_emi):,.0f}/mo, forcing you into emergency reserve depletion or credit card rollover."
    elif emi > surplus * 0.50:
        verdict = "HIGH STRESS - TIGHT SURPLUS"
        feasibility = "HIGH_STRESS"
        advice = f"The ₹{emi:,.0f}/mo EMI consumes {debt_to_surplus_pct}% of your ₹{surplus:,.0f}/mo monthly surplus. While technically affordable, it leaves only ₹{remaining_surplus_after_emi:,.0f}/mo buffer for irregular expenses or medical contingencies."
    else:
        verdict = "HEALTHY & COMFORTABLY AFFORDABLE"
        feasibility = "HEALTHY_AFFORDABLE"
        advice = f"The ₹{emi:,.0f}/mo EMI consumes only {debt_to_surplus_pct}% of your ₹{surplus:,.0f}/mo monthly surplus. You will retain a comfortable ₹{remaining_surplus_after_emi:,.0f}/mo savings buffer for your ongoing goals and emergency cushion."

    return {
        "loan_amount": loan_amt,
        "monthly_emi": emi,
        "tenure_months": tenure_months,
        "current_monthly_surplus": surplus,
        "current_monthly_income": income,
        "remaining_surplus_after_emi": remaining_surplus_after_emi,
        "debt_to_surplus_percentage": debt_to_surplus_pct,
        "debt_to_income_percentage": dti_pct,
        "verdict": verdict,
        "feasibility": feasibility,
        "fiduciary_advice": advice
    }

def simulate_goal_tool(
    df: Optional[pd.DataFrame],
    target_amount: float,
    monthly_allocation: float,
    vehicle_type: Optional[str] = "BALANCED",
    target_months: Optional[int] = 12
) -> Dict[str, Any]:
    """
    Simulates a financial goal compounding trajectory, verifying whether monthly surplus supports it.
    """
    context = get_cashflow_context(df)
    surplus = context.get("avg_monthly_surplus", 45000.0)

    # Return rate based on vehicle
    rates = {"SAFE": 7.0, "BALANCED": 12.0, "GROWTH": 14.5}
    cagr = rates.get(vehicle_type.upper(), 12.0)

    sim = simulate_goal_trajectory(
        target_amount=float(target_amount),
        monthly_allocation=float(monthly_allocation),
        discretionary_cuts={},
        lumpsum=0.0,
        return_cagr=cagr,
        inflation_rate=0.0,
        avg_monthly_surplus=surplus
    )

    return {
        "target_amount": float(target_amount),
        "monthly_allocation": float(monthly_allocation),
        "vehicle_type": vehicle_type,
        "expected_cagr": cagr,
        "months_required": sim.get("optimized_months") or sim.get("months_required") or 12,
        "years_required": round((sim.get("optimized_months") or 12) / 12.0, 1),
        "total_principal_invested": sim.get("total_principal_invested") or sim.get("total_invested"),
        "interest_earned": sim.get("total_wealth_gain_interest") or sim.get("total_interest_earned"),
        "monthly_surplus": surplus,
        "feasibility": sim.get("feasibility_status"),
        "feasibility_note": sim.get("feasibility_message") or sim.get("feasibility_note")
    }

def get_subscriptions_tool(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extracts recurring digital subscriptions and memberships from statement debits.
    """
    if df is None or df.empty:
        return {"has_data": False, "subscriptions": []}

    debits = df[df['debit'] > 0]
    sub_patterns = [
        ("Netflix", r"NETFLIX"),
        ("Spotify", r"SPOTIFY"),
        ("Amazon Prime", r"AMAZON PRIME|PRIME VIDEO|AMZN PRIME"),
        ("YouTube Premium", r"GOOGLE.*YOUTUBE|YOUTUBE PREM"),
        ("Hotstar / Disney+", r"HOTSTAR|DISNEY.*HOTSTAR"),
        ("Gym / Fitness Membership", r"CULT\.FIT|GYM|GOLD.*GYM|ANYTIME FITNESS"),
        ("Apple Services / iCloud", r"APPLE\.COM|ITUNES"),
        ("Google One / Drive", r"GOOGLE.*STORAGE|GOOGLE ONE")
    ]

    subs_found = []
    total_recurring_monthly = 0.0

    for name, pattern in sub_patterns:
        matches = debits[debits['narration'].str.contains(pattern, case=False, regex=True)]
        if not matches.empty:
            avg_amount = float(matches['debit'].iloc[-1])
            total_recurring_monthly += avg_amount
            subs_found.append({
                "service_name": name,
                "monthly_cost": round(avg_amount, 2),
                "last_charged": str(matches['date'].iloc[-1]) if 'date' in matches.columns else "Recent",
                "occurrences_detected": len(matches)
            })

    return {
        "has_data": True,
        "subscriptions_count": len(subs_found),
        "total_monthly_commitment": round(total_recurring_monthly, 2),
        "active_subscriptions": subs_found
    }

def get_top_merchants_tool(
    df: Optional[pd.DataFrame],
    category: Optional[str] = None,
    month: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Returns top merchants ranked by total spend amount and transaction count.
    Supports filtering by specific category (e.g. 'Food', 'Dining', 'Shopping')
    and specific month (e.g. 'last month', 'August', 'September', '2026-09').
    """
    if df is None or df.empty:
        return {"has_data": False, "merchants": []}

    work_df = df.copy()
    debits = work_df[work_df['debit'] > 0].copy()
    if debits.empty:
        return {"has_data": False, "merchants": []}

    debits['parsed_date'] = pd.to_datetime(debits['date'], errors='coerce')
    debits['ym'] = debits['parsed_date'].dt.strftime('%Y-%m')
    debits['month_name'] = debits['parsed_date'].dt.strftime('%B')
    debits['month_short'] = debits['parsed_date'].dt.strftime('%b')

    applied_month_str = None
    if month:
        m_clean = str(month).strip().lower()
        if any(w in m_clean for w in ["last", "latest", "prev", "recent"]):
            valid_yms = sorted(debits['ym'].dropna().unique().tolist())
            if valid_yms:
                latest_ym = valid_yms[-1]
                debits = debits[debits['ym'] == latest_ym]
                applied_month_str = f"last month ({latest_ym})"
        elif re.match(r'^\d{4}-\d{2}$', m_clean):
            debits = debits[debits['ym'].str.lower() == m_clean]
            applied_month_str = m_clean
        else:
            m_prefix = m_clean[:3]
            mask = (debits['month_name'].str.lower().str.startswith(m_prefix)) | \
                   (debits['month_short'].str.lower() == m_prefix)
            debits = debits[mask]
            applied_month_str = month

    if category:
        cat_clean = str(category).strip().lower()
        if any(f in cat_clean for f in ["food", "dining", "stall", "eat", "restaurant", "cafe", "biri", "biryani"]):
            mask = debits['sub_category'].str.contains(r'food|dining|restaurant|cafe', case=False, na=False) | \
                   debits['category'].str.contains(r'food|dining', case=False, na=False) | \
                   debits['narration'].str.contains(r'zomato|swiggy|biri|isthara|domino|mcdonald|kfc|pizza|burger|cafe|tea|coffee|bakery|canteen|mess', case=False, na=False)
        else:
            mask = debits['sub_category'].str.contains(re.escape(cat_clean), case=False, na=False) | \
                   debits['category'].str.contains(re.escape(cat_clean), case=False, na=False) | \
                   debits['narration'].str.contains(re.escape(cat_clean), case=False, na=False)
        debits = debits[mask]

    if debits.empty:
        return {
            "has_data": True,
            "merchants": [],
            "message": f"No expenses found matching '{category or 'all'}' in {applied_month_str or 'ledger'}."
        }

    # Best merchant grouping column
    col = 'merchant' if 'merchant' in debits.columns and debits['merchant'].dropna().nunique() > 1 else 'narration'
    grouped = debits.groupby(col)['debit'].agg(['sum', 'count']).reset_index()
    grouped.columns = ['merchant', 'total_spent', 'tx_count']
    grouped = grouped.sort_values(by='total_spent', ascending=False).head(limit)

    total_sel_spent = float(debits['debit'].sum())
    merchants_list = []
    for rank, (_, row) in enumerate(grouped.iterrows(), start=1):
        merchants_list.append({
            "rank": rank,
            "merchant": str(row['merchant']),
            "total_spent": round(float(row['total_spent']), 2),
            "transactions_count": int(row['tx_count']),
            "average_ticket": round(float(row['total_spent']) / int(row['tx_count']), 2)
        })

    return {
        "has_data": True,
        "category_filter": category,
        "month_filter": applied_month_str,
        "total_spend_in_selection": round(total_sel_spent, 2),
        "top_merchants": merchants_list
    }

# ----------------- GEMINI TOOL DECLARATIONS SCHEMA -----------------

GEMINI_TOOLS_DECLARATIONS = [
    {
        "name": "search_transactions",
        "description": "Searches the user's authentic bank statement ledger for specific merchants, keywords, or expenses. Use whenever the user asks about specific purchases, e.g. 'How much did I spend at McDonalds or Starbucks?'",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Keyword or merchant name, e.g. 'MCDONALDS', 'AMAZON', 'SWIGGY', 'SHELL', 'STARBUCKS'"
                },
                "months_back": {
                    "type": "INTEGER",
                    "description": "Optional number of months back to search, e.g. 3 for past 3 months"
                },
                "category": {
                    "type": "STRING",
                    "description": "Optional category filter, e.g. 'Dining & Delivery'"
                },
                "min_amount": {
                    "type": "NUMBER",
                    "description": "Optional minimum debit amount filter in INR"
                },
                "transaction_type": {
                    "type": "STRING",
                    "description": "Optional filter: 'all', 'debit', or 'credit'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_salary_and_inflows",
        "description": "Analyzes salary credits, employer payroll deposits, and all incoming cashflow/credits for a specific month (e.g. 'August', 'Aug 2026') or across the entire statement ledger. Use when the user asks about their salary, income, earnings, or inflows for any month.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "STRING",
                    "description": "Month name or YYYY-MM string, e.g. 'August', 'Aug', '2026-08', 'September'"
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Optional 4-digit year, e.g. 2026"
                }
            }
        }
    },
    {
        "name": "get_category_trends",
        "description": "Analyzes historical spending velocity and monthly trends for a category (e.g. food, shopping, utilities). Use when user asks 'What are the trends of my food expenses?'",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "The spending category to analyze, e.g. 'Dining', 'Food Delivery', 'Shopping', 'Fuel', 'Entertainment'"
                },
                "period_months": {
                    "type": "INTEGER",
                    "description": "Number of recent months to include in trend"
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "get_cashflow_summary",
        "description": "Returns the user's authentic income, living burn, net monthly surplus, ending bank balance, and emergency fund buffer.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "evaluate_loan_affordability",
        "description": "Audits whether a requested loan amount and monthly EMI can be safely supported by the user's authentic statement surplus. Use when user asks about taking a personal loan, car loan, home loan, or EMI feasibility.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "requested_loan_amount": {
                    "type": "NUMBER",
                    "description": "Total principal loan amount in INR, e.g. 500000"
                },
                "monthly_emi": {
                    "type": "NUMBER",
                    "description": "Expected monthly EMI outflow in INR, e.g. 14000"
                },
                "tenure_months": {
                    "type": "INTEGER",
                    "description": "Loan repayment tenure in months, e.g. 36"
                },
                "loan_purpose": {
                    "type": "STRING",
                    "description": "Purpose of the loan, e.g. 'Car loan', 'Personal loan', 'Home renovation'"
                }
            },
            "required": ["requested_loan_amount", "monthly_emi"]
        }
    },
    {
        "name": "simulate_goal",
        "description": "Simulates compounding growth and timeline for a financial goal (e.g. buying a gadget, emergency fund, vacation, car downpayment).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "target_amount": {
                    "type": "NUMBER",
                    "description": "Target amount in INR to accumulate"
                },
                "monthly_allocation": {
                    "type": "NUMBER",
                    "description": "Monthly savings amount allocated to this goal"
                },
                "vehicle_type": {
                    "type": "STRING",
                    "description": "Investment risk: 'SAFE' (FD 7%), 'BALANCED' (Nifty Index 12%), 'GROWTH' (Flexicap 14.5%)"
                }
            },
            "required": ["target_amount", "monthly_allocation"]
        }
    },
    {
        "name": "get_subscriptions_and_burdens",
        "description": "Identifies active recurring subscriptions (Netflix, Spotify, Prime, Gym, iCloud) and flags monthly recurring leakage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_top_merchants",
        "description": "Ranks the user's highest spending destinations, merchants, or food stalls. Can filter specifically by category (e.g. 'Food', 'Dining', 'Shopping') and by month (e.g. 'last month', 'August', 'September'). Use when user asks 'which food stall / merchant did I spend the most on last month?' or 'what are my highest expenses?'",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Optional category filter, e.g. 'food', 'dining', 'shopping', 'groceries'"
                },
                "month": {
                    "type": "STRING",
                    "description": "Optional month, e.g. 'last month', 'August', 'September', '2026-09'"
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Number of top merchants to rank, default 5"
                }
            }
        }
    }
]

def execute_finneas_tool(
    name: str,
    args: Dict[str, Any],
    df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """Dispatches tool execution to the corresponding deterministic function."""
    if name == "search_transactions":
        return search_transactions_tool(
            df=df,
            query=args.get("query", ""),
            months_back=args.get("months_back"),
            category=args.get("category"),
            min_amount=args.get("min_amount"),
            transaction_type=args.get("transaction_type", "all")
        )
    elif name == "get_salary_and_inflows":
        return get_salary_and_inflows_tool(
            df=df,
            month=args.get("month"),
            year=args.get("year")
        )
    elif name == "get_category_trends":
        return get_category_trends_tool(
            df=df,
            category=args.get("category", ""),
            period_months=args.get("period_months")
        )
    elif name == "get_cashflow_summary":
        return get_cashflow_summary_tool(df=df)
    elif name == "evaluate_loan_affordability":
        return evaluate_loan_affordability_tool(
            df=df,
            requested_loan_amount=args.get("requested_loan_amount", 0.0),
            monthly_emi=args.get("monthly_emi", 0.0),
            tenure_months=args.get("tenure_months", 36),
            loan_purpose=args.get("loan_purpose")
        )
    elif name == "simulate_goal":
        return simulate_goal_tool(
            df=df,
            target_amount=args.get("target_amount", 0.0),
            monthly_allocation=args.get("monthly_allocation", 0.0),
            vehicle_type=args.get("vehicle_type", "BALANCED")
        )
    elif name == "get_subscriptions_and_burdens":
        return get_subscriptions_tool(df=df)
    elif name == "get_top_merchants":
        return get_top_merchants_tool(
            df=df,
            category=args.get("category"),
            month=args.get("month"),
            limit=args.get("limit", 5)
        )
    else:
        return {"error": f"Tool '{name}' is not recognized."}
