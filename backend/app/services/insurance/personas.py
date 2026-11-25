"""
Synthetic Financial Personas for Testing finMan's Insurance Planner & Manager.
Provides deterministic data profiles, transaction ledgers, and declared policies
to test detection, gap analysis, and AI suggestions across different life stages.
"""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta

PERSONAS: Dict[str, Dict[str, Any]] = {
    "aarav_intern": {
        "id": "aarav_intern",
        "name": "Aarav Sharma",
        "tagline": "22yo Fresh Graduate & Tech Intern",
        "age": 22,
        "marital_status": "Single",
        "dependents": 0,
        "monthly_inflow": 45000,
        "annual_income": 540000,
        "monthly_burn": 32000,
        "outstanding_loans": 0,
        "liquid_assets": 65000,
        "declared_policies": [],
        "expected_findings": {
            "life_gap_status": "ADEQUATE",
            "health_gap_status": "HIGH RISK (ZERO HEALTH COVER)",
            "motor_status": "NO VEHICLE DETECTED",
            "key_insight": "Aarav has no financial dependents, so life insurance is unnecessary. However, zero health insurance combined with out-of-pocket pharmacy debits leaves him vulnerable to sudden hospitalization bills."
        }
    },
    "priya_tech_pro": {
        "id": "priya_tech_pro",
        "name": "Priya Nair",
        "tagline": "27yo Single IT Professional with Car Loan",
        "age": 27,
        "marital_status": "Single",
        "dependents": 0,
        "monthly_inflow": 135000,
        "annual_income": 1620000,
        "monthly_burn": 72000,
        "outstanding_loans": 520000,
        "liquid_assets": 420000,
        "declared_policies": [
            {
                "id": "decl_priya_gmc",
                "category": "HEALTH",
                "source": "EMPLOYER_GMC",
                "insurer_name": "HDFC ERGO General Insurance",
                "plan_name": "Corporate Employee Health Shield",
                "sum_insured": 500000,
                "annual_premium": 0,
                "is_employer_provided": True,
                "covered_members": ["Self"],
                "has_room_rent_capping": True,
                "room_rent_limit_percentage": 1.0,
                "renewal_date": "2027-03-31",
                "notes": "Employer sponsored group cover"
            }
        ],
        "expected_findings": {
            "life_gap_status": "MODERATE RISK",
            "health_gap_status": "CORPORATE DEPENDENCY RISK",
            "motor_status": "ACTIVE VEHICLE MISSING INSURANCE VERIFICATION",
            "key_insight": "Priya relies solely on employer corporate cover with 1% room rent capping. She owns a car (active auto EMI and FASTag) but has no motor policy debit in statement. She also has Rs 5.2L car debt without term cover."
        }
    },
    "vikram_young_family": {
        "id": "vikram_young_family",
        "name": "Vikram Malhotra",
        "tagline": "34yo Married Breadwinner with Home Loan & Child",
        "age": 34,
        "marital_status": "Married",
        "dependents": 2,
        "monthly_inflow": 210000,
        "annual_income": 2520000,
        "monthly_burn": 145000,
        "outstanding_loans": 4800000,
        "liquid_assets": 1250000,
        "declared_policies": [
            {
                "id": "decl_vikram_health",
                "category": "HEALTH",
                "source": "PERSONAL_RETAIL",
                "insurer_name": "Star Health Insurance",
                "plan_name": "Star Family Health Optima",
                "sum_insured": 500000,
                "annual_premium": 18200,
                "is_employer_provided": False,
                "covered_members": ["Self", "Spouse", "1 Child"],
                "has_room_rent_capping": True,
                "room_rent_limit_percentage": 1.0,
                "renewal_date": "2026-11-30",
                "notes": "Retail policy purchased via agent"
            }
        ],
        "expected_findings": {
            "life_gap_status": "CRITICAL PROTECTION GAP",
            "health_gap_status": "UNDER-INSURED FLOATER",
            "motor_status": "NO ACTIVE MOTOR ISSUE",
            "traditional_trap": True,
            "key_insight": "Vikram is paying Rs 28,500/year to an LIC traditional endowment policy that offers only ~Rs 4.5 Lakhs life cover. With a Rs 48L home loan and 2 dependents, his family faces a severe Rs 3+ Crore life protection deficit."
        }
    },
    "sunita_senior_parents": {
        "id": "sunita_senior_parents",
        "name": "Sunita Sengupta",
        "tagline": "43yo Senior Director with Aging Parents",
        "age": 43,
        "marital_status": "Married",
        "dependents": 3,
        "monthly_inflow": 380000,
        "annual_income": 4560000,
        "monthly_burn": 190000,
        "outstanding_loans": 0,
        "liquid_assets": 4500000,
        "declared_policies": [
            {
                "id": "decl_sunita_gmc",
                "category": "HEALTH",
                "source": "EMPLOYER_GMC",
                "insurer_name": "Care Health Insurance",
                "plan_name": "Corporate Family GMC",
                "sum_insured": 1000000,
                "annual_premium": 0,
                "is_employer_provided": True,
                "covered_members": ["Self", "Spouse", "Father (71)", "Mother (68)"],
                "has_room_rent_capping": False,
                "has_copay": True,
                "copay_percentage": 20,
                "renewal_date": "2027-04-30",
                "notes": "Employer covers parents with 20% co-pay"
            }
        ],
        "expected_findings": {
            "life_gap_status": "ADEQUATELY PROTECTED (Rs 2 Cr Pure Term Active)",
            "health_gap_status": "CATASTROPHIC OUT-OF-POCKET PARENTAL SPEND",
            "motor_status": "ADEQUATE",
            "key_insight": "Sunita has pure term life cover. However, recurring hospital debits of Rs 18,400/month for elderly parents highlight an acute vulnerability. The corporate 20% co-pay clause bleeds out-of-pocket cash during hospitalizations."
        }
    },
    "anand_entrepreneur": {
        "id": "anand_entrepreneur",
        "name": "Anand Vardhan",
        "tagline": "39yo MSME Business Owner with Personal Guarantees",
        "age": 39,
        "marital_status": "Married",
        "dependents": 3,
        "monthly_inflow": 320000,
        "annual_income": 3840000,
        "monthly_burn": 180000,
        "outstanding_loans": 3500000,
        "liquid_assets": 1800000,
        "declared_policies": [
            {
                "id": "decl_anand_health",
                "category": "HEALTH",
                "source": "PERSONAL_RETAIL",
                "insurer_name": "Care Health Insurance",
                "plan_name": "Care Supreme Individual",
                "sum_insured": 1000000,
                "annual_premium": 14500,
                "is_employer_provided": False,
                "covered_members": ["Self"],
                "has_room_rent_capping": False,
                "renewal_date": "2026-12-15",
                "notes": "Personal policy for self only"
            }
        ],
        "expected_findings": {
            "life_gap_status": "HIGH BUSINESS & PERSONAL LIABILITY RISK",
            "health_gap_status": "FAMILY UNPROTECTED",
            "motor_status": "MOTOR INSURANCE ACTIVE",
            "key_insight": "As a business owner with Rs 35L in personal business debt, Anand has zero corporate safety net. In an emergency, creditors can claim assets unless a term policy is secured under the Married Women's Property (MWP) Act."
        }
    }
}

