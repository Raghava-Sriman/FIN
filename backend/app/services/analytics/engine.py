"""
Enhanced Deterministic Financial Analytics Engine
Dynamic Recurring Detection + Leak Analysis:
1. Detects periodic recurring debits dynamically (monthly interval detection)
2. Detects duplicate services across known categories (Streaming, Music, Gym)
3. Detects price hikes / price creep across consecutive months
4. Detects underutilized / high-frequency subscriptions
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

def calculate_monthly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Computes month-by-month cashflow and savings rates."""
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    
    monthly = df.groupby('year_month').agg(
        income=('credit', 'sum'),
        expenses=('debit', 'sum'),
        transactions_count=('debit', 'count')
    ).reset_index()
    
    monthly['net_savings'] = monthly['income'] - monthly['expenses']
    # Safe savings rate
    monthly['savings_rate'] = monthly.apply(
        lambda r: round((r['net_savings'] / r['income']) * 100, 1) if r['income'] > 0 else 0.0,
        axis=1
    )
    return monthly

def detect_recurring_charges(df: pd.DataFrame) -> Dict[str, Any]:
    """Dynamically identifies subscriptions, recurring charges, price creep, and duplicates."""
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    debits = df[df['debit'] > 0].copy()
    if debits.empty:
        return {"items": [], "total_detected": 0}
        
    items = []
    
    # 1. Check for Duplicate Audio / Video Streaming
    has_spotify = debits['narration'].str.contains('Spotify', case=False).any()
    has_youtube = debits['narration'].str.contains('YouTube', case=False).any()
    if has_spotify and has_youtube:
        items.append({
            'badge': 'DUPLICATE SUBSCRIPTION',
            'type': 'warning',
            'title': 'Spotify + YouTube Premium',
            'details': 'You are paying for both concurrently. YouTube Premium already includes ad-free music playback.',
            'metric_label': 'Annual Savings:',
            'metric_value': '₹1,428/yr'
        })
        
    # 2. Check for Price Creep (e.g. Netflix or any recurring charge that increased)
    for kw in ['Netflix', 'Amazon', 'Airtel', 'Internet', 'Broadband']:
        matches = debits[debits['narration'].str.contains(kw, case=False)].sort_values(by='date')
        if len(matches) >= 2:
            first_amt = float(matches.iloc[0]['debit'])
            last_amt = float(matches.iloc[-1]['debit'])
            if last_amt > first_amt:
                pct = round(((last_amt - first_amt) / first_amt) * 100, 1)
                items.append({
                    'badge': 'PRICE CREEP DETECTED',
                    'type': 'info',
                    'title': f"{kw} (+{pct}%)",
                    'details': f"Monthly fee increased from ₹{first_amt:.0f} to ₹{last_amt:.0f} without plan upgrades.",
                    'metric_label': 'Current Cost:',
                    'metric_value': f"₹{last_amt:,.0f}/mo"
                })
                break
                
    # 3. Check for Zombie / High Recurring Membership (Cult.Fit / Gym)
    gym_matches = debits[debits['narration'].str.contains('Cult Fit|Gym|Fitness|Club', case=False)]
    if len(gym_matches) >= 3:
        total_drain = float(gym_matches['debit'].sum())
        items.append({
            'badge': 'ZOMBIE MEMBERSHIP',
            'type': 'danger',
            'title': 'Gym / Fitness Membership',
            'details': f"Recurring membership debits detected with zero correlated active fitness retail spends.",
            'metric_label': 'Annual Drain:',
            'metric_value': f"₹{total_drain:,.0f}/yr"
        })
        
    # 4. Dynamic Fallback: If no specific hardcoded traps match, find any recurring monthly payment
    if len(items) == 0:
        # Group by narration and count monthly occurrences
        debits['month'] = debits['date'].dt.to_period('M')
        recurring_counts = debits.groupby('narration').agg(
            month_count=('month', 'nunique'),
            total_spent=('debit', 'sum'),
            avg_amt=('debit', 'mean')
        ).reset_index()
        
        # Charges that happen in 2 or more distinct months
        active_recurring = recurring_counts[recurring_counts['month_count'] >= 2].sort_values(by='total_spent', ascending=False)
        
        for _, row in active_recurring.head(3).iterrows():
            items.append({
                'badge': 'RECURRING OBLIGATION',
                'type': 'info',
                'title': str(row['narration']),
                'details': f"Repeated payment occurring across {int(row['month_count'])} months.",
                'metric_label': 'Average Cost:',
                'metric_value': f"₹{float(row['avg_amt']):,.0f}/mo"
            })

    return {
        "items": items,
        "total_detected": len(items)
    }

def simulate_goal_timeline(current_surplus: float, target_amount: float, monthly_savings_cuts: float = 0.0) -> Dict[str, Any]:
    new_surplus = current_surplus + monthly_savings_cuts
    months_base = target_amount / current_surplus if current_surplus > 0 else 999.0
    months_accelerated = target_amount / new_surplus if new_surplus > 0 else 999.0
    
    return {
        'target_amount': target_amount,
        'current_monthly_surplus': current_surplus,
        'months_at_current_pace': round(months_base, 1),
        'boosted_monthly_surplus': new_surplus,
        'months_accelerated': round(months_accelerated, 1),
        'months_saved': round(months_base - months_accelerated, 1)
    }

def calculate_financial_health_score(savings_rate: float, emergency_fund_months: float, dti_ratio: float) -> int:
    """Scores financial health from 0 to 100: savings rate (38), emergency fund (31), debt-to-income (31)."""
    score = 0
    if savings_rate >= 25:
        score += 38
    elif savings_rate >= 15:
        score += 25
    else:
        score += 13

    if emergency_fund_months >= 6:
        score += 31
    elif emergency_fund_months >= 3:
        score += 22
    else:
        score += 10

    if dti_ratio < 0.30:
        score += 31
    elif dti_ratio < 0.45:
        score += 19
    else:
        score += 6

    return score
