"""
Gemini-Powered Fiduciary Insurance Recommendation Engine for finMan.
Analyzes user financial context, statement-grounded cashflow, detected & declared policies,
and matches against our curated Indian insurance catalog using Gemini 3.5 Flash Lite.
Strictly zero-commission fiduciary guidance.
"""

import os
import json
import re
from typing import Dict, Any, List
import requests
from app.services.insurance.catalog import INSURANCE_CATALOG, find_product_by_id

def call_gemini_insurance_advisor(
    portfolio: Dict[str, Any],
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates tailored, fiduciary insurance advice using Gemini 3.5 Flash Lite.
    Synthesizes HLV requirements, statement cashflow surplus/burn, corporate GMC status,
    and out-of-pocket health vulnerabilities.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Format current portfolio summary for the prompt
    metrics = portfolio.get("metrics", {})
    annual_income = float(metrics.get("annual_income", 1200000.0))
    outstanding_loans = float(metrics.get("outstanding_loans", 0.0))
    dependents = int(metrics.get("dependents_count", 0))
    age = profile.get("age", 30)
    
    life_info = portfolio.get("life_insurance", {})
    health_info = portfolio.get("health_insurance", {})
    motor_info = portfolio.get("motor_insurance", {})
    critical_alerts = portfolio.get("critical_alerts", [])
    arbitrage = portfolio.get("arbitrage", {})

    # Statement cashflow grounding
    cf_context = portfolio.get("cashflow_context", {})
    monthly_inflow = float(cf_context.get("monthly_inflow", annual_income / 12.0))
    monthly_burn = float(cf_context.get("monthly_burn", 0.0))
    monthly_surplus = float(cf_context.get("monthly_surplus", max(0.0, monthly_inflow - monthly_burn)))
    mandatory_burn = float(cf_context.get("mandatory_monthly_burn", monthly_burn * 0.65))
    disc_categories = cf_context.get("discretionary_categories", [])
    has_gmc_only = health_info.get("has_employer_health_only", False)
    has_retail_health = health_info.get("has_retail_health", False)

    # Curated catalog summary for prompt
    catalog_summary = []
    for p in INSURANCE_CATALOG:
        catalog_summary.append({
            "id": p["id"],
            "name": f"{p['insurer']} - {p['product_name']}",
            "category": p["category"],
            "csr_3yr_avg": p.get("csr_3yr_avg"),
            "asr_percentage": p.get("asr_percentage"),
            "icr_percentage": p.get("icr_percentage"),
            "zero_room_rent_capping": p.get("zero_room_rent_capping"),
            "features": p.get("key_features", [])[:2],
            "suitability": p.get("suitability", "")
        })

    prompt = f"""You are FinSight's Fiduciary AI Insurance Advisor for the Indian financial market.
You act strictly in the user's best financial interest (zero commissions, zero sales bias, pure risk protection).

User Profile & Real Statement Cashflow:
- Age: {age} | Dependents: {dependents}
- Annual Take-Home Income: Rs {annual_income:,.0f} (Monthly Inflow: Rs {monthly_inflow:,.0f}/mo)
- Monthly Living Burn: Rs {monthly_burn:,.0f}/mo (Mandatory: Rs {mandatory_burn:,.0f}/mo)
- Net Monthly Statement Surplus: Rs {monthly_surplus:,.0f}/mo
- Top Discretionary Spends: {json.dumps(disc_categories)}
- Outstanding Loans/Debt: Rs {outstanding_loans:,.0f}
- Required Pure Life Cover (HLV): Rs {metrics.get('required_life_cover', 0):,.0f}
- Active Life Cover: Rs {metrics.get('total_life_cover', 0):,.0f} (Status: {life_info.get('status')})
- Active Health Cover: Rs {metrics.get('total_health_cover', 0):,.0f} (Status: {health_info.get('status')})
- Corporate Employer GMC Only: {has_gmc_only} | Retail Health Active: {has_retail_health}
- Out-of-pocket Medical Spend in Statement: Rs {health_info.get('out_of_pocket_medical_spent', 0):,.0f}
- Motor Status: {motor_info.get('status')}
- Active Risk Alerts: {json.dumps(critical_alerts)}
- Traditional LIC Endowment Detected: {bool(arbitrage)}

Curated Available Products in Catalog:
{json.dumps(catalog_summary, indent=2)}

Fiduciary Mandate Rules:
1. AFFORDABILITY AUDIT: Compare each recommendation's monthly cost against the user's monthly surplus (Rs {monthly_surplus:,.0f}/mo).
   - If surplus is healthy (e.g. > Rs 10k), state clearly what % of surplus it uses (e.g., "Consumes only 3.2% of your Rs {monthly_surplus:,.0f}/mo monthly surplus").
   - If surplus is tight or zero, explicitly recommend which discretionary category (from the list above) to trim.
2. CORPORATE GMC SUPER TOP-UP RULE: If the user relies on Employer GMC (has_gmc_only=True), DO NOT push an expensive Rs 20,000/yr retail base policy. Instead, recommend a high-deductible Super Top-Up (e.g. HDFC ERGO Medisure or Care Enhance with Rs 5L deductible for Rs 25L-50L cover) at ~Rs 2,900/yr (Rs 240/mo).
3. ZERO ROOM RENT CAPPING: Warn against policies with room-rent limits that trigger proportionate deductions on doctors and surgeries.
4. PURE TERM ONLY: If HLV protection deficit exists, recommend only pure term life from top CSR insurers (Max Life, HDFC Life, Tata AIA, Kotak). Never recommend ULIPs or endowments.
5. ARBITRAGE GUIDANCE: If traditional LIC is detected, explain how redirecting premiums into Pure Term + Nifty 50 Index Fund creates superior compounding wealth.

Return ONLY a valid JSON object matching this exact schema:
{{
  "summary_verdict": "Clear 2-3 sentence overview grounded in their income, surplus, and primary gaps.",
  "primary_vulnerabilities": [
    "Short bullet describing vulnerability 1",
    "Short bullet describing vulnerability 2"
  ],
  "recommendations": [
    {{
      "priority": 1,
      "category": "LIFE_TERM",
      "action_title": "Secure Rs 2.0 Cr Pure Term Cover",
      "recommended_sum_insured": 20000000,
      "estimated_annual_cost": 13800,
      "estimated_monthly_cost": 1150,
      "matched_product_id": "term_max_life_step",
      "matched_product_name": "Max Life - Smart Total Elite Protection (STEP)",
      "key_metric_badge": "99.51% CSR | 98.2% ASR",
      "affordability_audit": "Consumes only 2.7% of your net monthly surplus (+Rs 41,884/mo). Fully sustainable.",
      "is_super_topup_bridge": false,
      "rationale": "Clear fiduciary reason grounded in their income, dependents, and IRDAI claim settlement ratio.",
      "tax_benefit": "Tax deduction up to Rs 1.5 Lakhs under Section 80C"
    }}
  ],
  "arbitrage_guidance": "Brief fiduciary advice if endowment detected, or empty string if none."
}}
"""

    if not api_key:
        print("[finMan Recommender] GEMINI_API_KEY missing. Generating statement-grounded fiduciary recommendation.")
        return _generate_fallback_recommendations(portfolio, profile)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    try:
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }

        resp = requests.post(endpoint, json=payload, timeout=12)
        if resp.status_code == 200:
            result = resp.json()
            candidates = result.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = json.loads(raw_text)
                return parsed
        else:
            print(f"[finMan Recommender] Gemini API returned {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[finMan Recommender] Error calling Gemini: {e}")

    # Fallback if API fails or network times out
    return _generate_fallback_recommendations(portfolio, profile)

