"""
Goals Planner and Simulation Engine for finMan.
Provides cashflow reality grounding, multi-goal persistence, dynamic discretionary spend levers,
and compound growth simulation with inflation adjustments.
"""

import os
import json
import math
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def _get_goals_file(user_vault_dir: Optional[str] = None) -> str:
    if not user_vault_dir:
        raise ValueError("[Goals] user_vault_dir must be specified so each account's goals stay isolated.")
    os.makedirs(user_vault_dir, exist_ok=True)
    return os.path.join(user_vault_dir, "goals.json")

def get_cashflow_context(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Extracts authentic cashflow figures from the user's statement ledger:
    mean monthly income, mandatory living burn, true surplus, and top discretionary categories.
    """
    if df is None or df.empty:
        return {
            "avg_monthly_income": 120000.0,
            "avg_monthly_expense": 75000.0,
            "avg_monthly_surplus": 45000.0,
            "mandatory_monthly_burn": 50000.0,
            "emergency_fund_3mo": 150000.0,
            "emergency_fund_6mo": 300000.0,
            "discretionary_categories": [
                {"name": "Food Delivery & Dining", "monthly_spend": 8000.0, "max_cut": 4000.0},
                {"name": "Shopping & E-Commerce", "monthly_spend": 6000.0, "max_cut": 3000.0},
                {"name": "Entertainment & Outings", "monthly_spend": 3000.0, "max_cut": 1500.0}
            ],
            "has_data": False
        }

    # Normalize dates and months
    work_df = df.copy()
    if 'date' in work_df.columns:
        work_df['date'] = pd.to_datetime(work_df['date'], errors='coerce')
        work_df['year_month'] = work_df['date'].dt.strftime('%Y-%m')
    else:
        work_df['year_month'] = 'current'

    months_count = max(1, work_df['year_month'].nunique())

    # Total credits & debits
    total_inflow = float(work_df[work_df['credit'] > 0]['credit'].sum())
    total_outflow = float(work_df[work_df['debit'] > 0]['debit'].sum())

    avg_monthly_income = round(total_inflow / months_count, 2)
    avg_monthly_expense = round(total_outflow / months_count, 2)
    avg_monthly_surplus = max(0.0, round(avg_monthly_income - avg_monthly_expense, 2))

    # Mandatory living burn (Fixed Expenses + Variable Essentials)
    debits = work_df[work_df['debit'] > 0]
    mandatory = debits[debits['category'].str.contains(r'Fixed|Variable Essentials|Loan|Rent|Utilities', case=False, na=False)]
    mandatory_total = float(mandatory['debit'].sum()) if not mandatory.empty else (total_outflow * 0.65)
    mandatory_monthly_burn = round(mandatory_total / months_count, 2)

    emergency_fund_3mo = round(mandatory_monthly_burn * 3.0, 0)
    emergency_fund_6mo = round(mandatory_monthly_burn * 6.0, 0)

    # Discretionary categories breakdown
    disc = debits[debits['category'].str.contains(r'Discretionary|Shopping|Dining|Food|Entertainment|Leisure', case=False, na=False)]
    disc_cats: List[Dict[str, Any]] = []

    if not disc.empty:
        grouped = disc.groupby('sub_category')['debit'].sum().sort_values(ascending=False)
        for sub_cat, total_spent in grouped.head(4).items():
            monthly_val = round(float(total_spent) / months_count, 0)
            if monthly_val >= 500.0:
                disc_cats.append({
                    "name": str(sub_cat),
                    "monthly_spend": monthly_val,
                    "max_cut": round(monthly_val * 0.50, 0) # Up to 50% cut realistic
                })

    if not disc_cats:
        disc_cats = [
            {"name": "Food Delivery & Dining", "monthly_spend": 8000.0, "max_cut": 4000.0},
            {"name": "Shopping & E-Commerce", "monthly_spend": 6000.0, "max_cut": 3000.0},
            {"name": "Entertainment & Outings", "monthly_spend": 3000.0, "max_cut": 1500.0}
        ]

    disc_total = sum(c["monthly_spend"] for c in disc_cats)
    net_monthly_cashflow = round(avg_monthly_income - avg_monthly_expense, 2)
    monthly_deficit = max(0.0, round(avg_monthly_expense - avg_monthly_income, 2))

    return {
        "avg_monthly_income": avg_monthly_income,
        "avg_monthly_expense": avg_monthly_expense,
        "avg_monthly_surplus": avg_monthly_surplus,
        "net_monthly_cashflow": net_monthly_cashflow,
        "monthly_deficit": monthly_deficit,
        "mandatory_monthly_burn": mandatory_monthly_burn,
        "emergency_fund_3mo": emergency_fund_3mo,
        "emergency_fund_6mo": emergency_fund_6mo,
        "discretionary_total": disc_total,
        "discretionary_categories": disc_cats,
        "has_data": True
    }

def get_default_goals(user_vault_dir: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Generates sensible default goals based on the user's authentic statement reality."""
    context = get_cashflow_context(df)
    surplus = context["avg_monthly_surplus"]
    ef_target = context["emergency_fund_6mo"]

    # Allocate 40% of surplus to Emergency Fund, 25% to Vacation, 35% to Wealth/Milestone
    alloc_ef = round(max(5000.0, surplus * 0.40), 0)
    alloc_vac = round(max(3000.0, surplus * 0.25), 0)
    alloc_car = round(max(5000.0, surplus * 0.35), 0)

    return [
        {
            "id": "goal_emergency_fund",
            "title": "6-Month Emergency Safety Vault",
            "category": "EMERGENCY",
            "target_amount": ef_target,
            "monthly_allocation": alloc_ef,
            "lumpsum_infusion": 0.0,
            "target_return_cagr": 6.5, # Safe Liquid / Sweep FD
            "is_auto_derived": True,
            "description": "Protects your family against unexpected job loss or medical crises (6x monthly essentials)."
        },
        {
            "id": "goal_vacation",
            "title": "Annual International Vacation",
            "category": "VACATION",
            "target_amount": 250000.0,
            "monthly_allocation": alloc_vac,
            "lumpsum_infusion": 0.0,
            "target_return_cagr": 7.0, # Short-term safe fund
            "is_auto_derived": False,
            "description": "Debt-free holiday funded purely through planned monthly sinking fund."
        },
        {
            "id": "goal_vehicle_downpayment",
            "title": "Vehicle / Asset Down Payment",
            "category": "ASSET",
            "target_amount": 500000.0,
            "monthly_allocation": alloc_car,
            "lumpsum_infusion": 50000.0,
            "target_return_cagr": 9.5, # Balanced advantage / hybrid fund
            "is_auto_derived": False,
            "description": "Large down payment to minimize loan interest liability and tenure."
        }
    ]

def load_user_goals(user_vault_dir: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Loads user goals from vault storage. Returns empty list if no goals have been created."""
    goals_file = _get_goals_file(user_vault_dir)
    if not os.path.exists(goals_file):
        save_user_goals([], user_vault_dir)
        return []
    try:
        with open(goals_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("goals", [])
    except Exception as e:
        print(f"[finMan Goals] Error reading {goals_file}: {e}")
        return []

def save_user_goals(goals: List[Dict[str, Any]], user_vault_dir: Optional[str] = None) -> bool:
    """Saves user goals to JSON vault."""
    goals_file = _get_goals_file(user_vault_dir)
    try:
        with open(goals_file, "w", encoding="utf-8") as f:
            json.dump({"goals": goals}, f, indent=2)
        return True
    except Exception as e:
        print(f"[finMan Goals] Error writing {goals_file}: {e}")
        return False

def add_user_goal(goal_data: Dict[str, Any], user_vault_dir: Optional[str] = None) -> Dict[str, Any]:
    """Adds a new goal to the user's active goals list."""
    goals = load_user_goals(user_vault_dir)
    if not goal_data.get("id"):
        goal_data["id"] = f"goal_{len(goals) + 1}_{int(pd.Timestamp.now().timestamp())}"
    goals.append(goal_data)
    save_user_goals(goals, user_vault_dir)
    return goal_data

def delete_user_goal(goal_id: str, user_vault_dir: Optional[str] = None) -> bool:
    """Removes a goal by ID."""
    goals = load_user_goals(user_vault_dir)
    initial_count = len(goals)
    goals = [g for g in goals if g.get("id") != goal_id]
    if len(goals) < initial_count:
        save_user_goals(goals, user_vault_dir)
        return True
    return False

def simulate_goal_trajectory(
    target_amount: float,
    monthly_allocation: float,
    discretionary_cuts: Optional[Dict[str, float]] = None,
    lumpsum: float = 0.0,
    return_cagr: float = 7.0,
    inflation_rate: float = 0.0,
    avg_monthly_surplus: float = 0.0,
    max_months: int = 120
) -> Dict[str, Any]:
    """
    Computes high-fidelity month-by-month compounding trajectory comparing:
    - Baseline: Simple monthly allocation without cuts and zero compound growth (cash mattress).
    - Optimized: Boosted monthly contribution with discretionary cuts and compound interest.
    """
    cuts_dict = discretionary_cuts or {}
    total_monthly_cuts = float(sum(cuts_dict.values()))
    
    baseline_monthly = max(100.0, monthly_allocation)
    optimized_monthly = baseline_monthly + total_monthly_cuts

    # Monthly rates
    monthly_return_rate = (return_cagr / 100.0) / 12.0
    monthly_inflation_rate = (inflation_rate / 100.0) / 12.0

    now = datetime.now()

    trajectory: List[Dict[str, Any]] = []
    
    curr_baseline = min(lumpsum, target_amount)
    curr_optimized = min(lumpsum, target_amount)
    total_invested_opt: float = min(lumpsum, target_amount)
    total_interest_opt: float = 0.0

    baseline_achieved_month: Optional[int] = None
    optimized_achieved_month: Optional[int] = None
    target_at_opt_goal: float = target_amount

    for m in range(1, max_months + 1):
        target_at_m = target_amount * ((1.0 + monthly_inflation_rate) ** m)

        # Baseline: linear accumulation with zero returns (stops once target reached)
        if baseline_achieved_month is None:
            curr_baseline += baseline_monthly
            if curr_baseline >= target_at_m:
                baseline_achieved_month = m

        # Optimized: compounding with returns
        if optimized_achieved_month is None:
            interest_m = curr_optimized * monthly_return_rate
            total_interest_opt += interest_m
            bal_before_deposit = curr_optimized + interest_m
            
            needed = max(0.0, target_at_m - bal_before_deposit)
            deposit = min(optimized_monthly, needed)
            total_invested_opt += deposit
            curr_optimized = bal_before_deposit + deposit
            
            if curr_optimized >= target_at_m:
                optimized_achieved_month = m
                target_at_opt_goal = target_at_m
        else:
            # Continue tracking trajectory after achievement for visualization
            curr_optimized = (curr_optimized + optimized_monthly) * (1.0 + monthly_return_rate)

        date_m = now + relativedelta(months=m)
        label_m = date_m.strftime("%b '%y")

        # Collect data points (up to 36 months or until both reach goal)
        if m <= 36 or (optimized_achieved_month is None) or (m <= (optimized_achieved_month + 6)):
            trajectory.append({
                "month_index": m,
                "label": label_m,
                "baseline_balance": round(curr_baseline, 0),
                "optimized_balance": round(curr_optimized, 0),
                "target_amount": round(target_at_m, 0)
            })

        if baseline_achieved_month and optimized_achieved_month and m >= max(baseline_achieved_month, optimized_achieved_month) + 3:
            break

    opt_m = optimized_achieved_month if optimized_achieved_month else max_months
    base_m = baseline_achieved_month if baseline_achieved_month else max_months

    months_saved = max(0, base_m - opt_m)
    target_date = now + relativedelta(months=opt_m)

    # Clean exact figures:
    total_invested = round(total_invested_opt, 0)
    total_interest_earned = max(0.0, round(target_at_opt_goal - total_invested, 0))

    # Real-world feasibility assessment
    available_pool = avg_monthly_surplus + total_monthly_cuts
    if monthly_allocation <= avg_monthly_surplus and avg_monthly_surplus > 0:
        feasibility_status = "fully_funded"
        feasibility_message = f"Allocating ₹{int(monthly_allocation):,}/month is fully supported by your regular monthly surplus of ₹{int(avg_monthly_surplus):,}."
    elif monthly_allocation <= available_pool and total_monthly_cuts > 0:
        feasibility_status = "funded_with_cuts"
        surplus_gap = int(max(0, monthly_allocation - avg_monthly_surplus))
        feasibility_message = f"Exceeds base surplus by ₹{surplus_gap:,}, but is 100% funded by your unlocked discretionary cuts (+₹{int(total_monthly_cuts):,}/mo)."
    else:
        deficit = int(monthly_allocation - available_pool)
        feasibility_status = "deficit"
        feasibility_message = f"Funding gap of ₹{deficit:,}/month. Requires unlocking further spending cuts or boosting monthly income to sustain this pace."

    return {
        "target_amount": target_amount,
        "lumpsum_infusion": lumpsum,
        "baseline_monthly": baseline_monthly,
        "optimized_monthly": optimized_monthly,
        "monthly_cuts_unlocked": total_monthly_cuts,
        "return_cagr": return_cagr,
        "inflation_rate": inflation_rate,
        "optimized_months": opt_m,
        "baseline_months": base_m,
        "months_saved": months_saved,
        "target_completion_date": target_date.strftime("%B %Y"),
        "total_invested": total_invested,
        "total_interest_earned": total_interest_earned,
        "feasibility_status": feasibility_status,
        "feasibility_message": feasibility_message,
        "trajectory": trajectory
    }
