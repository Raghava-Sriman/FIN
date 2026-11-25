"""
Curated Indian Insurance Product Knowledge Base for finMan.
Contains verified IRDAI-registered insurance products across Pure Term Life,
Comprehensive Health, Super Top-Up, Personal Accident, and Motor.
Includes 3-year IRDAI average Claim Settlement Ratios (CSR), Amount Settlement Ratios (ASR),
Incurred Claim Ratios (ICR), network hospital reach, room rent rules, and underwriting terms.
"""

from typing import List, Dict, Any, Optional

INSURANCE_CATALOG: List[Dict[str, Any]] = [
    # ------------------ PURE TERM LIFE ------------------
    {
        "id": "term_max_life_step",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "Max Life Insurance",
        "product_name": "Smart Total Elite Protection (STEP)",
        "csr_3yr_avg": 99.51,
        "asr_percentage": 98.2,
        "solvency_ratio": 2.14,
        "claim_settlement_speed_days": 1.0,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 8200,
        "approx_annual_premium_age_35_1cr": 13800,
        "approx_annual_premium_age_45_1cr": 26400,
        "approx_annual_premium_age_30_2cr": 18400,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Included (Accelerated payout up to Rs 1 Cr)",
        "key_features": [
            "Special Exit Option at age 65 with 100% premium return (excluding GST)",
            "Accelerated payout upon diagnosis of any terminal illness (remaining life expectancy < 6 months)",
            "Comprehensive Critical Illness rider covering 64 specified conditions",
            "Highest sustained Claim Settlement Ratio (99.51%) and Amount Settlement Ratio (98.2%) in India"
        ],
        "pros": [
            "Top-ranked IRDAI claim settlement track record over 5 consecutive years",
            "Seamless 1-day claim resolution for eligible clean submissions",
            "Zero sales surrender trap (pure term risk protection)"
        ],
        "cons_or_cautions": [
            "Strict medical underwriting; requires income proof (ITR / Form 16)"
        ],
        "sub_limits": "None (Full 100% sum insured paid to nominee upon claim)",
        "suitability": "Gold standard choice for primary breadwinners seeking pure term protection with India's highest claim payment reliability.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs (Old Regime) & 10(10D) tax-free payout"
    },
    {
        "id": "term_hdfc_click2protect",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "HDFC Life Insurance",
        "product_name": "Click 2 Protect Super",
        "csr_3yr_avg": 99.39,
        "asr_percentage": 98.1,
        "solvency_ratio": 2.03,
        "claim_settlement_speed_days": 1.2,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 8900,
        "approx_annual_premium_age_35_1cr": 14600,
        "approx_annual_premium_age_45_1cr": 27800,
        "approx_annual_premium_age_30_2cr": 19600,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Included automatically",
        "key_features": [
            "Inflation-hedging increasing cover option (sum insured automatically climbs 5-10% annually)",
            "Waiver of future premiums on total permanent disability or critical illness diagnosis",
            "Flexible payout schedules: Lump sum, monthly income replacement, or 50:50 combination",
            "Special exit value at milestone retirement ages"
        ],
        "pros": [
            "High amount settlement ratio (98.1%) guarantees large sum payouts without haircut",
            "Ideal for escalating home loan and childcare responsibilities"
        ],
        "cons_or_cautions": [
            "Slightly higher premium than peers for identical entry ages"
        ],
        "sub_limits": "None",
        "suitability": "Top fiduciary recommendation for salaried professionals holding long-term debt liabilities or home loans.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs & 10(10D) tax-free death benefit"
    },
    {
        "id": "term_tata_aia_srs",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "Tata AIA Life Insurance",
        "product_name": "Sampoorna Raksha Supreme",
        "csr_3yr_avg": 99.01,
        "asr_percentage": 97.8,
        "solvency_ratio": 2.22,
        "claim_settlement_speed_days": 1.1,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 8400,
        "approx_annual_premium_age_35_1cr": 14100,
        "approx_annual_premium_age_45_1cr": 26900,
        "approx_annual_premium_age_30_2cr": 18800,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Included",
        "key_features": [
            "Life Stage Milestone booster: Increase cover by 50% on marriage and 25% per child birth without new medical checkup",
            "Tata brand fiduciary pedigree and disciplined governance",
            "Option for whole of life cover up to age 85 or age 100",
            "Accidental death double sum insured rider available"
        ],
        "pros": [
            "Extremely flexible life stage milestone upgrades without underwriting friction",
            "High solvency ratio (2.22) reflecting strong capital backing"
        ],
        "cons_or_cautions": [
            "Medical tele-underwriting required for covers above Rs 1.5 Cr"
        ],
        "sub_limits": "None",
        "suitability": "Best for young families and newly married professionals anticipating rising family dependency over the next decade.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs"
    },
    {
        "id": "term_icici_iprotect",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "ICICI Prudential Life",
        "product_name": "iProtect Smart",
        "csr_3yr_avg": 98.75,
        "asr_percentage": 97.4,
        "solvency_ratio": 2.11,
        "claim_settlement_speed_days": 1.3,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 8600,
        "approx_annual_premium_age_35_1cr": 14400,
        "approx_annual_premium_age_45_1cr": 27500,
        "approx_annual_premium_age_30_2cr": 19100,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Accelerated full sum payout",
        "key_features": [
            "Comprehensive 3-in-1 protection covering death, terminal illness, and permanent disability",
            "Accelerated critical illness benefit for 34 illnesses payable on first medical confirmation",
            "Attractive non-smoker and women discount slabs",
            "Smart Exit benefit returning all premiums at designated retirement years"
        ],
        "pros": [
            "Broad nationwide institutional presence and efficient claims handling",
            "Very clear policy wording on terminal illness certification"
        ],
        "cons_or_cautions": [
            "Critical illness rider premium increases if opted with level term"
        ],
        "sub_limits": "None",
        "suitability": "Solid all-weather term choice with broad institutional reputation and attractive pricing for non-smokers.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs"
    },
    {
        "id": "term_kotak_eterm",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "Kotak Mahindra Life",
        "product_name": "Kotak e-Term",
        "csr_3yr_avg": 98.82,
        "asr_percentage": 96.9,
        "solvency_ratio": 2.62,
        "claim_settlement_speed_days": 1.4,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 7900,
        "approx_annual_premium_age_35_1cr": 13400,
        "approx_annual_premium_age_45_1cr": 25800,
        "approx_annual_premium_age_30_2cr": 17900,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Included",
        "key_features": [
            "Highly competitive pricing across young age bands (18-35)",
            "Highest solvency ratio among top private insurers (2.62x)",
            "Multiple plan options: Life, Life Plus (accidental cover), and Life Secure (premium waiver)",
            "Special Exit value allowing policy surrender at age 65 with full premium refund"
        ],
        "pros": [
            "Exceptional financial solvency and balance sheet robustness",
            "Very economical premium rates for healthy non-smokers"
        ],
        "cons_or_cautions": [
            "Fewer digital add-on riders compared to HDFC or Max Life"
        ],
        "sub_limits": "None",
        "suitability": "Cost-conscious breadwinners seeking the lowest premium for high-quality corporate solvency.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs"
    },
    {
        "id": "term_sbi_eshield",
        "category": "LIFE_TERM",
        "category_label": "Pure Term Life",
        "insurer": "SBI Life Insurance",
        "product_name": "eShield Next",
        "csr_3yr_avg": 97.58,
        "asr_percentage": 95.8,
        "solvency_ratio": 2.15,
        "claim_settlement_speed_days": 1.8,
        "min_entry_age": 18,
        "max_entry_age": 65,
        "approx_annual_premium_age_25_1cr": 8100,
        "approx_annual_premium_age_35_1cr": 13900,
        "approx_annual_premium_age_45_1cr": 26800,
        "approx_annual_premium_age_30_2cr": 18500,
        "zero_cost_exit": True,
        "terminal_illness_benefit": "Included",
        "key_features": [
            "Backed by India's largest public banking conglomerate",
            "Level cover, increasing cover, and future-proofing milestone options",
            "Accidental total and permanent disability benefit rider",
            "Extensive rural and semi-urban claims assistance footprint"
        ],
        "pros": [
            "Unrivaled brand trust and branch accessibility across tier-2/3/4 India",
            "Simple, transparent underwriting guidelines"
        ],
        "cons_or_cautions": [
            "Claim turn-around time is slightly slower than tech-first private insurers"
        ],
        "sub_limits": "None",
        "suitability": "Ideal for families that prioritize public sector trust and physical branch accessibility across India.",
        "tax_benefit": "Section 80C deduction up to Rs 1.5 Lakhs"
    },

    # ------------------ COMPREHENSIVE RETAIL HEALTH ------------------
    {
        "id": "health_ergo_optima_secure",
        "category": "HEALTH_COMPREHENSIVE",
        "category_label": "Retail Health",
        "insurer": "HDFC ERGO General Insurance",
        "product_name": "Optima Secure",
        "icr_percentage": 68.2,
        "network_hospitals_count": 13000,
        "room_rent_capping": "Zero Sub-limit (Any Room Category / Single Private AC)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "ped_waiting_period_years": 3,
        "cashless_settlement_speed_hours": 1.0,
        "approx_annual_premium_individual_10L_age_30": 11400,
        "approx_annual_premium_individual_25L_age_30": 16200,
        "approx_annual_premium_floater_2A_1C_10L_age_32": 24800,
        "approx_annual_premium_floater_2A_1C_25L_age_32": 32600,
        "approx_annual_premium_senior_parent_10L_age_65": 42000,
        "key_features": [
            "Secure Benefit: Instantly doubles your base cover from Day 1 (10L base gives 20L protection) at zero extra premium",
            "Plus Benefit: 100% sum insured bonus in 2 claim-free years (50% per year), scaling a 10L cover to 40L total coverage",
            "Restore Benefit: 100% automatic reload of sum insured unlimited times in a policy year for any illness",
            "Zero proportionate deduction clause: Choose any room without bill deductions"
        ],
        "pros": [
            "4X effective coverage over 2 years makes it the strongest medical inflation defense in India",
            "Zero room rent restrictions eliminates surprise out-of-pocket hospital deductions",
            "Over 13,000 cashless hospitals with near-instant pre-authorization"
        ],
        "cons_or_cautions": [
            "3-year pre-existing disease waiting period (can be reduced to 1 or 2 years with add-on rider)"
        ],
        "sub_limits": "Zero disease-specific sub-limits; zero room rent cap",
        "suitability": "Gold standard comprehensive retail health cover. Fiduciary choice for single earners and young families seeking complete hospital bill protection.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000 (Self/Family) & up to Rs 50,000 (Senior Parents)"
    },
    {
        "id": "health_care_supreme",
        "category": "HEALTH_COMPREHENSIVE",
        "category_label": "Retail Health",
        "insurer": "Care Health Insurance",
        "product_name": "Care Supreme",
        "icr_percentage": 64.8,
        "network_hospitals_count": 11000,
        "room_rent_capping": "Zero Sub-limit (All Room Categories)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "ped_waiting_period_years": 3,
        "cashless_settlement_speed_hours": 1.2,
        "approx_annual_premium_individual_10L_age_30": 9800,
        "approx_annual_premium_individual_25L_age_30": 14200,
        "approx_annual_premium_floater_2A_1C_10L_age_32": 21500,
        "approx_annual_premium_floater_2A_1C_25L_age_32": 28400,
        "approx_annual_premium_senior_parent_10L_age_65": 38500,
        "key_features": [
            "Cumulative Bonus Super: 500% cumulative bonus over 5 claim-free years (10L grows to 60L)",
            "Unlimited automatic recharge of sum insured for unrelated and related illnesses",
            "Free annual health check-up from Day 1 for all covered policy members",
            "Zero co-payment and zero sub-limits on common procedures (cataract, joint replacement)"
        ],
        "pros": [
            "Massive 500% no-claim bonus scaling provides industry-leading long-term value",
            "Extremely competitive pricing (~15% cheaper than HDFC ERGO for comparable sum insured)"
        ],
        "cons_or_cautions": [
            "Requires careful disclosure of past medical OPD consultations during underwriting"
        ],
        "sub_limits": "No room rent sub-limit; no treatment capping",
        "suitability": "Best value-for-money comprehensive retail policy for young healthy families seeking maximum cumulative bonus growth.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },
    {
        "id": "health_niva_reassure",
        "category": "HEALTH_COMPREHENSIVE",
        "category_label": "Retail Health",
        "insurer": "Niva Bupa Health Insurance",
        "product_name": "ReAssure 2.0 (Lock the Clock)",
        "icr_percentage": 62.9,
        "network_hospitals_count": 10500,
        "room_rent_capping": "Zero Sub-limit (Any Room Category)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "ped_waiting_period_years": 2,
        "cashless_settlement_speed_hours": 1.1,
        "approx_annual_premium_individual_10L_age_30": 10600,
        "approx_annual_premium_individual_25L_age_30": 15100,
        "approx_annual_premium_floater_2A_1C_10L_age_32": 23200,
        "approx_annual_premium_floater_2A_1C_25L_age_32": 29800,
        "approx_annual_premium_senior_parent_10L_age_65": 39800,
        "key_features": [
            "Lock the Clock: Pay the premium of your entry age until you make your very first claim",
            "Booster+: Unspent base sum insured carries forward to next year, accumulating up to 10X (10L becomes 1 Cr)",
            "ReAssure+: Unlimited recharges triggered from the very first claim, usable for identical illnesses",
            "Shorted 2-year PED waiting period as standard"
        ],
        "pros": [
            "Lock the Clock prevents age-bracket premium spikes during your healthy 20s and 30s",
            "Shorter 2-year pre-existing disease waiting window compared to industry 3-year standard"
        ],
        "cons_or_cautions": [
            "Premium locks reset once a claim is paid"
        ],
        "sub_limits": "Zero room rent limit",
        "suitability": "Best for young healthy professionals (age 22-35) looking to hedge future health insurance inflation by freezing entry-age pricing.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },
    {
        "id": "health_aditya_birla_activ_one",
        "category": "HEALTH_COMPREHENSIVE",
        "category_label": "Retail Health",
        "insurer": "Aditya Birla Health Insurance",
        "product_name": "Activ One (Max Cover)",
        "icr_percentage": 65.4,
        "network_hospitals_count": 11500,
        "room_rent_capping": "Zero Sub-limit (Single AC / Any Room)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "ped_waiting_period_years": 1,
        "cashless_settlement_speed_hours": 1.3,
        "approx_annual_premium_individual_10L_age_30": 11800,
        "approx_annual_premium_individual_25L_age_30": 16900,
        "approx_annual_premium_floater_2A_1C_10L_age_32": 25200,
        "approx_annual_premium_senior_parent_10L_age_65": 43500,
        "key_features": [
            "HealthReturns: Earn up to 100% of your annual premium back through active daily steps / gym tracking",
            "Chronic Management: Day-1 cover for hypertension, diabetes, asthma, and cholesterol via health coaching",
            "Shortest 1-year PED waiting period option in the retail market",
            "Super Reload: Unlimited 100% restoration of sum insured"
        ],
        "pros": [
            "Only 1-year waiting period for pre-existing conditions (fastest in India)",
            "High rewards for fitness enthusiasts (can effectively halve the net premium)"
        ],
        "cons_or_cautions": [
            "Requires active wearable tracking to unlock maximum health returns"
        ],
        "sub_limits": "None",
        "suitability": "Ideal for active individuals wanting premium cashback, or individuals with mild chronic indicators (BP/sugar) wanting fast Day-1 coverage.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },
    {
        "id": "health_star_premier",
        "category": "HEALTH_COMPREHENSIVE",
        "category_label": "Retail Health",
        "insurer": "Star Health Insurance",
        "product_name": "Star Health Premier / Comprehensive",
        "icr_percentage": 67.5,
        "network_hospitals_count": 14200,
        "room_rent_capping": "Single Standard AC Room",
        "zero_room_rent_capping": False,
        "co_pay": "0% for entry before 60 years",
        "ped_waiting_period_years": 2,
        "cashless_settlement_speed_hours": 1.5,
        "approx_annual_premium_individual_10L_age_30": 10400,
        "approx_annual_premium_floater_2A_1C_10L_age_32": 22900,
        "approx_annual_premium_senior_parent_10L_age_65": 41500,
        "key_features": [
            "Largest dedicated cashless hospital network across tier-1, tier-2, and tier-3 Indian towns",
            "In-house claim processing units without reliance on external third-party administrators (TPAs)",
            "Cover for non-allopathic treatments (AYUSH - Ayurveda, Yoga, Unani, Siddha, Homeopathy)",
            "Automatic restoration of sum insured up to 100% upon exhaustion"
        ],
        "pros": [
            "Peerless cashless footprint in non-metro and semi-urban locations",
            "In-house claims doctor desk speeds up rural hospital billing"
        ],
        "cons_or_cautions": [
            "Room rent is restricted to Standard Single AC Room (upgrading to Deluxe causes proportionate bill deductions)"
        ],
        "sub_limits": "Standard AC room limitation; specific cataract sub-limits apply",
        "suitability": "Best for policyholders residing in or supporting parents in tier-2/3 cities where Star has the only cashless empanelment.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },

    # ------------------ SUPER TOP-UP HEALTH (FOR CORPORATE GMC BRIDGING) ------------------
    {
        "id": "super_topup_ergo_medisure",
        "category": "HEALTH_SUPER_TOPUP",
        "category_label": "Super Top-Up Health",
        "insurer": "HDFC ERGO General Insurance",
        "product_name": "my:health Medisure Super Top Up",
        "deductible_options": [300000, 500000, 1000000],
        "sum_insured_options": [2500000, 5000000, 10000000],
        "approx_annual_premium_25L_5L_deductible": 2950,
        "approx_annual_premium_50L_5L_deductible": 3800,
        "approx_annual_premium_50L_10L_deductible": 3200,
        "approx_annual_premium_1Cr_10L_deductible": 4900,
        "room_rent_capping": "Zero Sub-limit (Any Room Category)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "key_features": [
            "Converts an ordinary Rs 3L-5L corporate employer GMC cover into an impregnable Rs 25L-50L shield for ~Rs 250/month",
            "Aggregates cumulative hospital bills across an entire policy year to satisfy the deductible (not per-incident)",
            "Zero pre-policy medical check-up requirement up to age 55",
            "Zero room rent restrictions once the deductible threshold is crossed"
        ],
        "pros": [
            "Massive fiduciary leverage: 10X more coverage at 80% lower cost than buying a redundant second retail base policy",
            "Seamless claim aggregation: your employer insurer pays the first 5L, HDFC ERGO pays the next 50L directly"
        ],
        "cons_or_cautions": [
            "Deductible must be satisfied before policy kicks in (ideally paid by employer GMC or base policy)"
        ],
        "sub_limits": "Deductible threshold must be crossed by base policy or self-payment",
        "suitability": "Absolute fiduciary imperative for salaried professionals with ₹3L-₹7L employer GMC. Eliminates corporate coverage gaps for pennies on the rupee.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },
    {
        "id": "super_topup_care_enhance",
        "category": "HEALTH_SUPER_TOPUP",
        "category_label": "Super Top-Up Health",
        "insurer": "Care Health Insurance",
        "product_name": "Care Enhance Super Top-Up",
        "deductible_options": [300000, 500000, 1000000],
        "sum_insured_options": [3000000, 5000000, 10000000],
        "approx_annual_premium_25L_5L_deductible": 2700,
        "approx_annual_premium_50L_5L_deductible": 3400,
        "approx_annual_premium_50L_10L_deductible": 2900,
        "approx_annual_premium_1Cr_10L_deductible": 4400,
        "room_rent_capping": "Zero Sub-limit",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "key_features": [
            "Aggregates all family hospitalizations throughout the 365-day policy period against the deductible",
            "Comprehensive in-patient care, 540+ day care treatments, and 30-day pre / 60-day post hospitalization",
            "Instant digital policy issuance with zero paperwork",
            "No co-payment clause irrespective of age at entry"
        ],
        "pros": [
            "Extremely low annual cost (~₹225 to ₹280 / month)",
            "Covers critical ICU and specialized oncology treatments without sub-limits"
        ],
        "cons_or_cautions": [
            "Requires keeping track of base policy claim settlement discharge summaries to trigger claims"
        ],
        "sub_limits": "Deductible threshold applies",
        "suitability": "Top companion for tech professionals and corporate employees seeking an ultra-low-cost catastrophic illness backstop.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },
    {
        "id": "super_topup_niva_recharge",
        "category": "HEALTH_SUPER_TOPUP",
        "category_label": "Super Top-Up Health",
        "insurer": "Niva Bupa Health Insurance",
        "product_name": "Health Recharge Super Top-Up",
        "deductible_options": [300000, 500000, 1000000],
        "sum_insured_options": [2000000, 4000000, 9500000],
        "approx_annual_premium_25L_5L_deductible": 2850,
        "approx_annual_premium_50L_5L_deductible": 3600,
        "approx_annual_premium_50L_10L_deductible": 3100,
        "approx_annual_premium_1Cr_10L_deductible": 4650,
        "room_rent_capping": "Zero Sub-limit (All Rooms)",
        "zero_room_rent_capping": True,
        "co_pay": "0%",
        "key_features": [
            "Flexible deductible laddering from Rs 1 Lakh up to Rs 10 Lakhs",
            "Organ donor expense coverage up to the full sum insured",
            "Pharmacy and diagnostic pre/post hospitalization expense reimbursement",
            "Worldwide emergency medical coverage available as rider"
        ],
        "pros": [
            "Zero room rent restrictions prevents ICU proportionate reductions",
            "Flexible deductible tiers fit perfectly with varied employer sum insured levels"
        ],
        "cons_or_cautions": [
            "Waiting periods for pre-existing conditions mirror base policies (2-3 years)"
        ],
        "sub_limits": "Deductible threshold applies",
        "suitability": "Ideal for professionals wanting to pair an existing retail or employer policy with high-limit organ donor and critical surgery cover.",
        "tax_benefit": "Section 80D deduction up to Rs 25,000"
    },

    # ------------------ PERSONAL ACCIDENT & DISABILITY ------------------
    {
        "id": "accident_ergo_pa",
        "category": "PERSONAL_ACCIDENT",
        "category_label": "Personal Accident",
        "insurer": "HDFC ERGO General Insurance",
        "product_name": "Personal Accident Comprehensive",
        "approx_annual_premium_25L": 2100,
        "approx_annual_premium_50L": 3800,
        "approx_annual_premium_1Cr": 6500,
        "key_features": [
            "100% lump sum payout upon Accidental Death or Permanent Total Disability (PTD - loss of limbs, sight, paralysis)",
            "Weekly income replacement benefit during Temporary Total Disability (up to Rs 50,000/week for 104 weeks)",
            "Child Education Grant: Additional lump sum benefit per dependent child to secure schooling",
            "24x7 worldwide coverage regardless of travel or geographical jurisdiction"
        ],
        "pros": [
            "Life insurance only covers death; personal accident is the only instrument that replaces income during permanent disability",
            "Exceptional value: ₹1 Crore disability protection for just ~₹540 / month"
        ],
        "cons_or_cautions": [
            "Does not cover illness-based disability (only external accidental trauma)"
        ],
        "sub_limits": "Pre-existing disabilities excluded; adventure sports require specific endorsement",
        "suitability": "Essential fiduciary requirement for daily commuters, active drivers, and primary breadwinners whose family income depends on physical capability.",
        "tax_benefit": "Asset protection instrument (Not eligible under Section 80D)"
    },
    {
        "id": "accident_star_pa",
        "category": "PERSONAL_ACCIDENT",
        "category_label": "Personal Accident",
        "insurer": "Star Health Insurance",
        "product_name": "Accident Care Individual Insurance",
        "approx_annual_premium_25L": 1950,
        "approx_annual_premium_50L": 3500,
        "approx_annual_premium_1Cr": 6200,
        "key_features": [
            "Covers accidental death, permanent total disability, and permanent partial disability (specified scale)",
            "Home & vehicle modification allowance if disability requires wheelchair modifications or ramp installations",
            "Transportation of mortal remains and ambulance charges included",
            "Cumulative bonus of 5% per claim-free year up to 50%"
        ],
        "pros": [
            "Includes home and vehicle wheelchair modification costs up to Rs 1 Lakh",
            "Very affordable entry-tier pricing"
        ],
        "cons_or_cautions": [
            "Weekly temporary disability benefit requires additional rider"
        ],
        "sub_limits": "Standard accidental policy exclusions",
        "suitability": "High-value personal accident coverage with built-in accessibility modification grants.",
        "tax_benefit": "Asset protection instrument"
    },

    # ------------------ COMPREHENSIVE MOTOR ------------------
    {
        "id": "motor_acko_comprehensive",
        "category": "MOTOR_COMPREHENSIVE",
        "category_label": "Motor Insurance",
        "insurer": "Acko General Insurance",
        "product_name": "Acko Zero-Depreciation Car Insurance",
        "claim_settlement_speed_days": 1.0,
        "approx_annual_premium_hatchback": 11500,
        "approx_annual_premium_suv": 22500,
        "approx_annual_premium_bike": 2400,
        "key_features": [
            "100% digital zero-paperwork claim settlement via smartphone app",
            "Zero-depreciation bumper-to-bumper coverage on plastic, rubber, fiber, and metal parts",
            "Doorstep vehicle pickup, cashless garage repair, and 3-day turnaround with complimentary cab vouchers",
            "Zero commission direct-to-consumer pricing (~20-30% cheaper than dealer quotes)"
        ],
        "pros": [
            "Eliminates middleman dealer markups and paper forms completely",
            "Immediate digital video claims processing for minor dents and scratches"
        ],
        "cons_or_cautions": [
            "Best experienced in tier-1 metro cities where Acko's dedicated repair network is dense"
        ],
        "sub_limits": "Standard compulsory deductible applies",
        "suitability": "Modern vehicle owners seeking transparent pricing, zero dealer commission markup, and fast smartphone claims.",
        "tax_benefit": "Personal asset protection (no Section 80D deduction)"
    },
    {
        "id": "motor_digit_comprehensive",
        "category": "MOTOR_COMPREHENSIVE",
        "category_label": "Motor Insurance",
        "insurer": "Go Digit General Insurance",
        "product_name": "Digit Comprehensive Motor Cover",
        "claim_settlement_speed_days": 1.2,
        "approx_annual_premium_hatchback": 12200,
        "approx_annual_premium_suv": 23800,
        "approx_annual_premium_bike": 2600,
        "key_features": [
            "Self-inspection audio-guided photo upload on your smartphone for instant claim evaluation",
            "Engine & Gearbox Protection add-on: shields against water ingression (hydro-lock) during urban floods",
            "Return to Invoice (RTI) cover pays full ex-showroom vehicle cost in event of total theft or write-off",
            "Consumables Cover pays for engine oil, nuts, bolts, coolant, and brake fluid during claims"
        ],
        "pros": [
            "Crucial engine protection against monsoonal urban water-logging",
            "Over 6,000 cashless network garages across India"
        ],
        "cons_or_cautions": [
            "Older vehicles (> 5 years) have higher zero-dep add-on costs"
        ],
        "sub_limits": "Standard compulsory deductible applies",
        "suitability": "Ideal for urban car owners exposed to monsoon flooding, offering vital engine hydro-lock and consumables coverage.",
        "tax_benefit": "Personal asset protection"
    }
]

def get_catalog_products(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns curated insurance products filtered optionally by category."""
    if not category or category == "ALL":
        return INSURANCE_CATALOG
    return [p for p in INSURANCE_CATALOG if p.get("category") == category]

def find_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Finds a single product by unique ID."""
    for p in INSURANCE_CATALOG:
        if p["id"] == product_id:
            return p
    return None