def _generate_fallback_recommendations(portfolio: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generates deterministic, high-quality rule-based recommendations grounded in statement cashflow."""
    metrics = portfolio.get("metrics", {})
    dependents = metrics.get("dependents_count", 0)
    life_gap = metrics.get("life_protection_gap", 0.0)
    total_health = metrics.get("total_health_cover", 0.0)
    has_gmc_only = portfolio.get("health_insurance", {}).get("has_employer_health_only", False)
    arbitrage = portfolio.get("arbitrage", {})
    motor_status = portfolio.get("motor_insurance", {}).get("status", "")

    cf_context = portfolio.get("cashflow_context", {})
    monthly_surplus = float(cf_context.get("monthly_surplus", 0.0))
    disc_cats = cf_context.get("discretionary_categories", [])
    top_disc = disc_cats[0] if disc_cats else None

    recs: List[Dict[str, Any]] = []
    vulnerabilities: List[str] = []
    priority = 1

    # 1. Life Check
    if dependents > 0 and life_gap > 500000:
        vulnerabilities.append(f"Unprotected life cover deficit of ₹{life_gap/10000000:.2f} Cr exposes your {dependents} dependents to debt and living expense risks.")
        annual_cost = 13800
        monthly_cost = round(annual_cost / 12.0, 0)
        
        if monthly_surplus >= monthly_cost * 2:
            pct_used = (monthly_cost / monthly_surplus) * 100
            affordability = f"Consumes only {pct_used:.1f}% of your net monthly surplus (+₹{monthly_surplus:,.0f}/mo). Fully funded without lifestyle impact."
        elif top_disc:
            affordability = f"Consumes ₹{monthly_cost:,.0f}/mo. Can be fully funded by trimming {top_disc['name']} spend from ₹{top_disc['monthly_spend']:,.0f} by ₹{monthly_cost:,.0f}."
        else:
            affordability = f"Estimated at ~₹{monthly_cost:,.0f}/mo. Fund this priority before any new discretionary commitments."

        recs.append({
            "priority": priority,
            "category": "LIFE_TERM",
            "action_title": f"Secure ₹{life_gap/10000000:.1f} Cr Pure Term Life Cover",
            "recommended_sum_insured": round(life_gap, 0),
            "estimated_annual_cost": annual_cost,
            "estimated_monthly_cost": monthly_cost,
            "matched_product_id": "term_max_life_step",
            "matched_product_name": "Max Life - Smart Total Elite Protection (STEP)",
            "key_metric_badge": "99.51% CSR | 98.2% ASR",
            "affordability_audit": affordability,
            "is_super_topup_bridge": False,
            "rationale": "Max Life maintains India's top 3-year average Claim Settlement Ratio (99.51%) and Amount Settlement Ratio (98.2%). Pure term provides uncompromised protection without endowment fees.",
            "tax_benefit": "Tax deduction up to ₹1.5 Lakhs under Section 80C (Old Regime)"
        })
        priority += 1

    # 2. Health Check
    if has_gmc_only:
        vulnerabilities.append("Relying exclusively on corporate employer group insurance creates catastrophic vulnerability during job transitions, layoffs, or post-retirement.")
        annual_cost = 2950
        monthly_cost = round(annual_cost / 12.0, 0)
        
        if monthly_surplus >= monthly_cost * 2:
            pct_used = (monthly_cost / monthly_surplus) * 100
            affordability = f"Consumes just {pct_used:.1f}% of your net surplus (+₹{monthly_surplus:,.0f}/mo). Instant 10X coverage boost for ~₹245/month."
        else:
            affordability = f"At only ~₹245/mo, this is an ultra-high-leverage protection upgrade that bridges your corporate cover."

        recs.append({
            "priority": priority,
            "category": "HEALTH_SUPER_TOPUP",
            "action_title": "Bridge Corporate Cover with ₹25L-₹50L Super Top-Up",
            "recommended_sum_insured": 5000000,
            "estimated_annual_cost": annual_cost,
            "estimated_monthly_cost": monthly_cost,
            "matched_product_id": "super_topup_ergo_medisure",
            "matched_product_name": "HDFC ERGO - my:health Medisure Super Top Up",
            "key_metric_badge": "Zero Room Rent Cap | ₹5L Deductible",
            "affordability_audit": affordability,
            "is_super_topup_bridge": True,
            "rationale": "Instead of spending ₹20,000/yr on a redundant retail policy, a Super Top-Up with ₹5L deductible pairs seamlessly with your employer GMC. It aggregates multiple claims and gives ₹50L shield for under ₹250/month.",
            "tax_benefit": "Tax deduction up to ₹25,000 under Section 80D"
        })
        priority += 1
    elif total_health == 0:
        vulnerabilities.append("Zero health insurance active. Even a single hospitalization can deplete liquid savings and emergency funds.")
        annual_cost = 11400
        monthly_cost = round(annual_cost / 12.0, 0)

        if monthly_surplus >= monthly_cost * 2:
            pct_used = (monthly_cost / monthly_surplus) * 100
            affordability = f"Consumes {pct_used:.1f}% of your monthly surplus (+₹{monthly_surplus:,.0f}/mo). Completely affordable."
        elif top_disc:
            affordability = f"Consumes ₹{monthly_cost:,.0f}/mo. Fund by trimming ~{int((monthly_cost/top_disc['monthly_spend'])*100)}% of your monthly {top_disc['name']} spend."
        else:
            affordability = f"Consumes ~₹{monthly_cost:,.0f}/mo. Critical protection requirement."

        recs.append({
            "priority": priority,
            "category": "HEALTH_COMPREHENSIVE",
            "action_title": "Purchase Base Retail Health Cover (₹10L Base = ₹20L Cover)",
            "recommended_sum_insured": 1000000,
            "estimated_annual_cost": annual_cost,
            "estimated_monthly_cost": monthly_cost,
            "matched_product_id": "health_ergo_optima_secure",
            "matched_product_name": "HDFC ERGO - Optima Secure",
            "key_metric_badge": "2X Cover Day 1 | Zero Room Rent Sub-limit",
            "affordability_audit": affordability,
            "is_super_topup_bridge": False,
            "rationale": "Provides 2X cover from Day 1 (₹20L protection) with zero room-rent sub-limits, avoiding proportionate bill deductions. Includes unlimited automatic restores.",
            "tax_benefit": "Tax deduction up to ₹25,000 under Section 80D"
        })
        priority += 1

    # 3. Personal Accident / Disability Check
    if dependents > 0 or life_gap > 0:
        annual_cost = 3800
        monthly_cost = round(annual_cost / 12.0, 0)
        recs.append({
            "priority": priority,
            "category": "PERSONAL_ACCIDENT",
            "action_title": "Add ₹50L Permanent Disability & Loss of Income Shield",
            "recommended_sum_insured": 5000000,
            "estimated_annual_cost": annual_cost,
            "estimated_monthly_cost": monthly_cost,
            "matched_product_id": "accident_ergo_pa",
            "matched_product_name": "HDFC ERGO - Personal Accident Comprehensive",
            "key_metric_badge": "100% PTD Payout | Weekly Income Benefit",
            "affordability_audit": f"Consumes only ~₹{monthly_cost:,.0f}/mo (~1% of surplus). Unrivaled hedge against accidental earning loss.",
            "is_super_topup_bridge": False,
            "rationale": "Term life pays only upon death; personal accident is the only instrument that replaces earned income during permanent or temporary total disability.",
            "tax_benefit": "Pure asset protection (no Section 80D deduction)"
        })
        priority += 1

    # 4. Motor Check
    if "MISSING" in motor_status:
        vulnerabilities.append("Active vehicle usage detected from fuel/toll debits, but no active motor insurance policy is logged.")
        recs.append({
            "priority": priority,
            "category": "MOTOR_COMPREHENSIVE",
            "action_title": "Verify / Renew Comprehensive Motor Insurance",
            "recommended_sum_insured": 500000,
            "estimated_annual_cost": 11500,
            "estimated_monthly_cost": 958,
            "matched_product_id": "motor_acko_comprehensive",
            "matched_product_name": "Acko - Zero-Depreciation Car Insurance",
            "key_metric_badge": "Zero Dep | 100% Digital Cashless",
            "affordability_audit": "Consumes ~₹958/mo. Protects against third-party liability and accident repairs.",
            "is_super_topup_bridge": False,
            "rationale": "Direct-to-consumer zero commission model eliminates dealer markups. Instant smartphone inspection and 3-day repair turnaround.",
            "tax_benefit": "Personal asset protection (no Section 80D deduction)"
        })

    arbitrage_text = arbitrage.get("insight", "")

    return {
        "summary_verdict": "Prioritize closing your critical protection deficits across life and health insurance to insulate your wealth and family from catastrophic shocks.",
        "primary_vulnerabilities": vulnerabilities or ["Portfolio has solid baseline coverage across key categories."],
        "recommendations": recs,
        "arbitrage_guidance": arbitrage_text
    }
