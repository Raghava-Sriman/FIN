# FIN — AI-Powered Personal Financial Assistant
## Comprehensive Project Plan & Technical Specification

> **Project Codename**: FIN  
> **Version**: 1.0  
> **Last Updated**: 2026-10-21  
> **Status**: Planning Phase

---

## Table of Contents

1. [Project Vision & Problem Statement](#1-project-vision--problem-statement)
2. [Product Overview](#2-product-overview)
3. [System Architecture](#3-system-architecture)
4. [Feature Breakdown (Detailed)](#4-feature-breakdown-detailed)
   - 4.1 [Statement Upload & Parsing Engine](#41-statement-upload--parsing-engine)
   - 4.2 [Transaction Categorization Engine](#42-transaction-categorization-engine)
   - 4.3 [Monthly Consumption Tracker](#43-monthly-consumption-tracker)
   - 4.4 [Recurring & Subscription Detector](#44-recurring--subscription-detector)
   - 4.5 [Financial Analytics Dashboard](#45-financial-analytics-dashboard)
   - 4.6 [AI Suggestor / Financial Copilot](#46-ai-suggestor--financial-copilot)
   - 4.7 [Insurance Gap Planner](#47-insurance-gap-planner)
   - 4.8 [Goal Planner & Simulator](#48-goal-planner--simulator)
   - 4.9 [Tax Deduction Finder](#49-tax-deduction-finder)
   - 4.10 [Report Generator](#410-report-generator)
5. [Data Models & Database Schema](#5-data-models--database-schema)
6. [AI/ML Pipeline Details](#6-aiml-pipeline-details)
7. [Technology Stack](#7-technology-stack)
8. [API Design](#8-api-design)
9. [Security & Privacy Architecture](#9-security--privacy-architecture)
10. [UI/UX Design Guidelines](#10-uiux-design-guidelines)
11. [Implementation Roadmap (Phased)](#11-implementation-roadmap-phased)
12. [Testing Strategy](#12-testing-strategy)
13. [Future Enhancements (V2+)](#13-future-enhancements-v2)
14. [Risks & Mitigations](#14-risks--mitigations)
15. [Project Directory Structure](#15-project-directory-structure)

---

## 1. Project Vision & Problem Statement

### The Problem

Most people have no idea where their money goes. They check their bank balance, feel anxious, and move on. The few who try to track expenses face these barriers:

- **Manual entry fatigue**: Apps like YNAB or Walnut require users to log every transaction by hand. Compliance drops within 2 weeks for 80% of users.
- **Privacy anxiety**: Aggregators like Plaid or India's Account Aggregator framework require sharing live bank credentials with third-party servers. Many users (rightfully) hesitate.
- **Backward-looking only**: Existing tools show "you spent ₹12,000 on dining last month" but never tell you *what to do about it*, how it affects your retirement timeline, or whether your insurance coverage is adequate.
- **No unified view**: Credit card statements, savings account statements, and loan statements live in separate PDFs. Nobody stitches them together.

### The Vision

**FIN** is a privacy-first, AI-powered personal financial assistant that lets users upload their bank/credit card statements (PDF, CSV, or Excel) and instantly receive:

1. A complete categorized spending breakdown for the entire year
2. Detection of every recurring charge, subscription, and EMI
3. Month-over-month consumption trends and anomaly alerts
4. Personalized savings suggestions based on *their actual spending patterns*
5. An insurance gap analysis showing whether they're under-insured
6. A goal planning engine that simulates how quickly they can reach financial targets
7. A conversational AI copilot that answers questions about their finances in plain language

**The key insight**: A single 12-month bank statement contains an extraordinary amount of signal about a person's financial life — income stability, spending habits, risk exposure, savings discipline, subscription bloat, and insurance coverage. We extract *all of it*.

---

## 2. Product Overview

### Core User Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          USER JOURNEY                                    │
│                                                                          │
│  ① Upload Statement(s)                                                   │
│     PDF / CSV / Excel from any bank                                      │
│          │                                                               │
│          ▼                                                               │
│  ② Automatic Processing (30-90 seconds)                                  │
│     Parse → Clean → Categorize → Detect Patterns → Calculate Metrics     │
│          │                                                               │
│          ▼                                                               │
│  ③ Interactive Dashboard                                                 │
│     Spending breakdown, trends, recurring charges, alerts                │
│          │                                                               │
│          ▼                                                               │
│  ④ Planning & Advisory Modules                                           │
│     Goal Planner │ Insurance Planner │ AI Suggestions │ Tax Finder       │
│          │                                                               │
│          ▼                                                               │
│  ⑤ Export & Action                                                       │
│     Download PDF report │ Set up goals │ Cancel subscriptions            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Target Users

| Segment | Description | Primary Need |
|---------|-------------|--------------|
| **Young Professionals (22-30)** | First job, first salary, no financial literacy | "Where is my money going?" |
| **Family Households (30-45)** | Dual income, kids, EMIs, insurance needs | "Am I saving enough? Am I insured enough?" |
| **Freelancers & Gig Workers** | Irregular income, multiple accounts | "How do I budget with variable income?" |
| **Pre-Retirees (50-60)** | Planning corpus, reducing risk | "Will I have enough?" |

---

## 3. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Upload Page  │  │  Dashboard   │  │  Goal Planner│  │  AI Chat     │    │
│  │  (Drag+Drop)  │  │  (Charts)    │  │  (Forms+Sim) │  │  (Copilot)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         └──────────────────┴────────────────┴────────────────┘              │
│                                    │                                        │
│                            REST API / WebSocket                             │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              API GATEWAY                                    │
│                         (FastAPI + Auth Middleware)                          │
│                                    │                                        │
│    ┌───────────────────────────────┼──────────────────────────────┐         │
│    │                               │                              │         │
│    ▼                               ▼                              ▼         │
│ ┌──────────────┐  ┌────────────────────────────┐  ┌──────────────────┐     │
│ │  INGESTION   │  │  ANALYTICS ENGINE          │  │  INTELLIGENCE    │     │
│ │  SERVICE     │  │  (Deterministic Python)     │  │  SERVICE         │     │
│ │              │  │                              │  │                  │     │
│ │ • PDF Parse  │  │ • Monthly Aggregations      │  │ • LLM Classify  │     │
│ │ • CSV Parse  │  │ • Burn Rate Calc            │  │ • LLM Chat      │     │
│ │ • OCR        │  │ • Savings Rate              │  │ • LLM Insights  │     │
│ │ • PII Mask   │  │ • Recurring Detection       │  │ • RAG Pipeline  │     │
│ │ • Normalize  │  │ • Goal Simulation           │  │                  │     │
│ │              │  │ • Insurance Gap Math         │  │                  │     │
│ └──────┬───────┘  └──────────┬─────────────────┘  └────────┬─────────┘     │
│        │                     │                              │               │
│        └─────────────────────┼──────────────────────────────┘               │
│                              │                                              │
│                    ┌─────────▼──────────┐                                   │
│                    │    DATABASE LAYER   │                                   │
│                    │                     │                                   │
│                    │  PostgreSQL         │                                   │
│                    │  + Redis (Cache)    │                                   │
│                    │  + File Storage     │                                   │
│                    └────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
Statement File
     │
     ▼
[1. File Validation]
     │  ── Check file type, size limits, password-protected PDF handling
     ▼
[2. Raw Extraction]
     │  ── pdfplumber for text PDFs, Tesseract OCR for scanned,
     │     direct pandas read for CSV/Excel
     ▼
[3. PII Redaction]
     │  ── Strip account numbers, customer names, branch addresses,
     │     Aadhaar/PAN/SSN before any external API call
     ▼
[4. Transaction Normalization]
     │  ── Standardize to schema: {date, narration, debit, credit, balance, mode}
     │  ── Handle multi-currency, different date formats, running vs closing balance
     ▼
[5. Merchant Cleaning]
     │  ── Regex rules for known patterns (UPI/NEFT/IMPS prefixes)
     │  ── Extract clean merchant name from noisy narration strings
     ▼
[6. Categorization]
     │  ── Tier 1: Rule-based regex matching (90% of known merchants)
     │  ── Tier 2: LLM fallback for ambiguous narrations (10%)
     │  ── User correction loop (optional manual override → retrains rules)
     ▼
[7. Pattern Detection]
     │  ── Recurring charges (subscriptions, EMIs, rent, salary)
     │  ── Seasonal spending patterns
     │  ── Anomalous transactions (spikes, unusual merchants)
     ▼
[8. Metric Computation]
     │  ── All computations in Python (pandas/polars) — NEVER by LLM
     │  ── Monthly aggregates, ratios, projections, simulations
     ▼
[9. Insight Generation]
     │  ── LLM generates human-readable explanations grounded on
     │     pre-computed numbers passed in prompt context
     ▼
[10. Presentation]
      ── Dashboard charts, cards, tables, chat interface
```

---

## 4. Feature Breakdown (Detailed)

---

### 4.1 Statement Upload & Parsing Engine

#### What It Does
Accepts bank or credit card statements in multiple formats and extracts every transaction into a clean, structured table.

#### Supported Formats

| Format | Method | Complexity |
|--------|--------|------------|
| **CSV** | Direct `pandas.read_csv()` with delimiter detection | Low |
| **Excel (.xlsx / .xls)** | `openpyxl` / `xlrd` via pandas | Low |
| **Text-based PDF** | `pdfplumber` table extraction with coordinate-based cell detection | Medium |
| **Scanned/Image PDF** | `pytesseract` OCR → text → table parsing | High |
| **Encrypted PDF** | User provides password client-side → `pikepdf` unlocks → pdfplumber | Medium |

#### Parsing Challenges & Solutions

**Challenge 1: Every bank formats statements differently**
- SBI puts narration in column 3, HDFC puts it in column 2
- Some banks use "Withdrawal" and "Deposit", others use "Debit" and "Credit"
- Date formats vary: DD/MM/YYYY, MM-DD-YYYY, DD-Mon-YYYY

**Solution**: Bank-specific template configs (JSON files mapping column positions and header names). For unknown banks, use heuristic detection:
```
1. Scan header row for keywords: "date", "narration"/"description"/"particulars",
   "debit"/"withdrawal", "credit"/"deposit", "balance"
2. Infer column mapping automatically
3. Fall back to LLM-based column detection if heuristics fail
```

**Challenge 2: Multi-page tables with repeated headers**
- Page 2 of a PDF repeats the header row mid-table

**Solution**: Detect and deduplicate header rows using header fingerprinting (exact string match with known header row).

**Challenge 3: Merged cells, subtotals, and summary rows**
- Statements often include "Total for January" or "Opening Balance" rows mixed into the transaction table

**Solution**: Filter rows where the date field is empty or contains aggregate keywords ("total", "opening", "closing", "balance b/f").

#### Output Schema
Every successfully parsed transaction is normalized to:
```json
{
  "id": "uuid-v4",
  "date": "2025-03-15",
  "narration": "UPI/428192841/ZOMATO/zomato@paytm/Bangalore",
  "clean_merchant": "Zomato",
  "debit": 459.00,
  "credit": null,
  "balance": 34521.50,
  "mode": "UPI",
  "category": null,
  "sub_category": null,
  "is_recurring": false,
  "tags": [],
  "source_file": "hdfc_savings_2025.pdf",
  "source_page": 3,
  "source_row": 47
}
```

#### Error Handling
- **Corrupt PDF**: Return clear error message with instructions to re-download from bank
- **Password-protected PDF**: Prompt for password, retry parsing
- **Partial extraction**: If >80% of expected rows are extracted (based on date range density), proceed with a warning. If <80%, flag for manual review.
- **Duplicate uploads**: Detect via file hash (SHA-256) and warn user if same statement was already uploaded

---

### 4.2 Transaction Categorization Engine

#### What It Does
Assigns every transaction a **category** and **sub-category** using a hybrid rule-based + AI approach. This is the foundation that powers every downstream engine.

#### Category Taxonomy (Complete)

```
INCOME
├── Primary Salary
├── Freelance / Contract Income
├── Rental Income
├── Dividends & Interest
├── Capital Gains / Stock Sales
├── Gifts & Peer Transfers (Received)
├── Refunds & Cashbacks
└── Government Benefits / Subsidies

FIXED EXPENSES (Non-Negotiable)
├── Rent / Mortgage EMI
├── Utility Bills
│   ├── Electricity
│   ├── Water
│   ├── Gas / Piped Gas
│   └── Internet / Broadband
├── Loan EMIs
│   ├── Home Loan
│   ├── Car Loan
│   ├── Personal Loan
│   ├── Education Loan
│   └── Credit Card EMI
├── Insurance Premiums
│   ├── Life Insurance
│   ├── Health Insurance
│   ├── Vehicle Insurance
│   └── Home Insurance
├── Subscriptions & Memberships
│   ├── Streaming (Netflix, Spotify, YouTube Premium, etc.)
│   ├── Software (iCloud, Microsoft 365, Adobe, etc.)
│   ├── Gym / Fitness
│   ├── News / Magazine
│   └── Other Recurring
└── Child Education Fees / Tuition

VARIABLE ESSENTIALS (Necessary but amount varies)
├── Groceries & Household Supplies
├── Healthcare & Pharmacy
│   ├── Doctor Visits
│   ├── Lab Tests
│   ├── Medicines
│   └── Hospital Bills
├── Transportation & Commute
│   ├── Fuel / Petrol
│   ├── Public Transit (Metro, Bus)
│   ├── Ride-hailing (Uber, Ola, Lyft)
│   └── Vehicle Maintenance & Parking
├── Communication
│   ├── Mobile Recharge / Postpaid
│   └── Landline
└── Personal Care (Salon, Grooming)

DISCRETIONARY (Wants, not needs)
├── Dining Out & Food Delivery
│   ├── Restaurants
│   ├── Cafes & Coffee Shops
│   ├── Food Delivery (Swiggy, Zomato, DoorDash)
│   └── Bars & Alcohol
├── Shopping
│   ├── Clothing & Apparel
│   ├── Electronics & Gadgets
│   ├── Home Decor & Furniture
│   └── Online Marketplace (Amazon, Flipkart)
├── Entertainment & Leisure
│   ├── Movies & Events
│   ├── Gaming
│   ├── Hobbies & Sports
│   └── Books
├── Travel & Vacation
│   ├── Flights
│   ├── Hotels & Accommodation
│   ├── Travel Activities
│   └── Travel Food & Transport
├── Gifts & Donations (Given)
└── Miscellaneous / Uncategorized

INVESTMENTS & SAVINGS
├── Mutual Fund SIPs
├── Stock Purchases
├── Fixed Deposits
├── PPF / NPS / 401k / IRA
├── Gold / Bonds
├── Crypto
├── Recurring Deposits
└── Emergency Fund Contributions

TRANSFERS (Internal)
├── Self-Transfer (Between own accounts)
├── Credit Card Payment
├── Wallet Top-up (PayPal, Paytm, etc.)
└── ATM Withdrawal (reclassified as cash spending)

FEES & CHARGES
├── Bank Charges & Maintenance Fees
├── ATM Fees
├── Late Payment Penalties
├── Forex / International Transaction Fees
├── Bounce / Dishonour Charges
└── GST / Service Tax on Banking
```

#### Categorization Pipeline

**Step 1: Payment Mode Extraction**
Parse the narration to identify the payment mode (UPI, NEFT, IMPS, RTGS, ACH, POS, ATM, Cheque, Auto-Debit). This immediately helps classify:
- ATM → Cash withdrawal
- NEFT/RTGS with salary keywords → Salary income
- Auto-Debit with insurance company names → Insurance premium

**Step 2: Merchant Name Cleaning**
Raw narrations are extremely noisy. Examples:
```
"UPI/428192841/ZOMATO/zomato@paytm/Bangalore"     →  "Zomato"
"POS 425361XXXX9182 SHELL PETROL PUMP MG ROAD"     →  "Shell Petrol Pump"
"NEFT/AXISCN0284719/ACME CORP PVT LTD/SALARY"     →  "Acme Corp (Salary)"
"ACH D- HDFC LIFE INSURANCE-ULIP PREMIUM"          →  "HDFC Life Insurance"
"CC 000382910184 AMAZON.IN"                         →  "Amazon"
```

Cleaning pipeline:
1. Remove UPI/NEFT/IMPS/RTGS prefixes and reference numbers (regex)
2. Remove trailing city names and branch codes
3. Normalize casing (title case)
4. Map known aliases (e.g., "AMZN" → "Amazon", "NFLX" → "Netflix")

**Step 3: Rule-Based Classification (Tier 1)**
A JSON lookup table mapping cleaned merchant names to categories:
```json
{
  "Zomato":        {"category": "Discretionary", "sub": "Food Delivery"},
  "Swiggy":        {"category": "Discretionary", "sub": "Food Delivery"},
  "Netflix":       {"category": "Fixed Expenses", "sub": "Streaming"},
  "Shell":         {"category": "Variable Essentials", "sub": "Fuel"},
  "Apollo Pharmacy": {"category": "Variable Essentials", "sub": "Medicines"},
  "HDFC Life":     {"category": "Fixed Expenses", "sub": "Life Insurance"}
}
```
This handles ~85-90% of transactions in a typical Indian or US bank statement.

**Step 4: LLM Classification (Tier 2 — Fallback)**
For the remaining 10-15% of ambiguous narrations, send to an LLM with a structured prompt:

```
You are a financial transaction classifier. Given the following bank
transaction narration, classify it into exactly one category and sub-category
from the provided taxonomy. Respond in JSON only.

Narration: "CHQ DEP 000482 RENT MR SHARMA"
Amount: ₹25,000 (Debit)

Output: {"category": "Fixed Expenses", "sub_category": "Rent", "confidence": 0.92}
```

**Step 5: User Feedback Loop**
- On the dashboard, each transaction shows its assigned category with an edit button
- When a user corrects a categorization, the correction is stored
- Periodically, accumulated corrections are used to update the Tier 1 rule table
- After 50+ corrections, fine-tune or update few-shot examples for the LLM prompt

#### Accuracy Targets
- **Tier 1 (Rule-based)**: 98% accuracy on matched merchants
- **Tier 2 (LLM fallback)**: 85-90% accuracy on ambiguous narrations
- **Overall after user corrections**: >95% accuracy within first session

---

### 4.3 Monthly Consumption Tracker

#### What It Does
Breaks down the user's financial activity month-by-month across the entire statement period, showing exactly how much came in, how much went out, what was saved, and where spending is trending.

#### Metrics Computed (All Deterministic — Python/Pandas)

**Per-Month Metrics:**

| Metric | Formula | Description |
|--------|---------|-------------|
| **Total Income** | `SUM(credits WHERE category = 'INCOME')` | All non-transfer money coming in |
| **Total Expenses** | `SUM(debits WHERE category != 'TRANSFERS' AND category != 'INVESTMENTS')` | All money going out (excluding self-transfers and investments) |
| **Net Savings** | `Total Income - Total Expenses` | Raw monthly savings |
| **Savings Rate** | `(Net Savings / Total Income) × 100` | Percentage of income saved |
| **Fixed Expense Ratio** | `(Fixed Expenses / Total Income) × 100` | How much income goes to non-negotiable costs |
| **Discretionary Spend** | `SUM(debits WHERE category = 'DISCRETIONARY')` | Total "wants" spending |
| **Essential Spend** | `SUM(debits WHERE category IN ('FIXED', 'VARIABLE ESSENTIALS'))` | Total "needs" spending |
| **Investment Rate** | `(Investments / Total Income) × 100` | Percentage being invested |

**Cross-Month Analytics:**

| Metric | Description |
|--------|-------------|
| **Month-over-Month (MoM) Change** | Percentage change in total expenses vs previous month |
| **Category-wise MoM Trend** | Per-category spending trend (e.g., "Dining Out increased 23% in December") |
| **Average Monthly Burn Rate** | Average total monthly expenses across all statement months |
| **Expense Volatility Score** | Standard deviation of monthly expenses ÷ mean → indicates spending consistency |
| **Income Stability Score** | Coefficient of variation of monthly income (important for freelancers) |
| **Seasonal Spending Patterns** | Identify months with consistently higher spending (holidays, back-to-school) |

**The 50/30/20 Benchmark:**
Compare the user's actual split against the classic budgeting rule:
- 50% → Needs (Fixed + Variable Essentials)
- 30% → Wants (Discretionary)
- 20% → Savings & Investments

Show a visual deviation chart — e.g., "You're at 62% Needs / 28% Wants / 10% Savings. Your needs allocation is 12 points above the benchmark."

#### Visualizations
1. **Stacked Bar Chart**: Monthly income vs expenses (stacked by category)
2. **Line Chart**: Savings rate trend over 12 months
3. **Donut Chart**: Overall annual spending by category
4. **Heatmap Calendar**: Daily spending intensity (darker = higher spend days)
5. **Waterfall Chart**: Income → Fixed → Variable → Discretionary → Net Savings flow

---

### 4.4 Recurring & Subscription Detector

#### What It Does
Automatically identifies all recurring charges in the statement — subscriptions, EMIs, rent, salary deposits, and any other periodic payments — without the user having to manually flag them.

#### Detection Algorithm

```
For each unique (merchant_name, approximate_amount) pair:

1. Collect all transaction dates for this merchant
2. Calculate intervals between consecutive transactions (in days)
3. Check against known periodicities:
   - Weekly:    interval ≈ 7 days  (tolerance: ±2 days)
   - Bi-weekly: interval ≈ 14 days (tolerance: ±2 days)
   - Monthly:   interval ≈ 30 days (tolerance: ±5 days)
   - Quarterly: interval ≈ 90 days (tolerance: ±10 days)
   - Annual:    interval ≈ 365 days (tolerance: ±15 days)

4. If ≥3 occurrences match a periodicity pattern → flag as RECURRING
5. Classify the recurring charge type:
   - Amount exactly same each time → "Fixed Recurring" (EMI, subscription)
   - Amount varies but merchant same → "Variable Recurring" (utility bill)
   - Credit (not debit) → "Recurring Income" (salary, rental income)
```

#### Recurring Charge Types

| Type | Example | Behavior |
|------|---------|----------|
| **Subscription** | Netflix ₹649/month | Same amount, same merchant, monthly |
| **Loan EMI** | Home Loan ₹45,000/month | Same amount, auto-debit, monthly |
| **Utility Bill** | Electricity ₹800-₹2400/month | Same merchant, variable amount |
| **Rent** | Landlord transfer ₹25,000/month | Same amount, same payee |
| **Insurance Premium** | LIC ₹12,000/quarter | Same amount, quarterly |
| **Salary** | Employer credit ₹85,000/month | Regular credit, same source |
| **SIP** | Mutual fund ₹10,000/month | Same amount, auto-debit |

#### Special Detections

**Zombie Subscriptions**:
Charges that have been recurring for >3 months but might be unused:
- Flag any subscription the user might have forgotten about
- Highlight total annual cost: "This ₹199/month subscription costs you ₹2,388/year"
- Compare against common duplicates: "You're paying for both YouTube Premium (₹149) and Spotify (₹119). Both include ad-free music."

**Price Creep Detection**:
Track if a recurring charge has gradually increased:
- "Netflix charged ₹499 in Jan-June but increased to ₹649 from July onwards (+30%)"

**Missing/Skipped Payments**:
If a recurring charge that appeared for 8+ months suddenly stops:
- Flag as "possibly cancelled" or "payment missed" for the user to verify

#### Output: Recurring Summary Table

```
┌────────────────────────┬──────────┬───────────┬──────────┬────────────────┐
│ Merchant               │ Amount   │ Frequency │ Annual   │ Status         │
├────────────────────────┼──────────┼───────────┼──────────┼────────────────┤
│ Home Loan EMI          │ ₹45,000  │ Monthly   │ ₹5,40,000│ Active         │
│ Netflix                │ ₹649     │ Monthly   │ ₹7,788   │ Price Increased│
│ Spotify                │ ₹119     │ Monthly   │ ₹1,428   │ Active         │
│ YouTube Premium        │ ₹149     │ Monthly   │ ₹1,788   │ Duplicate?     │
│ Gym Membership         │ ₹2,500   │ Monthly   │ ₹30,000  │ Active         │
│ iCloud Storage         │ ₹75      │ Monthly   │ ₹900     │ Zombie?        │
│ LIC Premium            │ ₹12,000  │ Quarterly │ ₹48,000  │ Active         │
│ Car Insurance          │ ₹18,500  │ Annual    │ ₹18,500  │ Active         │
├────────────────────────┼──────────┼───────────┼──────────┼────────────────┤
│ TOTAL RECURRING        │          │           │ ₹6,48,404│                │
│ % of Annual Income     │          │           │ 63.5%    │                │
└────────────────────────┴──────────┴───────────┴──────────┴────────────────┘
```

---

### 4.5 Financial Analytics Dashboard

#### What It Does
The central hub where all computed metrics, trends, and insights converge into an interactive, visual interface.

#### Dashboard Sections

**Section A: Financial Health Scorecard**
A single composite score (0-100) computed from:
```
Score = (Savings Rate Weight × 25) +
        (Emergency Fund Adequacy × 20) +
        (Debt-to-Income Ratio × 20) +
        (Insurance Coverage × 15) +
        (Expense Consistency × 10) +
        (Investment Rate × 10)

Rating Scale:
  90-100: Excellent — "Your finances are rock solid"
  75-89:  Good — "On track with room for optimization"
  50-74:  Fair — "Some areas need attention"
  25-49:  Needs Work — "Significant gaps to address"
  0-24:   Critical — "Immediate action recommended"
```

**Section B: Income vs Expense Overview**
- 12-month bar chart (income vs expenses)
- Running surplus/deficit line overlay
- Average monthly surplus highlighted

**Section C: Spending Breakdown**
- Interactive donut chart by category (click to drill into sub-categories)
- Top 10 merchants by total annual spend
- Category comparison vs national/benchmark averages

**Section D: Trend Analysis**
- Line charts for each major category over 12 months
- Highlighted months with anomalous spending (>1.5 standard deviations above mean)
- Weekend vs weekday spending split

**Section E: Cash Flow Calendar**
- Heatmap calendar view showing daily net cash flow
- Salary days automatically highlighted in green
- High-spend days highlighted in red
- Upcoming predicted recurring charges for the next 30 days

**Section F: Quick Insights Cards**
Auto-generated insight cards such as:
- "💡 Your top 3 discretionary merchants (Zomato, Amazon, Starbucks) account for 34% of all non-essential spending"
- "⚠️ You spent ₹8,400 on ATM withdrawal fees this year. Consider switching to a zero-fee account"
- "📈 Your grocery spending has increased 8% every month for the last 4 months"
- "🔄 You have 7 active subscriptions totaling ₹4,829/month. 2 may be duplicates"

---

### 4.6 AI Suggestor / Financial Copilot

#### What It Does
A conversational AI interface that answers user questions about their finances and proactively generates personalized suggestions — all grounded in the user's actual financial data.

#### Critical Architecture Rule

```
╔══════════════════════════════════════════════════════════════════╗
║  THE LLM NEVER CALCULATES. IT ONLY EXPLAINS AND ADVISES.       ║
║                                                                  ║
║  All numbers passed to the LLM are pre-computed by Python.       ║
║  The LLM receives a "financial context" object with all metrics  ║
║  and generates natural language insights grounded in that data.  ║
╚══════════════════════════════════════════════════════════════════╝
```

#### How It Works

**System Prompt Context Injection**:
Before every LLM call, inject a structured financial summary:
```
User Financial Context:
- Monthly Income: ₹85,000 (stable, salaried)
- Average Monthly Expenses: ₹68,400
- Savings Rate: 19.5% (below 20% benchmark)
- Top 3 Expense Categories: Rent (29%), Groceries (14%), Dining Out (11%)
- Active Subscriptions: 7 (total ₹4,829/month)
- Duplicate Subscriptions Detected: Spotify + YouTube Music
- Emergency Fund: ₹1,20,000 (covers 1.8 months — target is 6 months)
- Active Loans: Home Loan (₹45,000/month, 18 years remaining)
- Insurance: Term Life (₹1Cr cover), No Health Insurance detected
- Investment Rate: 11.7%
- Month with Highest Spend: December (₹94,200 — holiday season)
```

**Proactive Insight Types**:

| Insight Category | Example |
|------------------|---------|
| **Expense Optimization** | "Switching from food delivery (avg ₹8,200/month) to meal prep 3 days/week could save ₹3,000-4,000/month, boosting your savings rate to 24%." |
| **Subscription Audit** | "You're paying for both Spotify Premium (₹119) and YouTube Premium (₹149). YouTube Premium includes YouTube Music. Cancelling Spotify saves ₹1,428/year." |
| **Anomaly Alert** | "Your utility bill in August (₹4,800) was 2.4x your average (₹2,000). Worth checking for billing errors or AC overuse." |
| **Behavioral Nudge** | "You tend to spend 45% more on weekends. Setting a weekend spending cap of ₹3,000 could save ₹2,400/month." |
| **Fee Avoidance** | "You made 14 ATM withdrawals from other-bank ATMs, paying ₹2,800 in fees. Your bank allows 5 free withdrawals per month at own ATMs." |
| **Milestone Celebration** | "Great job! Your savings rate improved from 12% to 19.5% over the last 6 months. You're ₹30,000 closer to your emergency fund goal." |

**Conversational Chat Examples**:

User: "How much did I spend on food last year?"
→ System looks up: Groceries (₹1,68,000) + Dining Out (₹1,12,200) + Food Delivery (₹98,400) = ₹3,78,600
→ LLM responds: "You spent a total of ₹3,78,600 on food last year. Here's the breakdown: Groceries ₹1,68,000 (44%), Dining Out ₹1,12,200 (30%), and Food Delivery ₹98,400 (26%). Your food delivery spending alone is equivalent to 13 months of your Netflix subscription."

User: "Can I afford a vacation to Bali?"
→ System calculates: Current surplus = ₹16,600/month, estimated Bali trip = ₹1,20,000
→ LLM responds: "At your current savings rate, you'd need about 7.2 months to save for a ₹1,20,000 Bali trip without touching your emergency fund. However, if you temporarily reduce dining out by 40% (saving ₹4,480/month), you could fund it in 5.7 months."

---

### 4.7 Insurance Gap Planner

#### What It Does
Analyzes the user's financial profile (income, dependents, liabilities, existing premiums detected in the statement) to identify insurance coverage gaps and recommend adequate protection — **without selling any specific product**.

#### Analysis Framework

**A. Life Insurance Gap Analysis**

Method: Human Life Value (HLV) — The amount of money your dependents would need if you were no longer earning.

```
Recommended Life Cover = 
    (Annual Income × Remaining Working Years Multiplier)
  + Total Outstanding Liabilities (Home Loan + Car Loan + Personal Loans)
  + Future Obligations (Children's Education + Wedding)
  - Existing Life Cover (detected from statement premium payments)
  - Liquid Assets (estimated from savings patterns)

Multiplier ranges:
  Age 25-30: 15-20x annual income
  Age 30-40: 12-15x annual income
  Age 40-50: 8-12x annual income
  Age 50+:   5-8x annual income
```

**Detection from Statement**:
- Search for debits to known insurance companies (LIC, HDFC Life, ICICI Pru, Max Life, etc.)
- Estimate existing cover from premium amount using industry average premium-to-cover ratios
- Flag if user has only ULIP/Endowment (investment-linked) policies vs pure Term Insurance

**Output Example**:
```
┌─────────────────────────────────────────────────────────────────┐
│ LIFE INSURANCE GAP ANALYSIS                                     │
├─────────────────────────────────────────────────────────────────┤
│ Your Annual Income:              ₹10,20,000                     │
│ Recommended Cover (12x):         ₹1,22,40,000                  │
│ Outstanding Home Loan:           ₹54,00,000                     │
│ Total Recommended:               ₹1,76,40,000                  │
│                                                                 │
│ Detected Existing Cover:                                        │
│   - LIC Endowment (₹2,400/quarter → est. ₹5,00,000 cover)    │
│   - HDFC Life Term (₹850/month → est. ₹1,00,00,000 cover)     │
│   Total Existing:                ₹1,05,00,000                   │
│                                                                 │
│ ⚠️  COVERAGE GAP:                ₹71,40,000                    │
│                                                                 │
│ Recommendation: Consider an additional Term Insurance policy    │
│ of ₹75,00,000. Estimated premium: ₹8,000-12,000/year for a    │
│ 30-year-old non-smoker.                                         │
│                                                                 │
│ ⚠️  Your LIC Endowment gives very low cover (₹5L) for the     │
│ premium paid (₹9,600/year). A pure Term Plan would give         │
│ ₹1 Cr cover for similar premium. Consider if this policy        │
│ is serving your protection needs.                               │
└─────────────────────────────────────────────────────────────────┘
```

**B. Health Insurance Gap Analysis**

```
Recommended Health Cover:
  - Metro city (Mumbai, Delhi, Bangalore): ₹15-25 Lakhs minimum
  - Tier-2 city: ₹10-15 Lakhs minimum
  - Family floater if married with dependents
  - Super Top-up for cost-effective additional cover

Detection from Statement:
  - Search for health insurance premium debits
  - Sum up out-of-pocket medical expenses (pharmacy, hospital, lab tests)
  - If medical OOP > ₹50,000/year AND no health insurance premium found → Critical Gap
```

**C. Vehicle Insurance**
- Detect vehicle loan EMIs → infer vehicle ownership
- Check for vehicle insurance premium debits
- Flag if comprehensive insurance premium not detected (especially for financed vehicles)

**D. Output: Insurance Scorecard**

```
Insurance Coverage Score: 45/100 — NEEDS ATTENTION

✅ Life Insurance:    Partially Covered (Gap: ₹71.4L)
❌ Health Insurance:  NOT DETECTED — Critical Gap
✅ Vehicle Insurance: Active (renewal due ~March based on last payment)
❌ Home Insurance:    NOT DETECTED (you have a home loan — this is important)
```

---

### 4.8 Goal Planner & Simulator

#### What It Does
Lets users define financial goals and simulates pathways to achieve them, based on their actual income, expenses, and savings capacity extracted from the statement.

#### Goal Types

**1. Emergency Fund**
```
Target:         6 × Monthly Essential Expenses
Current:        Estimated from savings pattern analysis
Monthly Contribution: Calculated from current surplus
Time to Target: Target ÷ Monthly Contribution
```

**2. Savings Goal (Generic)**
User inputs: Target Amount + Target Date
```
Required Monthly Savings = Target Amount ÷ Months Until Target Date

If Required > Available Surplus:
  → Show budget adjustments needed
  → "Reduce dining out by 30% (saves ₹3,360) + cancel 2 subscriptions (saves ₹268)
     = ₹3,628 additional monthly savings → goal achievable by [new date]"
```

**3. Debt Payoff Planner**
Detects all active loans/EMIs from recurring charges and offers two strategies:

- **Avalanche Method**: Pay minimums on all debts, throw extra money at highest interest rate first
  - Mathematically optimal, saves the most on interest
- **Snowball Method**: Pay minimums on all debts, throw extra money at smallest balance first
  - Psychologically motivating (quick wins)

```
Example Output:
┌──────────────────────────────────────────────────────────┐
│ DEBT PAYOFF SIMULATION                                   │
├──────────────────────────────────────────────────────────┤
│ Active Debts Detected:                                   │
│   1. Home Loan:  ₹54,00,000 remaining @ 8.5% (18 yrs)  │
│   2. Car Loan:   ₹3,80,000 remaining @ 9.2% (2 yrs)    │
│   3. Credit Card: ₹45,000 revolving @ 42% APR           │
│                                                          │
│ ⚠️  ALERT: Credit card revolving balance detected at     │
│ 42% APR. This is the most expensive debt possible.       │
│                                                          │
│ If you redirect ₹5,000/month from discretionary:         │
│   Avalanche: Pay off CC in 10 months, save ₹18,400      │
│   Snowball:  Pay off CC in 10 months (same, smallest)    │
│                                                          │
│ After CC cleared, redirect ₹5,000 + ₹2,000 (CC min)     │
│ toward car loan: Finish 8 months early, save ₹14,720    │
└──────────────────────────────────────────────────────────┘
```

**4. What-If Scenario Simulator**
An interactive engine where users can adjust spending sliders and see real-time impact:

```
Scenario: "What if I reduce dining out by 50%?"

Current Dining Out:  ₹11,200/month
Reduced to:          ₹5,600/month
Monthly Savings Gain: +₹5,600

Impact:
  → Emergency fund target reached 4.2 months sooner
  → Bali vacation fully funded by August instead of November
  → Annual savings increase: ₹67,200
  → New savings rate: 26.1% (up from 19.5%)
```

**5. Retirement / Long-Term Wealth Projection**
```
Inputs (from statement + user input):
  - Current age, target retirement age
  - Current monthly savings (detected)
  - Current investments (estimated from SIP debits)
  - Expected returns (conservative 8%, moderate 12%, aggressive 15%)
  - Expected inflation (6%)

Calculation: Future Value with monthly compounding
  FV = P × [((1 + r)^n - 1) / r]
  where P = monthly investment, r = monthly return rate, n = months

Output:
  "At your current SIP of ₹10,000/month with 12% expected returns,
   you'll have approximately ₹3.5 Cr by age 60.
   Adjusted for 6% inflation, that's worth ₹87 Lakhs in today's money.
   To maintain your current lifestyle (₹68,400/month) for 25 years
   post-retirement, you'd need ₹2.1 Cr (inflation-adjusted).
   ✅ You're on track, but increasing SIP by ₹5,000 adds ₹1.7 Cr."
```

---

### 4.9 Tax Deduction Finder

#### What It Does
Scans transactions to identify expenses that may qualify for tax deductions or credits, helping users maximize their tax efficiency.

#### Detectable Deductions

**India (Section-wise)**:

| Section | What It Covers | How We Detect It |
|---------|---------------|-------------------|
| **80C** (₹1.5L limit) | Life insurance, PPF, ELSS, tuition fees, home loan principal | Insurance premium debits, SIP to ELSS funds, tuition fee payments |
| **80D** (₹25K-₹1L) | Health insurance premiums, preventive health checkups | Health insurance company debits |
| **80E** | Education loan interest | Education loan EMI debits |
| **24(b)** (₹2L limit) | Home loan interest | Home loan EMI detected → estimate interest component |
| **80G** | Charitable donations | Donations to recognized NGOs/charities |
| **80TTA** (₹10K) | Savings account interest | Interest credits in statement |

**US (Common Deductions)**:

| Deduction | How We Detect It |
|-----------|-------------------|
| **401(k) / IRA contributions** | Retirement account debits |
| **HSA contributions** | HSA account transfers |
| **Mortgage interest** | Mortgage payment debits |
| **Charitable donations** | Payments to registered nonprofits |
| **Medical expenses (>7.5% AGI)** | Sum of medical/pharmacy transactions |
| **Student loan interest** | Student loan payment debits |

#### Output
```
TAX OPTIMIZATION SUMMARY (FY 2025-26)

Section 80C: ₹1,12,000 utilized out of ₹1,50,000 limit
  ✅ LIC Premium:     ₹9,600
  ✅ ELSS SIP:         ₹60,000
  ✅ PPF:              ₹42,400
  💡 Gap: ₹38,000 — Consider investing before March 31 to save ₹11,400 in tax

Section 80D: ₹0 utilized out of ₹25,000 limit
  ❌ No health insurance premium detected
  💡 You spent ₹34,200 on out-of-pocket medical expenses
  💡 A health insurance policy would give you tax savings + financial protection

Section 24(b): ₹1,87,000 utilized (estimated from EMI)
  ✅ Home loan interest component: ₹1,87,000

POTENTIAL ADDITIONAL TAX SAVINGS: ₹22,800
```

---

### 4.10 Report Generator

#### What It Does
Generates a comprehensive, downloadable PDF report summarizing the user's complete financial health analysis — suitable for sharing with a financial advisor or for personal records.

#### Report Sections
1. **Executive Summary** — One-page financial health overview with score
2. **Income Analysis** — Sources, stability, growth trends
3. **Expense Analysis** — Category-wise breakdown, top merchants, trends
4. **Recurring Obligations** — Complete list of subscriptions, EMIs, and recurring charges
5. **Savings & Investment Review** — Savings rate, investment allocation
6. **Insurance Coverage Status** — Gap analysis with recommendations
7. **Goal Progress** — Status of each defined goal with projections
8. **Tax Optimization** — Deduction utilization and opportunities
9. **AI Recommendations** — Top 10 actionable suggestions ranked by impact
10. **Monthly Detail Appendix** — Full month-by-month breakdown tables

---

## 5. Data Models & Database Schema

```sql
-- Core Tables

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(100),
    country         VARCHAR(2) DEFAULT 'IN',    -- ISO country code
    currency        VARCHAR(3) DEFAULT 'INR',   -- ISO currency code
    age             INTEGER,
    dependents      INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE statements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    filename        VARCHAR(255) NOT NULL,
    file_hash       VARCHAR(64) NOT NULL,       -- SHA-256 for dedup
    file_type       VARCHAR(10) NOT NULL,        -- pdf, csv, xlsx
    bank_name       VARCHAR(100),
    account_type    VARCHAR(20),                 -- savings, current, credit_card
    statement_from  DATE,
    statement_to    DATE,
    total_rows      INTEGER,
    parsed_rows     INTEGER,
    parse_status    VARCHAR(20) DEFAULT 'pending', -- pending, processing, done, failed
    uploaded_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id    UUID REFERENCES statements(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    narration       TEXT NOT NULL,               -- Original raw narration
    clean_merchant  VARCHAR(200),                -- Cleaned merchant name
    debit           DECIMAL(15,2),
    credit          DECIMAL(15,2),
    balance         DECIMAL(15,2),
    mode            VARCHAR(20),                 -- UPI, NEFT, IMPS, POS, ATM, etc.
    category        VARCHAR(50),
    sub_category    VARCHAR(50),
    category_source VARCHAR(10) DEFAULT 'auto',  -- auto, llm, user
    is_recurring    BOOLEAN DEFAULT FALSE,
    recurring_id    UUID REFERENCES recurring_charges(id),
    tags            TEXT[],                       -- User-defined tags
    source_page     INTEGER,
    source_row      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recurring_charges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    merchant        VARCHAR(200) NOT NULL,
    average_amount  DECIMAL(15,2),
    frequency       VARCHAR(20),                 -- weekly, monthly, quarterly, annual
    category        VARCHAR(50),
    sub_category    VARCHAR(50),
    first_seen      DATE,
    last_seen       DATE,
    occurrence_count INTEGER,
    is_active       BOOLEAN DEFAULT TRUE,
    status          VARCHAR(30),                 -- active, zombie, price_increased, cancelled
    annual_cost     DECIMAL(15,2),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE monthly_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    month           DATE NOT NULL,               -- First day of month
    total_income    DECIMAL(15,2),
    total_expenses  DECIMAL(15,2),
    net_savings     DECIMAL(15,2),
    savings_rate    DECIMAL(5,2),                -- Percentage
    fixed_expenses  DECIMAL(15,2),
    variable_essentials DECIMAL(15,2),
    discretionary   DECIMAL(15,2),
    investments     DECIMAL(15,2),
    transfers       DECIMAL(15,2),
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, month)
);

CREATE TABLE goals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    goal_type       VARCHAR(30),                 -- emergency_fund, savings, debt_payoff, retirement
    target_amount   DECIMAL(15,2),
    current_amount  DECIMAL(15,2) DEFAULT 0,
    target_date     DATE,
    monthly_required DECIMAL(15,2),
    priority        INTEGER DEFAULT 1,
    status          VARCHAR(20) DEFAULT 'active', -- active, achieved, paused, abandoned
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE insurance_analysis (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    insurance_type  VARCHAR(30),                 -- life, health, vehicle, home
    detected_premium DECIMAL(15,2),
    detected_provider VARCHAR(100),
    estimated_cover DECIMAL(15,2),
    recommended_cover DECIMAL(15,2),
    gap_amount      DECIMAL(15,2),
    gap_severity    VARCHAR(20),                 -- none, low, medium, high, critical
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE category_corrections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    transaction_id  UUID REFERENCES transactions(id),
    original_category VARCHAR(50),
    corrected_category VARCHAR(50),
    original_sub    VARCHAR(50),
    corrected_sub   VARCHAR(50),
    merchant_pattern VARCHAR(200),               -- To learn from this correction
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE insights (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    insight_type    VARCHAR(30),                  -- expense_spike, subscription_zombie, etc.
    title           VARCHAR(200),
    description     TEXT,
    severity        VARCHAR(10),                  -- info, warning, critical, positive
    potential_savings DECIMAL(15,2),
    is_read         BOOLEAN DEFAULT FALSE,
    is_dismissed    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_category ON transactions(user_id, category);
CREATE INDEX idx_transactions_merchant ON transactions(clean_merchant);
CREATE INDEX idx_recurring_user ON recurring_charges(user_id);
CREATE INDEX idx_monthly_user ON monthly_summaries(user_id, month);
```

---

## 6. AI/ML Pipeline Details

### 6.1 LLM Usage Points

The LLM is used at exactly 4 points in the system. Everywhere else, computation is deterministic Python.

| # | Use Case | Input | Output | Model |
|---|----------|-------|--------|-------|
| 1 | **Transaction Classification** | Raw narration + amount + mode | `{category, sub_category, confidence}` | Gemini Flash (fast, cheap) |
| 2 | **Merchant Name Cleaning** | Raw narration | Clean merchant name string | Gemini Flash |
| 3 | **Insight Narration** | Pre-computed metrics JSON | Human-readable insight paragraph | Gemini Flash / Pro |
| 4 | **Conversational Chat** | User question + financial context JSON | Natural language answer | Gemini Pro |

### 6.2 Prompt Engineering Strategy

**For Classification (Tier 2 Fallback)**:
```
System: You are a financial transaction classifier for Indian bank statements.
Classify the following transaction into the provided taxonomy.
Rules:
- UPI payments to food merchants = Discretionary > Food Delivery/Dining
- EMI payments = Fixed Expenses > Loan EMIs
- Insurance company payments = Fixed Expenses > Insurance Premiums
- Transfers to self/own accounts = Transfers > Self-Transfer
- When uncertain, classify as "Discretionary > Miscellaneous"
Respond ONLY in JSON format: {"category": "...", "sub_category": "...", "confidence": 0.0-1.0}

User: Narration: "UPI/P2M/428192/PhonePe/FRESHTOHO/freshtoho@ybl"
      Amount: ₹892 (Debit)
      Mode: UPI
```

**For Insight Generation**:
```
System: You are a friendly, knowledgeable personal finance advisor.
You're reviewing a user's financial data and generating helpful insights.
Rules:
- Be specific with numbers (never round excessively)
- Always frame suggestions positively (what they CAN do, not what they did wrong)
- Include the exact monetary impact of each suggestion
- Never recommend specific financial products or brands
- Use simple language, avoid jargon

Context: {pre_computed_financial_summary_json}

Generate 3-5 actionable insights for this user, ordered by potential financial impact.
```

### 6.3 Embedding & Similarity Search

For merchant matching (mapping unknown merchants to known categories):
1. Pre-compute embeddings for all known merchant names in the rule database
2. When a new unknown merchant appears, compute its embedding
3. Find the nearest known merchant using cosine similarity
4. If similarity > 0.85, auto-assign the same category
5. If similarity 0.65-0.85, suggest the category but flag for review
6. If similarity < 0.65, fall back to full LLM classification

Storage: `pgvector` extension in PostgreSQL for efficient vector similarity search.

---

## 7. Technology Stack

### Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Web Framework** | FastAPI (Python 3.11+) | Async-native, auto-generated OpenAPI docs, excellent for data-heavy APIs |
| **Data Processing** | Pandas / Polars | Polars for speed on large statements, Pandas for complex aggregations |
| **PDF Parsing** | pdfplumber | Best open-source library for extracting tables from text-based PDFs |
| **OCR** | pytesseract + Pillow | Fallback for scanned/image-based PDFs |
| **PDF Password** | pikepdf | Handle password-protected bank statements |
| **LLM Integration** | Google Generative AI SDK / LangChain | Structured output, function calling, cost-effective Gemini Flash |
| **Task Queue** | Celery + Redis | Background processing of statement uploads (parsing takes 30-90 sec) |
| **Database** | PostgreSQL 16 | ACID compliance for financial data, pgvector for embeddings |
| **Vector Search** | pgvector | Semantic merchant matching without a separate vector DB |
| **Caching** | Redis | Session data, computed dashboard metrics, rate limiting |
| **PDF Generation** | WeasyPrint / ReportLab | Financial health report export |
| **Auth** | JWT + bcrypt | Stateless authentication, secure password hashing |

### Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Framework** | Next.js 14+ (App Router) | SSR for SEO, React Server Components for performance |
| **Styling** | Tailwind CSS | Rapid prototyping, consistent design system |
| **Charts** | Recharts / Tremor | React-native charting, financial dashboard components |
| **File Upload** | react-dropzone | Drag-and-drop with file type validation |
| **State Management** | Zustand | Lightweight, sufficient for this app's complexity |
| **Chat UI** | Custom + AI SDK (Vercel) | Streaming chat responses for the copilot |
| **Icons** | Lucide React | Clean, consistent icon set |
| **Tables** | TanStack Table | Sortable, filterable transaction tables |

### Infrastructure

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Hosting (Backend)** | Railway / Render / AWS ECS | Easy Python deployment with background workers |
| **Hosting (Frontend)** | Vercel | Optimal for Next.js, global CDN |
| **Database Hosting** | Supabase / Neon | Managed Postgres with pgvector, generous free tiers |
| **File Storage** | AWS S3 / Supabase Storage | Temporary statement storage (deleted after processing) |
| **Monitoring** | Sentry + Posthog | Error tracking + product analytics |

---

## 8. API Design

### Endpoints

```
AUTH
  POST   /api/auth/register          — Create account
  POST   /api/auth/login              — Login, receive JWT
  POST   /api/auth/refresh            — Refresh access token
  GET    /api/auth/me                 — Get current user profile
  PUT    /api/auth/me                 — Update profile (age, dependents, etc.)

STATEMENTS
  POST   /api/statements/upload       — Upload statement file (multipart)
  GET    /api/statements              — List all uploaded statements
  GET    /api/statements/:id          — Get statement details & parse status
  DELETE /api/statements/:id          — Delete statement and its transactions

TRANSACTIONS
  GET    /api/transactions            — List transactions (paginated, filterable)
           ?month=2025-03
           &category=Discretionary
           &merchant=Zomato
           &min_amount=500
           &max_amount=5000
  PUT    /api/transactions/:id        — Update category (user correction)
  GET    /api/transactions/search     — Full-text search in narrations

ANALYTICS
  GET    /api/analytics/summary       — Overall financial summary
  GET    /api/analytics/monthly       — Month-by-month breakdown
  GET    /api/analytics/categories    — Category-wise spending breakdown
  GET    /api/analytics/merchants     — Top merchants by spend
  GET    /api/analytics/trends        — Trend analysis (MoM changes)
  GET    /api/analytics/score         — Financial health score

RECURRING
  GET    /api/recurring               — All detected recurring charges
  PUT    /api/recurring/:id           — Mark as active/zombie/cancelled
  GET    /api/recurring/summary       — Total recurring obligation summary

GOALS
  POST   /api/goals                   — Create a new financial goal
  GET    /api/goals                   — List all goals
  PUT    /api/goals/:id               — Update goal
  DELETE /api/goals/:id               — Delete goal
  GET    /api/goals/:id/simulate      — Run what-if simulation
           ?reduce_dining=30
           &cancel_subscriptions=spotify,youtube

INSURANCE
  GET    /api/insurance/analysis      — Full insurance gap analysis
  PUT    /api/insurance/inputs        — User provides additional inputs
           (age, dependents, existing cover details)

INSIGHTS
  GET    /api/insights                — Get all generated insights
  PUT    /api/insights/:id/dismiss    — Dismiss an insight
  GET    /api/insights/suggestions    — Get savings suggestions

COPILOT
  POST   /api/copilot/chat            — Send message to AI copilot (streaming)
  GET    /api/copilot/history         — Chat history

REPORTS
  POST   /api/reports/generate        — Generate PDF report (async)
  GET    /api/reports/:id/download    — Download generated report

TAX
  GET    /api/tax/deductions          — Detected tax deduction opportunities
```

---

## 9. Security & Privacy Architecture

### Principles

1. **Statement files are ephemeral**: Raw PDF/CSV files are deleted from storage within 1 hour of successful parsing. Only structured transaction data is retained.
2. **PII is masked before LLM calls**: Account numbers, names, and addresses are stripped before any data is sent to external AI APIs.
3. **All financial data is encrypted at rest**: AES-256 encryption on the database level.
4. **No third-party bank credential sharing**: We never ask for bank login credentials. Upload-only model.
5. **User data isolation**: Row-level security in PostgreSQL ensures users can only access their own data.
6. **Right to deletion**: Users can delete all their data with a single action. This triggers cascading deletion across all tables.

### PII Masking Pipeline

Before any transaction narration is sent to an external LLM:
```python
import re

def mask_pii(narration: str) -> str:
    # Mask account numbers (10+ digit sequences)
    narration = re.sub(r'\b\d{10,}\b', '[ACCOUNT]', narration)
    # Mask PAN numbers (Indian tax ID)
    narration = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN]', narration)
    # Mask Aadhaar numbers (Indian national ID)
    narration = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[AADHAAR]', narration)
    # Mask email addresses
    narration = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', narration)
    # Mask phone numbers
    narration = re.sub(r'\b(\+91|0)?[6-9]\d{9}\b', '[PHONE]', narration)
    return narration
```

### Authentication & Authorization
- JWT-based stateless authentication
- Access tokens: 15-minute expiry
- Refresh tokens: 7-day expiry, stored in HTTP-only secure cookies
- Rate limiting: 100 requests/minute per user, 10 statement uploads/day
- CORS configured for frontend origin only

---

## 10. UI/UX Design Guidelines

### Design Principles
1. **Numbers front and center**: The most important metric should be visible within 2 seconds of page load
2. **Progressive disclosure**: Show summary first, details on click/tap
3. **Color coding**: Green = positive (income, savings), Red = negative (overspending, gaps), Amber = caution
4. **Mobile-first**: 60%+ of users will check finances on their phone
5. **Dark mode default**: Finance apps are often checked at night

### Key Screens

**Screen 1: Upload Page**
- Drag-and-drop zone (large, centered, friendly illustration)
- Supported formats listed (PDF, CSV, Excel)
- Upload progress bar
- Processing status with animated steps ("Parsing... Categorizing... Analyzing...")

**Screen 2: Dashboard (Home)**
- Financial Health Score (large circular gauge, top-center)
- Income vs Expenses bar chart (12-month)
- Quick stats row: Monthly Income | Monthly Expenses | Savings Rate | Active Subscriptions
- Top 3 Insight cards (dismissible)
- Category donut chart
- "Ask FIN anything" chat input pinned to bottom

**Screen 3: Transactions**
- Searchable, sortable, filterable table
- Each row: Date | Merchant | Category (editable) | Amount | Mode
- Filters: Month, Category, Amount Range, Merchant
- Bulk category correction (select multiple → reassign)

**Screen 4: Recurring & Subscriptions**
- Card view of all recurring charges
- Each card: Logo (if available) | Name | Amount | Frequency | Annual Cost
- "Zombie" badge on suspected unused subscriptions
- "Price Increase" badge with before/after amounts
- Total monthly and annual recurring obligation at the top

**Screen 5: Goals**
- Card per goal with progress bar
- "Add Goal" button (wizard-style form)
- What-if simulator: Spending adjustment sliders with real-time recalculation
- Debt payoff tab with Avalanche vs Snowball comparison

**Screen 6: Insurance**
- Coverage meter for each insurance type (life, health, vehicle, home)
- Gap amounts in large red text where gaps exist
- Recommendations in plain language (not product pitches)

**Screen 7: AI Copilot**
- Full-page chat interface
- Suggested questions: "Where is my money going?", "How can I save more?", "Can I afford a new car?"
- Source citations: Each AI response links to the specific transactions or metrics it references

**Screen 8: Reports**
- Preview of report sections
- "Generate Full Report" button
- Download as PDF

---

## 11. Implementation Roadmap (Phased)

### Phase 1: Core Foundation (Weeks 1-3)
**Goal**: Users can upload a statement and see categorized transactions

| Task | Details | Priority |
|------|---------|----------|
| Project scaffolding | FastAPI backend + Next.js frontend + PostgreSQL | P0 |
| Database schema | All core tables (users, statements, transactions) | P0 |
| File upload API | Multipart upload with validation | P0 |
| CSV parser | Direct pandas ingestion | P0 |
| PDF parser (text) | pdfplumber-based table extraction | P0 |
| Transaction normalizer | Date/amount/narration standardization | P0 |
| Merchant cleaner | Regex-based narration cleaning | P0 |
| Rule-based categorizer | JSON merchant→category lookup | P0 |
| Basic transaction list UI | Table with sort/filter | P0 |
| Auth (register/login) | JWT-based | P1 |

**Deliverable**: Upload a CSV/PDF → see cleaned, categorized transaction list

### Phase 2: Analytics & Patterns (Weeks 4-5)
**Goal**: Monthly breakdown, recurring detection, dashboard with charts

| Task | Details | Priority |
|------|---------|----------|
| Monthly aggregation engine | Income/expense/savings per month | P0 |
| Savings rate calculator | Net savings ÷ income | P0 |
| Recurring charge detector | Periodicity algorithm | P0 |
| Zombie subscription flagger | Recurring >3 months, possibly unused | P1 |
| Dashboard charts | Bar, donut, line charts | P0 |
| Financial health score | Composite scoring algorithm | P1 |
| Category breakdown view | Interactive donut with drill-down | P0 |

**Deliverable**: Full analytics dashboard with monthly trends and recurring charge detection

### Phase 3: Intelligence Layer (Weeks 6-7)
**Goal**: LLM-based classification fallback, AI suggestor, copilot chat

| Task | Details | Priority |
|------|---------|----------|
| LLM categorizer (Tier 2) | Gemini Flash structured output | P0 |
| User category correction UI | Edit category + feedback storage | P1 |
| Insight generation engine | Pre-compute metrics → LLM narration | P0 |
| Proactive suggestion cards | Top 5 insights on dashboard | P0 |
| Chat copilot backend | Streaming chat with financial context | P1 |
| Chat copilot UI | Full-page chat with suggested questions | P1 |

**Deliverable**: AI-powered insights and conversational copilot

### Phase 4: Planning Engines (Weeks 8-9)
**Goal**: Goal planner, insurance gap analysis, debt payoff simulator

| Task | Details | Priority |
|------|---------|----------|
| Emergency fund calculator | 6× essentials target | P0 |
| Savings goal planner | Target + date → required monthly savings | P0 |
| What-if simulator | Spending adjustment → goal impact | P1 |
| Debt payoff planner | Avalanche + Snowball comparison | P1 |
| Insurance gap analyzer | HLV + health cover detection | P0 |
| Insurance scorecard UI | Coverage meters + gap alerts | P0 |
| Tax deduction finder | Section-wise detection | P2 |

**Deliverable**: Full planning and advisory suite

### Phase 5: Polish & Launch (Week 10)
**Goal**: Report generation, security audit, performance optimization

| Task | Details | Priority |
|------|---------|----------|
| PDF report generator | WeasyPrint full financial report | P1 |
| PII masking audit | Review all LLM call paths | P0 |
| Performance optimization | Caching, query optimization | P1 |
| Error handling & edge cases | Corrupt files, partial parses | P0 |
| Mobile responsiveness | Test all screens on mobile | P1 |
| User testing & feedback | 5-10 beta users | P1 |
| Documentation | API docs, README, deployment guide | P2 |

**Deliverable**: Production-ready, secure, polished application

---

## 12. Testing Strategy

### Unit Tests
- **Parser tests**: Feed known PDF/CSV fixtures → assert correct extraction
- **Categorizer tests**: Known narrations → assert correct category
- **Recurring detector tests**: Synthetic transaction series → assert correct detection
- **Calculation tests**: Known income/expense sets → assert correct metrics
- **Goal simulator tests**: Known inputs → assert correct projections
- **Insurance calculator tests**: Known inputs → assert correct HLV and gaps

### Integration Tests
- Upload flow: File upload → parsing → categorization → DB storage
- Analytics flow: Transactions in DB → correct aggregations via API
- Chat flow: User message → financial context injection → LLM response

### Test Data
Create synthetic bank statements with known properties:
- 12 months of predictable transactions
- Known subscriptions at known frequencies
- Known salary deposits
- Known category distributions
- Edge cases: duplicate headers, merged cells, missing dates

### Quality Metrics
- **Parser accuracy**: % of transactions correctly extracted from test PDFs (target: >95%)
- **Categorization accuracy**: % of transactions correctly categorized (target: >90% auto, >95% after user corrections)
- **Calculation correctness**: All financial calculations match manual spreadsheet verification (target: 100%)

---

## 13. Future Enhancements (V2+)

| Feature | Description | Impact |
|---------|-------------|--------|
| **Multi-account stitching** | Upload statements from savings + credit card + loan accounts → unified view | High |
| **Net worth tracker** | Track assets (FDs, MFs, property) alongside liabilities | High |
| **Bill payment reminders** | Predict upcoming recurring charges → push notifications | Medium |
| **Spending limits & alerts** | Set category-wise monthly budgets, get alerts at 80%/100% | Medium |
| **Family/household mode** | Combine multiple family members' statements | High |
| **WhatsApp/Telegram bot** | Query finances via messaging apps | Medium |
| **Investment portfolio analysis** | Parse demat/MF statements → asset allocation review | High |
| **Credit score estimator** | Estimate creditworthiness from spending/debt patterns | Medium |
| **Peer benchmarking** | Anonymous comparison ("You spend 20% less on dining than similar profiles") | Medium |
| **Open Banking / Account Aggregator** | Live bank feed (with explicit consent) for real-time tracking | High |
| **Voice interface** | "Hey FIN, how much did I spend on food this month?" | Low |
| **Expense forecasting** | ML model to predict next month's expenses by category | Medium |
| **Gamification** | Savings streaks, badges, challenges ("No-Spend Weekend Challenge") | Medium |

---

## 14. Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **PDF parsing fails for a bank format** | High | High | Support CSV as universal fallback. Build template library incrementally. Let users manually map columns. |
| **LLM hallucinates financial numbers** | Critical | Medium | Never let LLM calculate. All math is deterministic Python. LLM only classifies and narrates. |
| **User uploads someone else's statement** | Medium | Low | Terms of service + statement name matching (if available) |
| **Data breach / PII leak** | Critical | Low | Encrypt at rest, mask before LLM calls, ephemeral file storage, annual security audit |
| **High LLM API costs** | Medium | Medium | Use Gemini Flash (cheapest), cache classifications, expand Tier 1 rules to reduce LLM calls |
| **Inaccurate insurance recommendations** | High | Medium | Add disclaimers ("This is an estimate, not financial advice"). Let users input actual cover amounts. |
| **User drops off after one upload** | High | High | Email summary report, monthly "financial pulse" reminder, gamification in V2 |
| **Regulatory compliance** | Medium | Medium | Add prominent disclaimer: "FIN is an informational tool, not a registered financial advisor" |

---

## 15. Project Directory Structure

```
FIN/
├── plan.md                          # This file
├── README.md                        # Project overview & setup instructions
│
├── backend/
│   ├── pyproject.toml               # Python dependencies (poetry/uv)
│   ├── alembic/                     # Database migrations
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Environment configuration
│   │   ├── database.py              # DB connection & session
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── statement.py
│   │   │   ├── transaction.py
│   │   │   ├── recurring.py
│   │   │   ├── goal.py
│   │   │   ├── insurance.py
│   │   │   └── insight.py
│   │   │
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── user.py
│   │   │   ├── statement.py
│   │   │   ├── transaction.py
│   │   │   ├── analytics.py
│   │   │   ├── goal.py
│   │   │   └── insurance.py
│   │   │
│   │   ├── api/                     # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── statements.py
│   │   │   ├── transactions.py
│   │   │   ├── analytics.py
│   │   │   ├── recurring.py
│   │   │   ├── goals.py
│   │   │   ├── insurance.py
│   │   │   ├── insights.py
│   │   │   ├── copilot.py
│   │   │   ├── reports.py
│   │   │   └── tax.py
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── parser/
│   │   │   │   ├── base.py          # Abstract parser interface
│   │   │   │   ├── csv_parser.py
│   │   │   │   ├── pdf_parser.py
│   │   │   │   ├── excel_parser.py
│   │   │   │   ├── ocr_parser.py
│   │   │   │   └── normalizer.py    # Transaction normalization
│   │   │   │
│   │   │   ├── categorizer/
│   │   │   │   ├── rules.py         # Tier 1 rule-based classifier
│   │   │   │   ├── llm_classifier.py # Tier 2 LLM fallback
│   │   │   │   ├── merchant_cleaner.py
│   │   │   │   └── taxonomy.py      # Category definitions
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── monthly.py       # Monthly aggregation
│   │   │   │   ├── trends.py        # Trend calculations
│   │   │   │   ├── scoring.py       # Financial health score
│   │   │   │   └── benchmarks.py    # 50/30/20 comparison
│   │   │   │
│   │   │   ├── recurring/
│   │   │   │   ├── detector.py      # Recurring charge detection algorithm
│   │   │   │   └── analyzer.py      # Zombie, price creep analysis
│   │   │   │
│   │   │   ├── planning/
│   │   │   │   ├── goals.py         # Goal simulation & projection
│   │   │   │   ├── debt.py          # Debt payoff strategies
│   │   │   │   ├── insurance.py     # Insurance gap analysis
│   │   │   │   └── tax.py           # Tax deduction detection
│   │   │   │
│   │   │   ├── intelligence/
│   │   │   │   ├── insights.py      # Automated insight generation
│   │   │   │   ├── copilot.py       # Conversational AI handler
│   │   │   │   └── prompts.py       # LLM prompt templates
│   │   │   │
│   │   │   └── reports/
│   │   │       └── pdf_generator.py # PDF report generation
│   │   │
│   │   ├── utils/
│   │   │   ├── pii_masker.py        # PII redaction
│   │   │   ├── security.py          # Password hashing, JWT
│   │   │   └── file_utils.py        # File handling, hash, cleanup
│   │   │
│   │   └── data/
│   │       ├── merchant_rules.json  # Tier 1 merchant→category mapping
│   │       ├── bank_templates.json  # Bank-specific column mappings
│   │       └── insurance_benchmarks.json
│   │
│   └── tests/
│       ├── fixtures/                # Sample PDFs, CSVs for testing
│       ├── test_parser.py
│       ├── test_categorizer.py
│       ├── test_analytics.py
│       ├── test_recurring.py
│       ├── test_goals.py
│       └── test_insurance.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   │
│   ├── public/
│   │   └── illustrations/          # Empty state illustrations
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (dark mode, fonts)
│   │   │   ├── page.tsx             # Landing / Upload page
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx         # Main dashboard
│   │   │   ├── transactions/
│   │   │   │   └── page.tsx         # Transaction list
│   │   │   ├── recurring/
│   │   │   │   └── page.tsx         # Subscriptions & recurring
│   │   │   ├── goals/
│   │   │   │   └── page.tsx         # Goal planner
│   │   │   ├── insurance/
│   │   │   │   └── page.tsx         # Insurance analysis
│   │   │   ├── copilot/
│   │   │   │   └── page.tsx         # AI chat
│   │   │   └── reports/
│   │   │       └── page.tsx         # Report generation
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                  # Generic UI components
│   │   │   ├── charts/              # Chart components
│   │   │   ├── upload/              # File upload components
│   │   │   ├── dashboard/           # Dashboard widgets
│   │   │   ├── transactions/        # Transaction table components
│   │   │   └── planning/            # Goal & insurance components
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts               # API client
│   │   │   ├── auth.ts              # Auth utilities
│   │   │   └── utils.ts             # Formatting, helpers
│   │   │
│   │   ├── stores/
│   │   │   └── useStore.ts          # Zustand global store
│   │   │
│   │   └── types/
│   │       └── index.ts             # TypeScript type definitions
│   │
│   └── tests/
│
├── docker-compose.yml               # Local dev environment
├── .env.example                     # Environment variables template
└── .gitignore
```

---

## Summary

FIN transforms a simple bank statement upload into a comprehensive financial intelligence platform. The architecture enforces a strict separation between **deterministic calculations** (Python) and **generative intelligence** (LLM), ensuring financial accuracy while delivering human-quality explanations and advice.

The 10-week phased roadmap prioritizes a working MVP (upload → categorize → dashboard) by week 3, with intelligence and planning features layered on top. Each phase delivers a functional, testable product increment.

**Key differentiators over existing tools**:
1. No bank credential sharing — upload-only privacy model
2. 12 months of historical analysis from a single file
3. Forward-looking advisory (insurance gaps, goal simulation, tax optimization) — not just backward-looking expense tracking
4. Conversational AI copilot grounded in real numbers
5. Financial health score that quantifies overall wellness

---

*This document is the single source of truth for the FIN project. Update it as decisions are made and implementation progresses.*
