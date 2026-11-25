"""
Insurance Declaration and Portfolio Management Engine for finMan.
Handles user-declared policies, persistent JSON storage, bank statement reconciliation,
Human Life Value (HLV) gap analysis, and endowment-vs-term arbitrage simulation.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from app.services.goals.engine import get_cashflow_context

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
DEFAULT_VAULT_DIR = os.path.join(PROJECT_ROOT, "vault_storage")

def _get_profile_file(user_vault_dir: Optional[str] = None) -> str:
    target_dir = user_vault_dir or DEFAULT_VAULT_DIR
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    return os.path.join(target_dir, "insurance_profile.json")

def load_declared_policies(user_vault_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads user-declared insurance policies from persistent vault."""
    profile_file = _get_profile_file(user_vault_dir)
    if not os.path.exists(profile_file):
        return []
    try:
        with open(profile_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("declared_policies", [])
    except Exception as e:
        print(f"[finMan Insurance] Error reading {profile_file}: {e}")
        return []

def save_declared_policies(policies: List[Dict[str, Any]], user_vault_dir: Optional[str] = None) -> bool:
    """Saves user-declared insurance policies to persistent vault."""
    profile_file = _get_profile_file(user_vault_dir)
    try:
        data = {"declared_policies": policies}
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[finMan Insurance] Error writing {profile_file}: {e}")
        return False

def add_declared_policy(policy_data: Dict[str, Any], user_vault_dir: Optional[str] = None) -> Dict[str, Any]:
    """Adds a new declared policy to the persistent store."""
    policies = load_declared_policies(user_vault_dir)
    
    # Generate unique ID if missing
    if not policy_data.get("id"):
        policy_data["id"] = f"decl_pol_{len(policies) + 1}_{int(pd.Timestamp.now().timestamp())}"
    
    # Set default flags
    if "is_employer_provided" not in policy_data:
        policy_data["is_employer_provided"] = (policy_data.get("source") == "EMPLOYER_GMC" or policy_data.get("policy_type") == "EMPLOYER_GMC")
    
    policies.append(policy_data)
    save_declared_policies(policies, user_vault_dir)
    return policy_data

def delete_declared_policy(policy_id: str, user_vault_dir: Optional[str] = None) -> bool:
    """Removes a declared policy by ID."""
    policies = load_declared_policies(user_vault_dir)
    initial_len = len(policies)
    policies = [p for p in policies if p.get("id") != policy_id]
    if len(policies) < initial_len:
        save_declared_policies(policies, user_vault_dir)
        return True
    return False

def clear_declared_policies(user_vault_dir: Optional[str] = None) -> bool:
    """Clears all declared policies."""
    return save_declared_policies([], user_vault_dir)

def set_declared_policies(policies: List[Dict[str, Any]], user_vault_dir: Optional[str] = None) -> bool:
    """Overwrites declared policies with a specific list."""
    return save_declared_policies(policies, user_vault_dir)

# ----------------- RECONCILIATION & DETECTION ENGINE -----------------

def analyze_statement_insurance(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Scans statement transactions to detect insurance debits, vehicle indicators,
    out-of-pocket medical expenditures, loan EMIs, and ending liquidity buffer.
    """
    if df is None or df.empty:
        return {
            "detected_policies": [],
            "medical_spends": 0.0,
            "medical_transactions_count": 0,
            "vehicle_detected": False,
            "vehicle_signals": [],
            "detected_monthly_emi": 0.0,
            "estimated_outstanding_debt": 0.0,
            "ending_balance": 0.0,
            "corporate_gmc_detected": False,
            "corporate_gmc_signals": []
        }

    debits = df[df['debit'] > 0]
    detected_policies: List[Dict[str, Any]] = []

    # 1. Life Insurance Detection
    lic_matches = debits[debits['narration'].str.contains(r'LIC OF INDIA|Life Insurance Corp|ACH D- LIC', case=False, regex=True)]
    for _, row in lic_matches.iterrows():
        premium = float(row['debit'])
        # Traditional Endowment heuristic: 10x - 15x premium
        est_sum_insured = premium * 15.0
        detected_policies.append({
            "id": f"det_life_lic_{row.get('ref_no', 'ref')}",
            "category": "LIFE",
            "policy_type": "TRADITIONAL_ENDOWMENT",
            "insurer_name": "Life Insurance Corporation of India (LIC)",
            "plan_name": "Traditional Endowment / Money-Back",
            "annual_premium": premium,
            "sum_insured": est_sum_insured,
            "source": "STATEMENT_DETECTED",
            "is_traditional_endowment": True,
            "narration": row['narration'],
            "date": str(row['date'])
        })

    pvt_life_matches = debits[debits['narration'].str.contains(r'HDFC LIFE|MAX LIFE|ICICI PRU|TATA AIA|SBI LIFE|BAJAJ ALLIANZ LIFE|KOTAK LIFE', case=False, regex=True)]
    for _, row in pvt_life_matches.iterrows():
        premium = float(row['debit'])
        is_term = bool(re.search(r'CLICK2PROTECT|STEP|IPROTECT|TERM', str(row['narration']), re.IGNORECASE))
        # Pure term heuristic: Rs 1-2 Cr cover for Rs 8k-30k premium
        est_sum_insured = 15000000.0 if (is_term or premium < 30000.0) else (premium * 20.0)
        detected_policies.append({
            "id": f"det_life_pvt_{row.get('ref_no', 'ref')}",
            "category": "LIFE",
            "policy_type": "PURE_TERM" if (is_term or premium < 30000.0) else "TRADITIONAL_LIFE",
            "insurer_name": "Private Life Insurer",
            "plan_name": "Term Protection Plan" if (is_term or premium < 30000.0) else "Life Insurance Plan",
            "annual_premium": premium,
            "sum_insured": est_sum_insured,
            "source": "STATEMENT_DETECTED",
            "is_traditional_endowment": False,
            "narration": row['narration'],
            "date": str(row['date'])
        })

    # 2. Health Insurance Detection
    health_matches = debits[debits['narration'].str.contains(r'STAR HEALTH|CARE HEALTH|HDFC ERGO HEALTH|NIVA BUPA|MANIPALCIGNA|ADITYA BIRLA HEALTH|RELIGARE HEALTH', case=False, regex=True)]
    for _, row in health_matches.iterrows():
        premium = float(row['debit'])
        est_sum_insured = max(500000.0, premium * 30.0)
        detected_policies.append({
            "id": f"det_health_{row.get('ref_no', 'ref')}",
            "category": "HEALTH",
            "policy_type": "RETAIL_HEALTH",
            "insurer_name": str(row['narration'])[:25],
            "plan_name": "Retail Comprehensive Health Cover",
            "annual_premium": premium,
            "sum_insured": est_sum_insured,
            "source": "STATEMENT_DETECTED",
            "is_employer_provided": False,
            "narration": row['narration'],
            "date": str(row['date'])
        })

    # 3. Motor Insurance Detection
    motor_matches = debits[debits['narration'].str.contains(r'ACKO GENERAL|GO DIGIT|ICICI LOMBARD|BAJAJ ALLIANZ GEN|TATA AIG GEN|POLICYBAZAAR MOTOR|NEW INDIA ASSUR', case=False, regex=True)]
    for _, row in motor_matches.iterrows():
        premium = float(row['debit'])
        detected_policies.append({
            "id": f"det_motor_{row.get('ref_no', 'ref')}",
            "category": "MOTOR",
            "policy_type": "MOTOR_COMPREHENSIVE",
            "insurer_name": str(row['narration'])[:25],
            "plan_name": "Comprehensive Vehicle Insurance",
            "annual_premium": premium,
            "sum_insured": 500000.0,
            "source": "STATEMENT_DETECTED",
            "narration": row['narration'],
            "date": str(row['date'])
        })

    # 4. Out-of-pocket Medical Spend Detection
    medical_txs = debits[debits['narration'].str.contains(r'Hospital|Pharmacy|Apollo|Manipal|Clinic|Doctor|MedPlus|Tata 1mg|1mg|PharmEasy|Dr Lal|Metropolis|Fortis|Max Healthcare|Dental', case=False, regex=True)]
    medical_spends = float(medical_txs['debit'].sum()) if not medical_txs.empty else 0.0

    # 5. Vehicle Ownership Detection Signals
    fastag_txs = debits[debits['narration'].str.contains(r'FASTAG|NETC|IHMCL', case=False, regex=True)]
    fuel_txs = debits[debits['narration'].str.contains(r'HPCL|BPCL|IOCL|SHELL|PETROL|DIESEL|FUEL', case=False, regex=True)]
    auto_loan_txs = debits[debits['narration'].str.contains(r'AUTO LOAN|CAR LOAN|VEHICLE LOAN', case=False, regex=True)]
    
    vehicle_detected = (len(fastag_txs) > 0) or (len(fuel_txs) >= 2) or (len(auto_loan_txs) > 0)
    vehicle_signals = []
    if len(fastag_txs) > 0:
        vehicle_signals.append(f"{len(fastag_txs)} FASTag toll debits found")
    if len(fuel_txs) > 0:
        vehicle_signals.append(f"{len(fuel_txs)} Fuel pump transactions detected (Rs {fuel_txs['debit'].sum():,.0f})")
    if len(auto_loan_txs) > 0:
        vehicle_signals.append("Active Auto Loan EMI debit detected")

    # 6. Loan / Liability Detection
    loan_txs = debits[debits['narration'].str.contains(r'LOAN|EMI|MORTGAGE|BAJAJ FIN|HDB FS|HOME LOAN|AUTO LOAN|CAR LOAN|PERSONAL LOAN|CHOLA', case=False, regex=True)]
    months_count = 1
    if 'date' in df.columns:
        try:
            dates = pd.to_datetime(df['date'], errors='coerce')
            months_count = max(1, dates.dt.to_period('M').nunique())
        except Exception:
            months_count = 1

    total_loan_debits = float(loan_txs['debit'].sum()) if not loan_txs.empty else 0.0
    detected_monthly_emi = round(total_loan_debits / months_count, 2)
    # Estimate outstanding debt liability as 36 months of detected recurring EMI obligations
    estimated_outstanding_debt = round(detected_monthly_emi * 36.0, 0)

    # 7. Liquid Cushion from Ending Statement Balance
    ending_balance = 0.0
    if 'balance' in df.columns and not df['balance'].dropna().empty:
        try:
            ending_balance = max(0.0, float(df['balance'].dropna().iloc[-1]))
        except Exception:
            ending_balance = 0.0

    # 8. Corporate GMC Signals (e.g., TPA mentions or employer health deductions)
    corp_gmc_txs = debits[debits['narration'].str.contains(r'MEDIASSIST|VIDAL|PARAMOUNT TPA|MDINDIA|HERITAGE TPA|GMC|GROUP HEALTH|CORP HEALTH', case=False, regex=True)]
    corporate_gmc_detected = len(corp_gmc_txs) > 0
    corporate_gmc_signals = []
    if corporate_gmc_detected:
        corporate_gmc_signals.append(f"Detected corporate medical administrator debits: {len(corp_gmc_txs)} transactions")

    return {
        "detected_policies": detected_policies,
        "medical_spends": medical_spends,
        "medical_transactions_count": len(medical_txs),
        "vehicle_detected": vehicle_detected,
        "vehicle_signals": vehicle_signals,
        "detected_monthly_emi": detected_monthly_emi,
        "estimated_outstanding_debt": estimated_outstanding_debt,
        "ending_balance": ending_balance,
        "corporate_gmc_detected": corporate_gmc_detected,
        "corporate_gmc_signals": corporate_gmc_signals
    }

def calculate_endowment_arbitrage(endowment_premium: float, duration_years: int = 20) -> Dict[str, Any]:
    """
    Compares keeping a traditional endowment policy vs buying pure term life + investing
    the remaining difference in a Nifty 50 Index Mutual Fund.
    """
    if endowment_premium <= 0:
        return {}
    
    # 1. Pure term cost for equivalent or superior Rs 1.5 Cr cover
    term_annual_cost = min(12000.0, endowment_premium * 0.45)
    monthly_investable_surplus = max(0.0, (endowment_premium - term_annual_cost) / 12.0)
    
    # 2. Traditional endowment estimated maturity at ~4.5% returns
    total_paid = endowment_premium * duration_years
    endowment_maturity = total_paid * 1.55 # Typical LIC 4-5% return profile
    
    # 3. SIP in Nifty 50 Index Fund at 12% CAGR
    monthly_rate = 0.12 / 12.0
    months = duration_years * 12
    sip_future_value = monthly_investable_surplus * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    
    wealth_advantage = max(0.0, sip_future_value - endowment_maturity)
    
    return {
        "endowment_annual_premium": endowment_premium,
        "pure_term_annual_cost": term_annual_cost,
        "annual_savings_for_investment": endowment_premium - term_annual_cost,
        "duration_years": duration_years,
        "endowment_maturity_est": round(endowment_maturity, 0),
        "index_fund_future_value": round(sip_future_value, 0),
        "wealth_advantage": round(wealth_advantage, 0),
        "term_coverage_provided": 15000000.0, # Rs 1.5 Cr
        "endowment_coverage_provided": round(endowment_premium * 15.0, 0),
        "insight": f"By switching Rs {endowment_premium:,.0f}/year from LIC to Pure Term (Rs {term_annual_cost:,.0f}/yr for Rs 1.5 Cr cover) and investing the remaining Rs {endowment_premium - term_annual_cost:,.0f}/year in a Nifty 50 Index Fund at 12% CAGR, you create Rs {wealth_advantage:,.0f} extra wealth while giving your family 10X more death protection."
    }

def compute_insurance_portfolio(
    df: Optional[pd.DataFrame],
    annual_income: Optional[float] = None,
    outstanding_loans: Optional[float] = None,
    liquid_assets: Optional[float] = None,
    dependents_count: Optional[int] = None,
    income_multiplier: float = 12.0,
    user_vault_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Consolidates statement-detected and user-declared policies, executes statement-grounded HLV
    gap analysis, checks corporate health vulnerability, motor coverage, and calculates Insurance Shield Score.
    """
    # 1. Cashflow & Statement Analysis
    cf_context = get_cashflow_context(df)
    stmt_data = analyze_statement_insurance(df)
    
    detected_policies = stmt_data["detected_policies"]
    medical_spends = stmt_data["medical_spends"]
    vehicle_detected = stmt_data["vehicle_detected"]
    vehicle_signals = stmt_data["vehicle_signals"]

    # 2. Determine Grounded HLV Parameters
    # Derive from statement ledger if not explicitly overridden by user
    is_income_from_statement = False
    if annual_income is not None:
        effective_income = float(annual_income)
    elif cf_context.get("has_data") and cf_context.get("avg_monthly_income", 0) > 0:
        effective_income = round(cf_context["avg_monthly_income"] * 12.0, 2)
        is_income_from_statement = True
    else:
        effective_income = 1260000.0

    is_loans_from_statement = False
    if outstanding_loans is not None:
        effective_loans = float(outstanding_loans)
    elif stmt_data["estimated_outstanding_debt"] > 0:
        effective_loans = stmt_data["estimated_outstanding_debt"]
        is_loans_from_statement = True
    else:
        effective_loans = 0.0

    is_assets_from_statement = False
    if liquid_assets is not None:
        effective_assets = float(liquid_assets)
    elif stmt_data["ending_balance"] > 0:
        effective_assets = stmt_data["ending_balance"]
        is_assets_from_statement = True
    else:
        effective_assets = round(cf_context.get("emergency_fund_3mo", 300000.0), 0)

    effective_dependents = int(dependents_count) if dependents_count is not None else 2
    effective_multiplier = float(income_multiplier) if income_multiplier is not None else 12.0

    # 3. Declared Policies
    declared_policies = load_declared_policies(user_vault_dir)

    # 4. Policy Reconciliation & Unified List
    unified_policies: List[Dict[str, Any]] = []
    
    total_life_cover = 0.0
    total_health_cover = 0.0
    total_motor_cover = 0.0
    total_pa_cover = 0.0
    total_annual_premium = 0.0

    has_employer_health_only = False
    has_retail_health = False
    has_motor_policy = False
    traditional_endowment_premium = 0.0

    # Process declared policies first
    for pol in declared_policies:
        raw_cat = pol.get("category", "OTHER").upper()
        si = float(pol.get("sum_insured", 0.0))
        prem = float(pol.get("annual_premium", 0.0))
        total_annual_premium += prem
        
        is_emp = pol.get("is_employer_provided", False) or pol.get("source") == "EMPLOYER_GMC"
        badge = "EMPLOYER GMC" if is_emp else ("AI ADOPTED" if pol.get("source") == "AI_RECOMMENDED" else "USER DECLARED")

        # Normalize category
        cat = "OTHER"
        if "LIFE" in raw_cat:
            cat = "LIFE"
        elif "HEALTH" in raw_cat:
            cat = "HEALTH"
        elif "MOTOR" in raw_cat:
            cat = "MOTOR"
        elif "ACCIDENT" in raw_cat:
            cat = "PERSONAL_ACCIDENT"
        else:
            cat = raw_cat

        unified_item = {
            **pol,
            "category": cat,
            "badge": badge,
            "is_verified_by_statement": False
        }

        if cat == "LIFE":
            total_life_cover += si
        elif cat == "HEALTH":
            total_health_cover += si
            if is_emp:
                has_employer_health_only = True
            else:
                has_retail_health = True
        elif cat == "MOTOR":
            total_motor_cover += si
            has_motor_policy = True
        elif cat == "PERSONAL_ACCIDENT":
            total_pa_cover += si

        unified_policies.append(unified_item)

    # Process statement-detected policies
    for pol in detected_policies:
        cat = pol.get("category", "OTHER").upper()
        si = float(pol.get("sum_insured", 0.0))
        prem = float(pol.get("annual_premium", 0.0))
        
        # Check if already declared with similar insurer
        already_linked = False
        for u in unified_policies:
            if u.get("category") == cat and (u.get("insurer_name", "").lower() in pol.get("insurer_name", "").lower()):
                u["is_verified_by_statement"] = True
                u["badge"] = "STATEMENT VERIFIED"
                already_linked = True
                break

        if not already_linked:
            total_annual_premium += prem
            unified_policies.append({
                **pol,
                "badge": "STATEMENT DETECTED",
                "is_verified_by_statement": True
            })

            if cat == "LIFE":
                total_life_cover += si
                if pol.get("is_traditional_endowment"):
                    traditional_endowment_premium += prem
            elif cat == "HEALTH":
                total_health_cover += si
                has_retail_health = True
            elif cat == "MOTOR":
                total_motor_cover += si
                has_motor_policy = True

    if has_retail_health:
        has_employer_health_only = False

    # Check if corporate GMC detected via TPA debits but not yet formally declared
    if stmt_data.get("corporate_gmc_detected") and not has_retail_health and total_health_cover == 0:
        has_employer_health_only = True
        total_health_cover = 500000.0 # Standard ₹5L employer GMC default
        unified_policies.append({
            "id": "det_corp_gmc_estimated",
            "category": "HEALTH",
            "policy_type": "EMPLOYER_GMC",
            "insurer_name": "Employer Group Medical Cover (GMC)",
            "plan_name": "Corporate Group Health Shield (Estimated)",
            "annual_premium": 0.0,
            "sum_insured": 500000.0,
            "source": "STATEMENT_DETECTED",
            "is_employer_provided": True,
            "badge": "EMPLOYER GMC"
        })

    # 5. Grounded Needs-Based Human Life Value (HLV)
    # Required Cover = (Annual Income * Multiplier) + Outstanding Loans - Liquid Assets
    required_life_cover = max(0.0, (effective_income * effective_multiplier) + effective_loans - effective_assets)
    life_protection_gap = max(0.0, required_life_cover - total_life_cover)

    # Status classification
    if effective_dependents == 0:
        life_status = "ADEQUATE (NO DEPENDENTS)"
        life_insight = "Zero financial dependents. Life insurance is unnecessary until you take on family dependants or large liabilities."
    elif life_protection_gap <= 0:
        life_status = "ADEQUATELY PROTECTED"
        life_insight = f"Your active life cover of ₹{total_life_cover/10000000:.2f} Cr fully safeguards your family against liabilities and future income needs."
    elif total_life_cover == 0:
        life_status = "CRITICAL DEFICIT (ZERO COVER)"
        life_insight = f"Zero life insurance found. With {effective_dependents} dependents and ₹{effective_loans/100000:.1f}L in debt, your family has a critical ₹{life_protection_gap/10000000:.2f} Cr protection gap."
    else:
        life_status = "UNDER-INSURED GAP"
        life_insight = f"You hold ~₹{total_life_cover/100000:.1f} Lakhs life cover, but liabilities and income replacement require ₹{required_life_cover/10000000:.2f} Cr. Protection gap is ₹{life_protection_gap/10000000:.2f} Cr."

    # 6. Health Vulnerability
    critical_alerts: List[str] = []
    
    if total_health_cover == 0.0:
        health_status = "HIGH RISK - ZERO HEALTH COVER"
        health_insight = f"Zero health policies detected. You spent ₹{medical_spends:,.2f} out-of-pocket on medical expenses. A major hospitalization could liquidate your emergency savings."
        critical_alerts.append("Zero health insurance active. One hospitalization can wipe out personal savings.")
    elif has_employer_health_only:
        health_status = "CORPORATE DEPENDENCY RISK"
        health_insight = f"You are covered only under an employer group cover (~₹{total_health_cover/100000:.1f}L). If you switch jobs, face layoffs, or retire, you will have zero personal healthcare protection."
        critical_alerts.append("Corporate Health Dependency: Zero personal retail health cover detected. Bridge this gap with an ultra-low-cost Super Top-Up.")
    else:
        health_status = "ACTIVE RETAIL COVER"
        health_insight = f"Active retail health protection of ₹{total_health_cover/100000:.1f}L protects against unexpected hospitalization."

    if traditional_endowment_premium > 0:
        critical_alerts.append(f"Traditional LIC Endowment policy detected (₹{traditional_endowment_premium:,.0f}/yr). High cost, low death benefit (~4.5% returns).")

    if vehicle_detected and not has_motor_policy:
        motor_status = "MISSING MOTOR POLICY VERIFICATION"
        critical_alerts.append("Active vehicle usage detected (FASTag / Fuel / Auto Loan), but no active motor insurance policy is logged.")
    else:
        motor_status = "COVERED" if has_motor_policy else "NO VEHICLE"

    # 7. Composite Insurance Shield Score (0-100)
    score = 0
    # Life (Max 40)
    if effective_dependents == 0:
        score += 40
    else:
        life_ratio = min(1.0, total_life_cover / required_life_cover) if required_life_cover > 0 else 1.0
        score += int(life_ratio * 40)

    # Health (Max 40)
    if total_health_cover >= 1000000.0 and not has_employer_health_only:
        score += 40
    elif total_health_cover >= 500000.0 and not has_employer_health_only:
        score += 30
    elif has_employer_health_only:
        score += 18 # Corporate cover gets reasonable baseline
    else:
        score += 0

    # Motor / Asset (Max 10)
    if not vehicle_detected or has_motor_policy:
        score += 10
    else:
        score += 0

    # Medical spend burden (Max 10)
    if medical_spends < 10000.0:
        score += 10
    elif medical_spends < 30000.0:
        score += 5
    else:
        score += 0

    # Traditional Arbitrage
    arbitrage_data = calculate_endowment_arbitrage(traditional_endowment_premium)

    # Estimated tax savings under 80C and 80D
    tax_80c_saved = min(150000.0, total_annual_premium * 0.7) * 0.30
    tax_80d_saved = min(25000.0, 15000.0) * 0.30

    return {
        "shield_score": max(10, min(100, score)),
        "shield_status": "STRONG SHIELD" if score >= 80 else ("MODERATE GAP" if score >= 50 else "VULNERABLE"),
        "metrics": {
            "annual_income": effective_income,
            "outstanding_loans": effective_loans,
            "liquid_assets": effective_assets,
            "dependents_count": effective_dependents,
            "income_multiplier": effective_multiplier,
            "required_life_cover": required_life_cover,
            "total_life_cover": total_life_cover,
            "life_protection_gap": life_protection_gap,
            "total_health_cover": total_health_cover,
            "total_motor_cover": total_motor_cover,
            "total_annual_premium": total_annual_premium,
            "out_of_pocket_medical_spent": medical_spends,
            "estimated_tax_savings": round(tax_80c_saved + tax_80d_saved, 0),
            "is_income_from_statement": is_income_from_statement,
            "is_loans_from_statement": is_loans_from_statement,
            "is_assets_from_statement": is_assets_from_statement
        },
        "life_insurance": {
            "status": life_status,
            "required_cover": required_life_cover,
            "detected_cover": total_life_cover,
            "coverage_gap": life_protection_gap,
            "insight": life_insight
        },
        "health_insurance": {
            "status": health_status,
            "total_cover": total_health_cover,
            "has_employer_health_only": has_employer_health_only,
            "has_retail_health": has_retail_health,
            "out_of_pocket_medical_spent": medical_spends,
            "insight": health_insight
        },
        "motor_insurance": {
            "status": motor_status,
            "vehicle_detected": vehicle_detected,
            "vehicle_signals": vehicle_signals,
            "has_policy": has_motor_policy
        },
        "critical_alerts": critical_alerts,
        "unified_policies": unified_policies,
        "arbitrage": arbitrage_data,
        "cashflow_context": {
            "monthly_inflow": cf_context.get("avg_monthly_income", 0.0),
            "monthly_burn": cf_context.get("avg_monthly_expense", 0.0),
            "monthly_surplus": cf_context.get("avg_monthly_surplus", 0.0),
            "mandatory_monthly_burn": cf_context.get("mandatory_monthly_burn", 0.0),
            "discretionary_categories": cf_context.get("discretionary_categories", [])
        }
    }