def generate_persona_transactions(persona_id: str) -> pd.DataFrame:
    """Generates a realistic 1-year (12 continuous months) transaction DataFrame for the specified persona."""
    months = [
        (2025, 11), (2025, 12),
        (2026, 1), (2026, 2), (2026, 3), (2026, 4),
        (2026, 5), (2026, 6), (2026, 7), (2026, 8),
        (2026, 9), (2026, 10)
    ]
    tx_list: List[Dict[str, Any]] = []
    ref_counter = 1000

    if persona_id == "vikram_young_family":
        bal = 1250000.0
        for yr, mo in months:
            def add(day, narration, debit, credit, cat, subcat, merchant, mode="UPI"):
                nonlocal bal, ref_counter
                ref_counter += 1
                d_str = f"{yr:04d}-{mo:02d}-{min(day, 28):02d}"
                if credit > 0:
                    bal += credit
                if debit > 0:
                    bal -= debit
                tx_list.append({
                    "date": d_str,
                    "narration": narration,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": round(bal, 2),
                    "mode": mode,
                    "source": "vikram_statement.csv",
                    "merchant": merchant,
                    "category": cat,
                    "sub_category": subcat,
                    "ref_no": f"TXN{ref_counter}",
                    "_statement_id": "stmt_vikram_01",
                    "_statement_filename": "Vikram Malhotra Bank Statement.csv"
                })

            add(1, "ACH C- TATA MOTORS LTD SALARY", 0.0, 210000.0, "Salary & Direct Inflow", "Salary & Direct Inflow", "Tata Motors Ltd", "ACH")
            add(3, "NEFT/GREENWOOD APARTMENTS MAINTENANCE", 6500.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Greenwood Apartments", "NEFT")
            add(5, "ACH D- HDFC HOME LOAN EMI-3920", 58000.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "HDFC Bank Home Loan", "ACH")
            add(8, "POS NATURES BASKET BANDRA", 3850.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Natures Basket", "POS")
            add(10, "SIP/NIPPON INDIA GROWTH FUND", 15000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "Nippon India Mutual Fund", "ACH")
            add(11, "AIRTEL BROADBAND FIBER BILL", 1199.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Airtel Broadband", "UPI")
            add(13, "UPI/ZOMATO RESTAURANT ORDER", 950.0, 0.0, "Discretionary", "Food Delivery & Dining", "Zomato", "UPI")
            add(14, "TATA POWER MUMBAI ELECTRICITY", 2650.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Tata Power", "UPI")
            add(15, "POS HPCL AUTO FUEL PUMP", 4200.0, 0.0, "Variable Essentials", "Fuel & Commute", "HPCL Auto Fuel", "CARD")
            add(16, "NETFLIX ENTERTAINMENT MUMBAI", 649.0, 0.0, "Fixed Expenses", "Subscriptions", "Netflix India", "CARD")
            add(17, "UPI/BLINKIT GROCERY DELIVERY", 780.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Blinkit", "UPI")
            add(18, "CULT FIT HEALTHCARE MEMBERSHIP", 1499.0, 0.0, "Fixed Expenses", "Subscriptions", "Cult.fit", "UPI")
            add(19, "UPI/APOLLO PHARMACY FAMILY", 1850.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Apollo Pharmacy", "UPI")
            add(21, "UPI/SWIGGY FOOD DELIVERY", 840.0, 0.0, "Discretionary", "Food Delivery & Dining", "Swiggy", "UPI")
            add(22, "UPI/ZEPTO INSTANT GROCERIES", 620.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Zepto", "UPI")
            add(23, "POS STARBUCKS COFFEE BANDRA", 740.0, 0.0, "Discretionary", "Food Delivery & Dining", "Starbucks", "CARD")
            add(24, "NETC FASTAG TOLL MUMBAI PUNE", 1000.0, 0.0, "Variable Essentials", "Fuel & Commute", "FASTag Toll", "UPI")
            add(25, "POS PUNJAB GRILL MUMBAI", 3450.0, 0.0, "Discretionary", "Food Delivery & Dining", "Punjab Grill", "CARD")
            add(26, "AMAZON PAY INDIA RETAIL", 2400.0, 0.0, "Discretionary", "Shopping & E-Commerce", "Amazon India", "CARD")
            add(27, "POS NATURES BASKET BANDRA", 4100.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Natures Basket", "POS")

            if mo in (1, 4, 7, 10):
                add(10, "ACH D- DELHI PUBLIC SCHOOL FEES", 16000.0, 0.0, "Variable Essentials", "Education & Academic", "Delhi Public School", "ACH")

            if mo == 8:
                add(9, "ACH D- LIC OF INDIA PREM-983284", 28500.0, 0.0, "Fixed Expenses", "Insurance Premiums", "Life Insurance Corporation of India (LIC)", "ACH")

    elif persona_id == "priya_tech_pro":
        bal = 420000.0
        for yr, mo in months:
            def add(day, narration, debit, credit, cat, subcat, merchant, mode="UPI"):
                nonlocal bal, ref_counter
                ref_counter += 1
                d_str = f"{yr:04d}-{mo:02d}-{min(day, 28):02d}"
                if credit > 0:
                    bal += credit
                if debit > 0:
                    bal -= debit
                tx_list.append({
                    "date": d_str,
                    "narration": narration,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": round(bal, 2),
                    "mode": mode,
                    "source": "priya_statement.csv",
                    "merchant": merchant,
                    "category": cat,
                    "sub_category": subcat,
                    "ref_no": f"TXN{ref_counter}",
                    "_statement_id": "stmt_priya_01",
                    "_statement_filename": "Priya Nair Bank Statement.csv"
                })

            inflow = 165000.0 if mo in (3, 8) else 135000.0
            add(1, "NEFT CR- ZETA TECH CONSULTING RETAINER", 0.0, inflow, "Salary & Direct Inflow", "Salary & Direct Inflow", "Zeta Tech Consulting", "NEFT")
            add(2, "UPI/RENT TRANSFER TO SUNIL PROPERTIES", 28000.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "Sunil Properties Rent", "UPI")
            add(7, "ACH D- HDFC AUTO LOAN EMI-9482", 14800.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "HDFC Bank Auto Loan", "ACH")
            add(9, "POS THIRD WAVE COFFEE INDIRANAGAR", 650.0, 0.0, "Discretionary", "Food Delivery & Dining", "Third Wave Coffee", "CARD")
            add(11, "POS BPCL FUEL STATION INDIRANAGAR", 4200.0, 0.0, "Variable Essentials", "Fuel & Commute", "BPCL Fuel Station", "CARD")
            add(13, "UPI/BLINKIT QUICK GROCERY", 850.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Blinkit", "UPI")
            add(14, "NETC FASTAG RECHARGE IHMCL", 2000.0, 0.0, "Variable Essentials", "Fuel & Commute", "FASTag Toll", "UPI")
            add(15, "SIP/PARAG PARIKH FLEXI CAP", 20000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "Parag Parikh Flexi Cap", "ACH")
            add(16, "ADOBE CREATIVE CLOUD SUBSCRIPTION", 4230.0, 0.0, "Fixed Expenses", "Cloud & Tech Tools", "Adobe Creative Cloud", "CARD")
            add(17, "FIGMA PROFESSIONAL SUBSCRIPTION", 1250.0, 0.0, "Fixed Expenses", "Cloud & Tech Tools", "Figma Inc", "CARD")
            add(18, "SPOTIFY PREMIUM INDIA", 119.0, 0.0, "Fixed Expenses", "Subscriptions", "Spotify India", "CARD")
            add(19, "POS KAYA SKIN CLINIC INDIRANAGAR", 4800.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Kaya Skin Clinic", "CARD")
            add(20, "APPLE SERVICES ICLOUD STORAGE", 219.0, 0.0, "Fixed Expenses", "Subscriptions", "Apple Services", "CARD")
            add(21, "UPI/SWIGGY GOURMET MEALS", 920.0, 0.0, "Discretionary", "Food Delivery & Dining", "Swiggy", "UPI")
            add(22, "UPI/ZEPTO DAILY FRESH", 580.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Zepto", "UPI")
            add(23, "POS BLUE TOKAI COFFEE ROASTERS", 540.0, 0.0, "Discretionary", "Food Delivery & Dining", "Blue Tokai Coffee", "CARD")
            add(24, "UPI/TATA 1MG HEALTHCARE", 1850.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Tata 1mg", "UPI")
            add(25, "POS ZARA RETAIL BANGALORE", 6200.0, 0.0, "Discretionary", "Shopping & E-Commerce", "Zara Retail", "CARD")
            add(26, "NYKAA BEAUTY E-COMMERCE", 3400.0, 0.0, "Discretionary", "Shopping & E-Commerce", "Nykaa", "CARD")

            if mo in (12, 5):
                vac_cost = 18500.0 if mo == 12 else 14200.0
                add(27, "AIRBNB GOA BEACHFRONT RESORT", vac_cost, 0.0, "Discretionary", "Travel & Vacation", "Airbnb", "CARD")

            if mo == 4:
                add(12, "ACH D- ICICI LOMBARD MOTOR INS-3921", 9400.0, 0.0, "Fixed Expenses", "Insurance Premiums", "ICICI Lombard General Insurance", "ACH")

    elif persona_id == "aarav_intern":
        bal = 65000.0
        for yr, mo in months:
            def add(day, narration, debit, credit, cat, subcat, merchant, mode="UPI"):
                nonlocal bal, ref_counter
                ref_counter += 1
                d_str = f"{yr:04d}-{mo:02d}-{min(day, 28):02d}"
                if credit > 0:
                    bal += credit
                if debit > 0:
                    bal -= debit
                tx_list.append({
                    "date": d_str,
                    "narration": narration,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": round(bal, 2),
                    "mode": mode,
                    "source": "aarav_statement.csv",
                    "merchant": merchant,
                    "category": cat,
                    "sub_category": subcat,
                    "ref_no": f"TXN{ref_counter}",
                    "_statement_id": "stmt_aarav_01",
                    "_statement_filename": "Aarav Sharma Bank Statement.csv"
                })

            inflow = 60000.0 if (yr == 2026 and mo >= 6) else 45000.0
            label = "ACH C- INFOSYS LTD FTE SALARY" if (yr == 2026 and mo >= 6) else "ACH C- INFOSYS LTD STIPEND"
            add(1, label, 0.0, inflow, "Salary & Direct Inflow", "Salary & Direct Inflow", "Infosys Ltd", "ACH")
            add(3, "UPI/FLATSHARE RENT TO ROHIT", 14000.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "Flatshare Rent", "UPI")
            add(5, "ACT FIBERNET BROADBAND BILL", 600.0, 0.0, "Fixed Expenses", "Utilities & Bills", "ACT Fibernet", "UPI")
            add(8, "UPI/ANNAPURNA MESS KORAMANGALA", 2600.0, 0.0, "Discretionary", "Food Delivery & Dining", "Annapurna Mess", "UPI")
            
            if yr == 2026:
                add(10, "SIP/UTI NIFTY 50 INDEX FUND", 5000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "UTI Mutual Fund", "ACH")
                
            add(12, "NAMMA METRO SMART CARD RECHARGE", 600.0, 0.0, "Variable Essentials", "Public Transit & Metro", "Namma Metro", "UPI")
            add(14, "UPI/SWIGGY MEAL DELIVERY", 380.0, 0.0, "Discretionary", "Food Delivery & Dining", "Swiggy", "UPI")
            add(15, "GITHUB COPILOT SUBSCRIPTION", 850.0, 0.0, "Fixed Expenses", "Cloud & Tech Tools", "GitHub Inc", "CARD")
            add(16, "SPOTIFY STUDENT PREMIUM", 59.0, 0.0, "Fixed Expenses", "Subscriptions", "Spotify India", "UPI")
            add(17, "UPI/CHAI POINT KORAMANGALA", 120.0, 0.0, "Daily Micro-Spends", "Local Vendor / Street Pay", "Chai Point", "UPI")
            add(18, "RAPIDO BIKE TAXI COMMUTE", 95.0, 0.0, "Variable Essentials", "Ride Hailing & Auto", "Rapido", "UPI")
            add(19, "UPI/BLINKIT GROCERY SNACKS", 450.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Blinkit", "UPI")
            add(20, "UPI/FITNESS ONE GYM MEMBERSHIP", 1500.0, 0.0, "Fixed Expenses", "Subscriptions", "Fitness One Gym", "UPI")
            add(22, "UBER AUTO RIDE BANGALORE", 160.0, 0.0, "Variable Essentials", "Ride Hailing & Auto", "Uber India", "UPI")
            add(24, "MCDONALDS FORUM MALL", 480.0, 0.0, "Discretionary", "Food Delivery & Dining", "McDonalds", "UPI")
            add(26, "BOOKMYSHOW MOVIE TICKETS", 550.0, 0.0, "Discretionary", "Entertainment & Outings", "BookMyShow", "UPI")

            if mo in (12, 3, 7):
                add(25, "STEAM GAMES DIGITAL PURCHASE", 1450.0, 0.0, "Discretionary", "Entertainment & Outings", "Steam Games", "CARD")

            if mo in (1, 5, 9):
                add(21, "UPI/APOLLO PHARMACY BANGALORE", 650.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Apollo Pharmacy", "UPI")

    elif persona_id == "sunita_senior_parents":
        bal = 4500000.0
        for yr, mo in months:
            def add(day, narration, debit, credit, cat, subcat, merchant, mode="UPI"):
                nonlocal bal, ref_counter
                ref_counter += 1
                d_str = f"{yr:04d}-{mo:02d}-{min(day, 28):02d}"
                if credit > 0:
                    bal += credit
                if debit > 0:
                    bal -= debit
                tx_list.append({
                    "date": d_str,
                    "narration": narration,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": round(bal, 2),
                    "mode": mode,
                    "source": "sunita_statement.csv",
                    "merchant": merchant,
                    "category": cat,
                    "sub_category": subcat,
                    "ref_no": f"TXN{ref_counter}",
                    "_statement_id": "stmt_sunita_01",
                    "_statement_filename": "Sunita Sengupta Bank Statement.csv"
                })

            add(1, "ACH C- GOOGLE INDIA PVT LTD SALARY", 0.0, 380000.0, "Salary & Direct Inflow", "Salary & Direct Inflow", "Google India Pvt Ltd", "ACH")
            add(3, "UPI/DRIVER RAMESH SALARY", 18000.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Driver Ramesh", "UPI")
            add(3, "UPI/COOK REKHA MONTHLY SALARY", 12000.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Cook Rekha", "UPI")
            add(4, "UPI/MAID SUNITA HOUSEKEEPING", 8000.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Maid Sunita", "UPI")
            add(5, "NEFT/DLF PHASE 5 RESIDENTS ASSOCIATION", 12500.0, 0.0, "Fixed Expenses", "Utilities & Bills", "DLF Phase 5 Condominium", "NEFT")
            add(8, "SIP/PARAG PARIKH FLEXI CAP", 40000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "Parag Parikh Flexi Cap", "ACH")
            add(8, "SIP/HDFC TOP 100 EQUITY FUND", 35000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "HDFC Mutual Fund", "ACH")
            add(10, "POS NATURES BASKET GURGAON", 5800.0, 0.0, "Variable Essentials", "Groceries & Supplies", "Natures Basket", "CARD")
            add(12, "POS MAX HEALTHCARE GURGAON", 4500.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Max Healthcare", "CARD")
            
            elec = 8500.0 if mo in (5, 6, 7, 8) else 4800.0
            add(14, "DHBVN POWER GURGAON ELECTRICITY", elec, 0.0, "Fixed Expenses", "Utilities & Bills", "DHBVN Power", "UPI")
            add(15, "TATA PLAY FIBER BROADBAND", 1999.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Tata Play Fiber", "UPI")
            add(17, "POS MEDPLUS PHARMACY GURGAON", 7800.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "MedPlus Pharmacy", "CARD")
            add(19, "POS DR LAL PATHLABS GURGAON", 3200.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Dr Lal PathLabs", "CARD")
            add(21, "BIGBASKET SUPERSAVER GROCERY", 4500.0, 0.0, "Variable Essentials", "Groceries & Supplies", "BigBasket", "UPI")
            add(23, "UPI/PORTEA MEDICAL PHYSIOTHERAPY", 4500.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Portea Medical", "UPI")
            add(24, "POS FABINDIA RETAIL GURGAON", 6800.0, 0.0, "Discretionary", "Shopping & E-Commerce", "Fabindia", "CARD")
            add(25, "THE OBEROI GURGAON DINING", 5800.0, 0.0, "Discretionary", "Food Delivery & Dining", "The Oberoi", "CARD")
            add(26, "POS GOOD EARTH HOME & APPAREL", 8500.0, 0.0, "Discretionary", "Shopping & E-Commerce", "Good Earth", "CARD")

            if mo == 3:
                add(8, "ACH D- HDFC LIFE CLICK2PROTECT TERM", 32000.0, 0.0, "Fixed Expenses", "Insurance Premiums", "HDFC Life Insurance", "ACH")

            if mo == 6:
                add(15, "ACH D- CARE HEALTH INSURANCE", 44500.0, 0.0, "Fixed Expenses", "Insurance Premiums", "Care Health Insurance", "ACH")

    elif persona_id == "anand_entrepreneur":
        bal = 1800000.0
        for yr, mo in months:
            def add(day, narration, debit, credit, cat, subcat, merchant, mode="UPI"):
                nonlocal bal, ref_counter
                ref_counter += 1
                d_str = f"{yr:04d}-{mo:02d}-{min(day, 28):02d}"
                if credit > 0:
                    bal += credit
                if debit > 0:
                    bal -= debit
                tx_list.append({
                    "date": d_str,
                    "narration": narration,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": round(bal, 2),
                    "mode": mode,
                    "source": "anand_statement.csv",
                    "merchant": merchant,
                    "category": cat,
                    "sub_category": subcat,
                    "ref_no": f"TXN{ref_counter}",
                    "_statement_id": "stmt_anand_01",
                    "_statement_filename": "Anand Vardhan Bank Statement.csv"
                })

            inflow = 380000.0 if mo in (3, 6, 9, 12) else 300000.0
            add(1, "RTGS CR- VARDHAN PRECISION TOOLS PVT LTD", 0.0, inflow, "Salary & Direct Inflow", "Salary & Direct Inflow", "Vardhan Precision Tools", "RTGS")
            add(4, "ACH D- BAJAJ FINSERV BUSINESS LOAN", 48000.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "Bajaj Finserv Business Loan", "ACH")
            add(7, "NEFT/AMANORA TOWNSHIP PUNE MAINTENANCE", 8500.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Amanora Township Maintenance", "NEFT")
            add(10, "ACH D- TATA CAPITAL VEHICLE FINANCE", 24500.0, 0.0, "Fixed Expenses", "Loan EMIs & Rent", "Tata Capital Vehicle Finance", "ACH")
            add(12, "SIP/SBI SMALL CAP FUND", 15000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "SBI Mutual Fund", "ACH")
            add(12, "SIP/MIRAE ASSET LARGE CAP", 15000.0, 0.0, "Investments & Deposits", "Mutual Funds & SIPs", "Mirae Asset Mutual Fund", "ACH")
            add(14, "POS BPCL DIESEL COMMERCIAL PUMP", 5400.0, 0.0, "Variable Essentials", "Fuel & Commute", "BPCL Fuel Station", "CARD")
            add(15, "DMART SUPERMARKET PUNE", 6800.0, 0.0, "Variable Essentials", "Groceries & Supplies", "DMart Supermarket", "CARD")
            add(16, "AIRTEL BUSINESS BROADBAND LEASE", 3500.0, 0.0, "Fixed Expenses", "Cloud & Tech Tools", "Airtel Business", "UPI")
            add(18, "NETC FASTAG MUMBAI PUNE EXPRESSWAY", 2200.0, 0.0, "Variable Essentials", "Fuel & Commute", "FASTag Toll", "UPI")
            add(20, "JW MARRIOTT PUNE BUSINESS DINING", 5200.0, 0.0, "Discretionary", "Food Delivery & Dining", "JW Marriott Pune", "CARD")
            add(22, "INDIGO AIRLINES FLIGHT TICKETS", 6800.0, 0.0, "Discretionary", "Travel & Vacation", "IndiGo Airlines", "CARD")
            add(24, "BIGBASKET MONTHLY GROCERIES", 4800.0, 0.0, "Variable Essentials", "Groceries & Supplies", "BigBasket", "UPI")
            add(25, "MALAKA SPICE RESTAURANT PUNE", 3200.0, 0.0, "Discretionary", "Food Delivery & Dining", "Malaka Spice", "CARD")
            add(26, "UPI/APOLLO PHARMACY FAMILY", 2100.0, 0.0, "Variable Essentials", "Healthcare & Eyewear", "Apollo Pharmacy", "UPI")

            if mo in (12, 3, 6, 9):
                add(14, "INCOME TAX ADVANCE TAX E-PAY", 65000.0, 0.0, "Fixed Expenses", "Utilities & Bills", "Income Tax Department", "NETBANKING")

            if mo == 2:
                add(11, "ACH D- GO DIGIT GENERAL INS-9482", 18200.0, 0.0, "Fixed Expenses", "Insurance Premiums", "Go Digit General Insurance", "ACH")

            if mo == 11:
                add(18, "ACH D- STAR HEALTH OPTIMA RETAIL-8392", 36000.0, 0.0, "Fixed Expenses", "Insurance Premiums", "Star Health Insurance", "ACH")

    df = pd.DataFrame(tx_list)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    return df

def get_persona_details(persona_id: str) -> Dict[str, Any]:
    """Returns persona definition, expected findings, and declared policies."""
    return PERSONAS.get(persona_id, PERSONAS["aarav_intern"])

def list_all_personas() -> List[Dict[str, Any]]:
    """Returns metadata for all available personas."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "tagline": p["tagline"],
            "age": p["age"],
            "marital_status": p["marital_status"],
            "dependents": p["dependents"],
            "annual_income": p["annual_income"],
            "monthly_inflow": p["monthly_inflow"],
            "outstanding_loans": p["outstanding_loans"],
            "liquid_assets": p["liquid_assets"],
            "declared_policies_count": len(p["declared_policies"]),
            "expected_findings": p["expected_findings"]
        }
        for p in PERSONAS.values()
    ]
