# finMan - Development Journal

This journal tracks all architectural decisions, milestones, experiments, and implementation steps taken during the development of FIN.

---


### Entry 1: Project Scoping & Core Blueprint
- **User Prompt**: Conceived the idea of a Personal Financial Assistant (PFA) that analyzes uploaded bank statements, categorizes spending, tracks recurring/consumption patterns, suggests optimizations, and includes goal and insurance planners.
- **Actions Taken**:
  - Validated the product concept against real-world PFM pain points (manual tracking fatigue vs. privacy concerns with live bank linking).
  - Established the fundamental design rule: **Deterministic Python (`pandas`/`polars`) for all financial arithmetic**, and **LLMs strictly for narration classification and conversational reasoning**.
  - Generated the initial architectural specification in `personal_financial_assistant_blueprint.md`.

### Entry 2: Comprehensive Specification (`plan.md`)
- **Actions Taken**:
  - Expanded the technical plan to ~800 lines in `plan.md`.
  - Documented:
    - 50+ sub-category financial taxonomy.
    - Deterministic recurring charge detection algorithm with tolerance windows.
    - Insurance gap formulas (Human Life Value - HLV method & health vulnerability metrics).
    - Debt payoff strategies (Avalanche vs. Snowball).
    - Tax deduction opportunities (Sections 80C, 80D, 24(b)).
    - 8-table relational database schema with indexes.
    - 4 specific LLM integration points with structured JSON output contracts.

### Entry 3: Real Statement Analysis & Ground-Truth Discovery
- **User Context**: Clarified that this prototype is targeted for an exhibition, and provided their own bank statements (6 months of SBI e-statements: `dec.pdf` to `may.pdf`, plus a `PhonePe_Transaction_Statement.csv`).
- **Actions Taken**:
  - Inspected the uploaded statements and identified two distinct bank PDF formats:
    1. Table-based SBI YONO app exports (`dec.pdf` through `april.pdf`).
    2. Text stream-based SBI NetBanking exports (`may till 17.pdf`).
  - Built `backend/app/services/parser/universal_parser.py` supporting both PDF structures and CSV inputs.
  - Extracted **561 real transactions** into `parsed_real_transactions.csv`.
  - Built `backend/app/services/categorizer/rules.py` and benchmarked it against the 561 transactions:
    - Confirmed that **77% (434 transactions)** in modern Indian personal banking are daily UPI micro-spends (chai, auto, local vendors, P2P).

### Entry 4: Learning from External Benchmarks (Kaggle & GitHub)
- **Actions Taken**:
  - Researched open datasets for Indian banking and household transactions.
  - Downloaded and analyzed:
    - `Daily_Household_Transactions.csv` (2,461 rows covering maid wages, milk, groceries, pharmacy).
    - `kaggle_dataset_1/bank_statements.csv` (985 rows of card, ATM, NEFT transactions).
    - `kaggle_dataset_2/transactions.csv` (1,000 UPI records).
  - Synthesized learned patterns into a unified 12-month master statement for the exhibition persona ("Rohan Sharma", 29, Bangalore):
    - Produced `master_salaried_statement.csv` (758 rows, Nov 2025 – Oct 2026, mathematically consistent running balance).
    - Seeded golden test cases: salary credits, festival bonus, car loan EMI, rent, duplicate audio subscriptions (Spotify + YouTube), price creep (Netflix +30%), zombie subscription (Cult.Fit gym), underinsured LIC endowment, and out-of-pocket medical expenses.

### Entry 5: Core Analytics Engine
- **Actions Taken**:
  - Implemented `backend/app/services/analytics/engine.py` with pure deterministic math:
    - `calculate_monthly_metrics`: Inflow, outflow, net savings, savings rate.
    - `detect_recurring_charges`: Duplicate audio subscriptions, price jumps, zombie candidate detection.
    - `analyze_insurance_gaps`: HLV life cover shortfall calculation and health insurance absence risk.
    - `simulate_goal_timeline`: Dynamic acceleration calculator based on discretionary spend adjustments.
    - `calculate_financial_health_score`: Composite 0–100 health scoring.

### Entry 6: Full-Stack Integration (FastAPI + Next.js)
- **User Decision**: Chose a modern Next.js frontend integrated with Python rather than a basic Streamlit script.
- **Actions Taken**:
  - Implemented the FastAPI service in `backend/main.py`:
    - Endpoints: `/api/overview`, `/api/subscriptions`, `/api/insurance`, `/api/simulate-goal`, `/api/transactions`, `/api/upload`, `/api/reset-demo`.
    - Enabled CORS for frontend communication.
  - Bootstrapped a Next.js 16 + Tailwind CSS app in `frontend/`.
  - Installed `lucide-react` and `recharts`.
  - Implemented the fintech dashboard UI in `frontend/src/app/page.tsx`:
    - Top KPI cards (Health Score 48/100, Inflow ₹13.10L, Outflow ₹12.28L, Savings Rate 6.3%, Balance ₹2.50L).
    - 12-month cash flow bar chart (income vs. burn rate).
    - Spending allocation donut chart.
    - Subscription audit cards (duplicate detection, price creep, zombie membership).
    - Insurance gap meter (₹1.53 Crore life cover shortfall, zero health cover warning).
    - Interactive "What-If" goal simulator with live sliders.
    - File upload dropzone and reset button.
  - Started both servers in background tasks:
    - FastAPI backend live on port `8000`.
    - Next.js frontend live on port `3000`.

### Entry 7: UI Guidelines & Design System Overhaul
- **User Feedback**: Noted the initial UI felt generic and requested a custom design system with vibrant colors, stronger typography, and clear guidelines.
- **Actions Taken**:
  - Authored [`UI_guidelines.md`](file:///Users/raghava/Desktop/FIN/UI_guidelines.md) defining the "Electric Fintech" design philosophy:
    - **Typography**: `Plus Jakarta Sans` for geometric display headings and `JetBrains Mono` for tabular financial figures.
    - **Color Tokens**: Obsidian Canvas (`#07090E`), Electric Emerald (`#10E599` for inflow), Cyber Cyan (`#00D2FF` for burn), Vivid Coral (`#FF3B69` for critical gaps), Warm Amber (`#FFB800` for creep/traps).
  - Configured custom font variables and backdrop grid in `frontend/src/app/layout.tsx` and `frontend/src/app/globals.css`.
  - Redesigned `frontend/src/app/page.tsx`:
    - Replaced static metric boxes with high-contrast KPI cards featuring glow borders (`glow-coral`, `glow-cyan`, `glow-amber`).
    - Added tabular mono styling for monetary values.
    - Updated Recharts with dual-tone gradients.
    - Highlighted subscription traps and insurance shortfalls with distinct visual treatment.
    - Re-built and verified the Next.js production build and dev server.

### Entry 8: Donut Breakdown Granularity Fix
- **User Feedback**: Questioned why the spending breakdown donut chart only displayed 4 generic macro categories.
- **Root Cause**: The UI was grouping expenses into high-level buckets (`Fixed Expenses`, `Discretionary`, `Investments`, `Daily Micro-Spends`) and slicing the top 4 in the legend.
- **Actions Taken**:
  - Enhanced `backend/main.py` `/api/overview` endpoint to return granular `subcategory_breakdown` (Rent, Loan EMIs, Food Delivery & Dining, Mutual Funds, Fuel & Commute, Healthcare, Domestic Help, Utilities).
  - Updated `frontend/src/app/page.tsx` with a **Granular vs. Macro** toggle switch.
  - Enabled detailed legend visualization displaying all real expense categories.
  - Hot-reloaded FastAPI backend and Next.js frontend.

### Entry 9: Multi-Tab Architecture & Monthly Spend Drilldown
- **User Prompt**: Clarified that statements should not be treated as a single-page upload, but as a structured profile with distinct tabs:
  1. **Overview Dashboard**: High-level financial KPIs, health score, insurance gap, and goal simulator.
  2. **Monthly Spend Drilldown**: Month selector pills with interactive charts (sub-category donut, daily burn rate timeline) and an in-month searchable ledger.
  3. **Statement Vault**: Dedicated management page for uploading new statements, viewing active metadata, and switching datasets.
- **Actions Taken**:
  - Added new backend endpoints in `backend/main.py`:
    - `GET /api/months`: Discovers and returns available months in the active ledger.
    - `GET /api/month-detail/{year_month}`: Calculates inflow, outflow, savings, granular subcategory spending, daily burn trend, and full transaction history for a specific month.
    - `GET /api/statements-list`: Returns active statement filename, row count, date span, and balance.
  - Redesigned `frontend/src/app/page.tsx` with a top tab navigation bar (`Overview`, `Monthly Spend Drilldown`, `Statement Vault`).
  - Implemented the Monthly Spend page:
    - Month selector pills (`2026-10`, `2026-09`, etc.).
    - 4 KPI cards per month (Inflow, Outflow, Net Surplus Added, Transaction Count).
    - Sub-category donut chart with scrollable value breakdown.
    - Daily burn timeline chart showing spending spikes.
    - Searchable transaction ledger table for the selected month.
  - Implemented the Statement Vault page with an upload dropzone and active dataset info card.
  - Verified with `npm run build` and live reload.

### Entry 10: Goal Tracking Lifecycle & Delta Ingestion Architecture
- **User Prompt**: Clarified the goal tracking lifecycle when new statements are uploaded:
  - How transactions are tagged by date vs. upload batch date.
  - Whether goal tracking strictly evaluates transactions occurring **after** the goal creation date.
- **Actions Taken**:
  - Authored [`goal_tracking_architecture.md`](file:///Users/raghava/Desktop/FIN/goal_tracking_architecture.md) documenting the mathematical reconciliation model:
    - **Dual Timestamping**: `transaction_date` (chronological bank date) vs. `created_at` (ingestion timestamp).
    - **Goal Start Date Partition**: Transactions occurring *before* `goal.start_date` serve only as baseline velocity; transactions *on or after* `goal.start_date` calculate actual accumulated surplus.
    - **Discipline Feedback Loop**: Automated comparison of actual category burn (e.g. dining out) against the user's committed spending cap.
    - **Deduplication Engine**: Hash-based deduplication allowing out-of-order statement uploads without corrupting progress metrics.

### Entry 11: Editorial Light Mode Overhaul & Real Empty-State Screen
- **User Feedback**: 
  - Noted that pre-loading demo metrics automatically made no sense if the user hasn't uploaded anything yet.
  - Requested removal of dark mode in favor of a crisp, aesthetic modern light palette.
- **Actions Taken**:
  - Rewrote [`UI_guidelines.md`](file:///Users/raghava/Desktop/FIN/UI_guidelines.md) for the "Editorial Fintech Light" aesthetic (Mercury / Linear aesthetic).
  - Updated `backend/main.py`:
    - Statement state defaults to `CURRENT_FILE_PATH = None`.
    - Added empty state handling (`has_statement: false`), `/api/load-demo`, and `/api/clear-statement`.
  - Updated `frontend/src/app/globals.css`:
    - Canvas switched to clean slate light grid (`#F8FAFC`, `#0F172A` text).
  - Redesigned `frontend/src/app/page.tsx`:
    - **Zero-State Experience**: When no statement is uploaded, renders a clean hero screen with drag-and-drop upload and an optional *"Test with Master Salaried Profile"* button.
    - **Aesthetic Light Palette**: White cards (`#FFFFFF`), borders (`#E2E8F0`), Indigo primary (`#4F46E5`), Emerald inflows (`#10B981`), and Coral outflows (`#EF4444`).
    - Tab navigation (`Overview`, `Monthly Spend Drilldown`, `Statement Vault`) activates once a statement is ingested.
    - Unload / Clear Statement button allows returning to the empty state at any time.

### Entry 12: Production-Grade Full-Width Layout & Typography Overhaul
- **User Feedback**: 
  - Criticized the generic "AI font" (Plus Jakarta / JetBrains Mono combo) and constrained width.
  - Noted elements like the donut breakdown legend were overflowing out of card containers.
- **Actions Taken**:
  - Replaced the typography stack across `layout.tsx` and `globals.css` with **Inter** (`var(--font-inter)`), matching standard modern financial platforms like Stripe and Mercury.
  - Re-engineered the container system from boxed `max-w-7xl` to a clean, edge-to-edge **Full-Width Layout** (`w-full px-8`).
  - Fixed the donut chart card layout:
    - Reduced inner/outer radius to fit card constraints.
    - Added text truncation and two-column compact grid for category labels (`truncate max-w-[120px]`) to eliminate text overflow.
  - Simplified card styling to clean, neutral borders (`border-slate-200`) and standard text weights (`text-slate-900`, `text-slate-500`).
  - Verified compilation with zero build errors.

### Entry 13: Minimalist Topbar & Tab Navigation Clean-up
- **User Feedback**: 
  - Requested removal of the redundant "Personal Finance" badge next to the logo.
  - Criticized the boxed "tab container" look (`bg-slate-100 border p-1 rounded-lg`) for page navigation.
- **Actions Taken**:
  - Cleaned up the header in `frontend/src/app/page.tsx`:
    - Removed the "Personal Finance" pill badge.
    - Replaced the boxed segmented controller with modern **minimalist underline tabs** (`border-b-2 border-slate-900` on active, clean text with no background box).
    - Reduced topbar height to a compact `h-14` with standard spacing.
    - Simplified the "Unload" action to a clean, subtle text button.
  - Tested build with zero compilation errors.

### Entry 14: App Rebrand to "finMan" & Em Dash Scrub
- **User Prompt**: 
  - Change the browser tab title and in-app name to `finMan` (with lowercase `f`).
  - Completely avoid em dashes (`—`) anywhere across the project.
- **Actions Taken**:
  - Updated `frontend/src/app/layout.tsx`: Browser title updated to `title: "finMan"`.
  - Updated `frontend/src/app/page.tsx`: In-app logo mark and text updated to `f` and `finMan`.
  - Ran a project-wide scan across `frontend/src/` and `backend/` to verify zero em dash (`—`) characters exist in code and templates.
  - Verified compilation via `npm run build`.

### Entry 15: Recharts Tooltip Missing Series Label Fix
- **Issue**: Hovering over the Inflow vs. Burn Rate bar chart rendered an empty space before the colon (`: ₹112,087.54`).
- **Root Cause**: Recharts `Tooltip` `formatter` callback was returning `[value, ""]` with an empty string for the series name.
- **Fix**: Updated `formatter` callback to return proper series names `[value, name === "income" ? "Inflow" : name === "expenses" ? "Burn" : name]`. Now renders cleanly as:
  - `Inflow: ₹105,000`
  - `Burn: ₹112,087.54`

### Entry 16: Red Danger Styling on Unload Action
- **User Prompt**: Requested styling the "Unload" statement button in red.
- **Actions Taken**:
  - Updated both the header and Statement Vault unload buttons in `frontend/src/app/page.tsx` with dedicated danger styling:
    - `bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 font-semibold shadow-xs`.
  - Hot-reloaded and verified on the Next.js dev server.

### Entry 17: Uploaded Statement Parsing & Balance Imputation Fix
- **Issue**: User attempted to upload a statement (`working_person_statement.csv`), but encountered a runtime `500 Internal Server Error` (`Failed to fetch`).
- **Root Cause**:
  1. The uploaded CSV statement format (PhonePe/UPI-style) lacked a native bank `Balance` column (`balance: NaN`), which caused `json.dumps()` in FastAPI to crash with `ValueError: Out of range float values are not JSON compliant: nan`.
  2. The dates were formatted as `"Jul 01, 2026"` rather than ISO `YYYY-MM-DD`.
- **Fix**:
  - Enhanced `backend/app/services/parser/universal_parser.py`:
    - Added date parsing with `pd.to_datetime(raw_date, errors='coerce')` converting strings like `"Jul 01, 2026"` into standard `2026-07-01`.
    - Added automated running-balance imputation so statements missing explicit bank balance columns calculate running credit/debit balances starting from a positive baseline.
  - Enhanced `backend/main.py`:
    - Added `.fillna(0.0)` guards across `credit`, `debit`, and `balance` to ensure all numerical outputs are strictly JSON-compliant.
  - Tested end-to-end: verified upload of `working_person_statement.csv` (81 transactions) completes with `200 OK`, transitions cleanly to the dashboard, and can be unloaded back to the empty state without errors.

### Entry 18: Dedicated Goal Simulator Tab
- **User Prompt**: Moved the Goal Planner and Simulator from the bottom of the overview dashboard to its own dedicated tab.
- **Actions Taken**:
  - Updated `frontend/src/app/page.tsx`:
    - Added **Goal Simulator** tab to the top navigation (`Overview`, `Monthly Drilldown`, `Goal Simulator`, `Statement Vault`).
    - Removed the goal simulator card from the Overview page to keep it focused on core analytics (Health Score, Inflow/Outflow, Subscriptions, Insurance Gap).
    - Built out a dedicated Goal Simulator page with target sliders, dining reallocation controls, subscription cancellation checkboxes, and projected timeline cards.
  - Verified with `npm run build` (compiled in <1s with zero errors).

### Entry 19: Dynamic Subscriptions & Recurring Detection Engine
- **Issue**: In the uploaded statement, the header rendered "3 Actionable Leaks Found" but the cards below were completely empty.
- **Root Cause**:
  1. The UI was hardcoded to look for three specific fixed keys: `duplicate_alert`, `price_creep_alert`, and `zombie_alert`.
  2. If an uploaded statement didn't happen to have the exact Spotify/Cult.Fit strings, `engine.py` returned `None`, leaving the UI cards empty while displaying a hardcoded label "3".
- **Fix**:
  - Re-architected `backend/app/services/analytics/engine.py` to be **100% dynamic**:
    - Discovers duplicate streaming and price hikes if present.
    - If specific subscriptions aren't detected, automatically runs **periodic recurrence analysis** (`month_count >= 2`) across all debits.
    - Successfully detected the 3 actual recurring charges in `working_person_statement.csv`:
      1. `Greenview Apartments - Rent` (₹20,000/mo)
      2. `HDFC Bank - Personal Loan EMI` (₹10,000/mo)
      3. `Zerodha Mutual Fund SIP` (₹8,000/mo)
  - Updated `frontend/src/app/page.tsx`:
    - Reads dynamically from `subscriptions.items` array.
    - Displays the exact count of items found: `{subscriptions.items.length} Actionable Items Detected`.
    - Renders dynamic cards with appropriate badges (`RECURRING OBLIGATION`, `DUPLICATE SUBSCRIPTION`, `PRICE CREEP`).

### Entry 20: Dedicated Insurance Planner Page & Direct Navigation Button
- **User Prompt**: "below Insurance Protection & Gap Analysis, there should be button that should take to insurance planner page"
- **Actions Taken**:
  - **Overview Page Navigation**:
    - Added an "Open Insurance Planner" button directly inside the "Insurance Protection & Gap Analysis" card footer on the Overview page (`activeTab === 'dashboard'`).
    - Made both Life Insurance and Health Insurance gap indicators dynamic based on the active ledger data.
  - **Top Navigation Bar**:
    - Added **Insurance Planner** as a primary navigation tab (`activeTab === 'insurance'`) alongside `Overview`, `Monthly Drilldown`, `Goal Simulator`, and `Statement Vault`.
  - **Dedicated Insurance Planner View**:
    - **Summary Metric Cards**: Live display of Recommended Pure Term Cover, Detected Existing Life Cover, Net Protection Deficit, and Health Policy Audit status.
    - **Interactive Human Life Value (HLV) Calculator**: Interactive range sliders for Annual Take-Home Income, Multiplier (8x to 20x), Outstanding Loan Liabilities, and Existing Liquid Assets with real-time recalculation of recommended cover, monthly term premiums, and coverage gaps.
    - **Health Defense Matrix**: 2-layer healthcare strategy highlighting base retail family floater (₹15L-₹25L) and catastrophic super top-up (₹50L with ₹5L deductible).
    - **Fiduciary Policy Guidance**: Mathematical comparison table contrasting low-yielding Endowment/ULIP traps (4.5% IRR) with pure term protection paired with low-cost index funds (12% CAGR).
    - **Actionable Execution Checklist**: 3-step fiduciary roadmap for life cover, healthcare defense, and legacy policy audits.
  - **Backend Improvements**:
    - Fixed a copy-paste check in `backend/app/services/analytics/engine.py` where life insurance insights were conditionally overridden by health checks.
  - **Compliance & Build Verification**:
    - Strictly verified zero em dashes across the codebase.
    - Retained modern institutional light theme (`#F9FAFB` / `#FFFFFF` / Inter font).
    - Verified with `npm run build` (compiled cleanly in 2.2s).

### Entry 21: Multi-File Statement Upload & Automated Ledger Stitching
- **User Prompt**: "why is it not allowing me to upload multiple files at once?" (showing Finder dialog with monthly SBI PDF e-statements: `dec.pdf`, `jan.pdf`, `feb.pdf`, `march.pdf`, `april.pdf`, `may till 17.pdf`).
- **Root Cause**:
  1. The HTML `<input type="file">` elements on both the zero-state upload screen and the Statement Vault lacked the `multiple` attribute. Without this, macOS Finder forcibly disables multi-file selection (Shift+click and Cmd+click).
  2. The frontend `handleFileUpload` only submitted `files[0]`.
  3. The FastAPI `/api/upload` endpoint only accepted a single `file: UploadFile = File(...)`.
- **Fix**:
  - **Frontend (`frontend/src/app/page.tsx`)**:
    - Added `multiple` attribute to both file inputs.
    - Added full native drag and drop listeners (`onDragOver`, `onDragLeave`, `onDrop`) with visual state feedback (`isDragging`).
    - Implemented `uploadFiles` taking `File[]` and appending all files as `files` to `FormData`.
    - Updated copy to "Browse Statement Files (Multi-Select)" and "Drag & drop one or multiple monthly statements".
  - **Backend (`backend/main.py`)**:
    - Updated `/api/upload` to accept `files: Optional[List[UploadFile]] = File(None)` as well as single `file`.
    - Iterates over all uploaded statement files, extracting transactions using `parse_statement_file`.
    - Concatenates transactions, sorts chronologically by `date`, deduplicates overlapping transactions across monthly boundaries, and ensures continuous running balance calculation.
    - Saves unified ledger as `active_merged_{N}_statements.csv`.
  - **Verification**:
    - Tested end-to-end with the user's actual 6 monthly SBI PDFs (`dec.pdf`, `jan.pdf`, `feb.pdf`, `march.pdf`, `april.pdf`, `may till 17.pdf`).
    - Successfully parsed and merged all 561 transactions spanning Dec 2025 to May 2026.
    - Re-built frontend (`npm run build` completed in 1.0s with zero errors).

### Entry 22: Cleaned Upload Button Labels
- **User Prompt**: "remove text in brackets 'multi select' no need to mention"
- **Actions Taken**:
  - Cleaned upload button copy in `frontend/src/app/page.tsx`:
    - Zero-state upload button changed from `"Browse Statement Files (Multi-Select)"` to `"Browse Statement Files"`.
    - Statement Vault upload button changed from `"Select Files (Multi-Select)"` to `"Select Files"`.
  - Retained multi-file selection (`multiple` attribute) and native drag-and-drop capability.
  - Verified with `npm run build` (compiled cleanly in 840ms with zero errors).

### Entry 23: Removed Demo Prompt Below Upload Card
- **User Prompt**: "remove this too" (referring to "Don't have a statement handy? Test with Master Salaried Dataset (758 transactions)").
- **Actions Taken**:
  - Removed the auxiliary demo helper text and link below the zero-state upload card in `frontend/src/app/page.tsx`.
  - Preserved the clean minimalist upload dropzone.
  - Verified with `npm run build` (compiled cleanly in 750ms).

### Entry 24: Shifted Zero-State Upload Section Higher Up
- **User Prompt**: "move the whole thing up in the page. looks bad"
- **Actions Taken**:
  - Removed vertical centering (`flex-1`, `justify-center`) from `<main>` on the zero-state page in `frontend/src/app/page.tsx`.
  - Replaced extreme padding (`py-20`) with natural top-weighted spacing (`pt-10 pb-16`).
  - Constrained width to `max-w-3xl` for a tighter, more intentional layout directly below the navbar without massive dead space.
  - Verified with `npm run build` (compiled cleanly in 740ms).

### Entry 25: Fixed Cumulative Statement Stitching & Original Filename Tracking
- **User Prompt**: "what is the proccess going in back, when i uploaded 1 pdf, and then sometimes later another, previous one is no longer there. also i upload pdf and it says csv, i want to understand what is going on?"
- **Root Cause**:
  1. The backend extracted transactions from PDFs and saved the normalized table as a local CSV file (`active_feb.csv`), which was returned verbatim to the frontend UI as the statement name.
  2. Successive uploads through Statement Vault were overwriting `CURRENT_FILE_PATH` rather than appending and stitching them to the existing active ledger.
- **Fix**:
  - Implemented `CURRENT_DISPLAY_NAME` and `UPLOADED_FILENAMES` tracking original file names (`feb.pdf` instead of `active_feb.csv`).
  - Updated `/api/upload` to merge incoming statement transactions with existing active ledger data, sorting chronologically, deduplicating boundaries, and recalculating balances.
  - Successive uploads now append cleanly (e.g. `feb.pdf` + `march.pdf` -> `2 Statements (feb.pdf, march.pdf)` with 184 transactions).

### Entry 26: Multi-Statement Vault with Individual Unload and Ledger Re-Stitching
- **User Prompt**: "each statement should be stored here as a list. and a upload button below to upload more, each uploaded statement should be a row, it should should what is the date range of that statement(coz person can upload monthy or 6month or random interval statements) and unload button. suppose i upload month 1, then sometime later month 2 , then month 3. then i removed month2, how are we managing the data in the background."
- **Architecture Implemented**:
  - **Vault Catalog & Manifest (`vault_storage/manifest.json`)**:
    - Each uploaded statement file is given a unique statement ID and stored independently in `vault_storage/{id}.csv`.
    - Manifest tracks metadata for each statement: `id`, `filename`, `date_range` (exact start to end date), `transactions_count`, `inflow`, `outflow`, `uploaded_at`.
  - **Dynamic Unified Ledger (`rebuild_active_ledger`)**:
    - Master active ledger is the dynamic union of all active statements in the vault.
    - When statements are added or removed, the engine re-stitches remaining statements, sorts chronologically, deduplicates boundary overlaps, and recalculates continuous running balances.
  - **Granular Removal Endpoint (`DELETE /api/statements/{statement_id}`)**:
    - Deleting a statement (e.g. Month 2) removes its data file, updates the manifest, and instantly re-stitches remaining statements (Month 1 + Month 3). If all statements are removed, returns cleanly to zero-state.
  - **Statement Vault UI (`frontend/src/app/page.tsx`)**:
    - Displays active statements as distinct rows in a list card: Filename, Period date range badge, Volume count, Cashflow in/out, and an individual **Unload** button.
    - Renders the upload area directly below the list to append more intervals at any time.
    - Added top summary bar with active statements count, total records, unified date range, and an "Unload All Statements" button.
  - **Verification**:
    - Tested end-to-end: uploaded `jan.pdf` (Month 1, 115 txs), `feb.pdf` (Month 2, 79 txs), `march.pdf` (Month 3, 105 txs) totaling 299 txs.
    - Deleted `feb.pdf`: successfully excised February, leaving 220 txs across January and March with `/api/months` automatically showing `['2026-03', '2026-01']`.

### Entry 27: Overhaul of Indian UPI Transaction Categorization Engine
- **User Prompt**: "i dont think categories are coreectly written." (Provided sample 2026-09 ledger showing misclassified food vendors, interest credits, and P2P transfers under `Local Vendor / Street Pay`).
- **Root Causes Identified**:
  1. **Credit / Inflow Blindness**: The categorizer only inspected narration text without checking if a transaction was a credit or debit. Bank Interest (`INTEREST CREDIT`), BHIM Cashbacks (`bhimcashba`), and incoming P2P transfers from friends were all dumped into `Daily Micro-Spends / Local Vendor / Street Pay`.
  2. **Regex Over-Matching False Positives**:
     - `vi ` in Vodafone regex was matching personal names like `Manvi J` and marking them as `Utilities & Bills`.
     - `prime` in Amazon Prime regex was matching grocery stores like `Prime Mart` and marking them as `Subscriptions`.
  3. **Missing Real Indian Merchant Heuristics**:
     - `ISTHARA` (co-living / campus food court) was unmapped and falling back to street pay.
     - `SRS BIRI` (SRS Biryani), `K R BAKE` (KR Bakery), `ZAITOON` (restaurant), `BON APPE` (Bon Appetit), `VAJRA CA` (Vajra Cafe) were unmapped.
     - `LENSKART` (eyewear) was unmapped.
     - `Lunavath`, `Miss Manvi`, `Aditya` (peer-to-peer transfers with mobile number VPAs) were treated as generic local vendors instead of personal P2P transfers.
- **Fixes Applied**:
  - **Credit-First Logic**:
    - Credits (`credit > 0`) are evaluated for `Bank Interest`, `Cashbacks & Rewards`, `Refunds & Reversals`, `Salary`, and `Transfers In (P2P)`. No credit is ever categorized as an expense or street pay.
  - **Boundary Guards on Regex**:
    - Fixed telecom patterns (`\b(airtel|jio|vodafone)\b|\bvi\s+recharge\b`) so `Manvi J` is correctly detected as a personal contact, not a utility.
    - Fixed subscription pattern (`amazon\s*prime` instead of bare `prime`) so `Prime Mart` maps to `Groceries & Supplies`.
  - **Expanded Merchant & Campus Patterns**:
    - Added `isthara`, `biri\b`, `bake\b`, `zaitoon`, `bon\s*appe`, `vajra\s*ca`, `babu\s*s`, `moidheen` to `Food Delivery & Dining`.
    - Added `lenskart` to `Healthcare & Eyewear`.
    - Added 10-digit phone number and name title detection (`\b[6-9]\d{9}\b`, `Miss/Mr`) to route personal transfers to `Transfers & P2P / Transfer to Friends & Contacts`.
  - **UI Category Badging**:
    - Added color-coded badges in the Monthly Drilldown ledger for Income (emerald), P2P Transfers (amber), Subscriptions/Fixed (purple), and Discretionary (blue).
- **Result on User's 2026-09 Ledger**:
  - `Local Vendor / Street Pay` dropped from ₹15,978 down to ₹1,388 (actual small QR debits).
  - `Food Delivery & Dining` accurately captured ₹8,024.
  - `Transfer to Friends & Contacts` accurately captured ₹4,635.
  - `Bank Interest` (₹630) and `Cashback` (₹19.28) correctly attributed to Income.

---

## Current System State

| Component | Status | Port / Path |
| :--- | :--- | :--- |
| **Next.js Frontend** | Running | [http://localhost:3000](http://localhost:3000) |
| **FastAPI Backend** | Running | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Active Statement** | Dynamic Vault | `2 Statements (sept_26, aug-26)` |
| **Real PDF Parser** | Tested & Verified | `backend/app/services/parser/universal_parser.py` |
| **Analytics Engine** | Tested & Verified | `backend/app/services/analytics/engine.py` |

---

## Next Steps
- [ ] Implement the AI Copilot / Conversational Chat interface using LLM Function Calling (Gemini).
- [ ] Connect chat tools to the running FastAPI endpoints (`query_transactions`, `get_monthly_summary`, `simulate_goal`).
- [ ] Add tax deduction optimization card (Section 80C & 80D savings finder).

## Entry 28: Merchant Intelligence System & Gemini 3.5 Flash Lite Integration
- **Objective**: Implement the dynamic 3-layer Merchant Intelligence System designed to categorize arbitrary Indian merchants, vendors, and P2P transfers using `gemini-3.5-flash-lite`, persistent merchant dictionary cache, and interactive user review/editing.
- **Backend Enhancements**:
  - Created `backend/app/services/categorizer/merchant_intelligence.py` with batch zero-shot classification using `gemini-3.5-flash-lite`.
  - Added confidence thresholding: >= 50% confidence auto-accepts; < 50% marks `needs_review: true`.
  - Configured persistent store at `vault_storage/merchant_dictionary.json` caching merchant key, display name, category, subcategory, confidence, source, and AI reasoning.
  - Updated `rules.py` and `rebuild_active_ledger()` in `backend/main.py` to consult the dictionary first.
  - Implemented REST APIs:
    - `GET /api/merchant-dictionary` (search and filter support)
    - `PUT /api/merchant-dictionary/{key}` (user category overrides with instant retroactive ledger recalculation)
    - `POST /api/merchant-dictionary/{key}/approve` & `POST /api/merchant-dictionary/approve-all`
    - `GET /api/merchant-dictionary/stats`
    - `POST /api/merchant-dictionary/scan-active`
- **Frontend Enhancements**:
  - Added new **Merchant Intelligence** tab in `frontend/src/app/page.tsx` with live pending item count badge.
  - Added top notification banner alerting the user when low-confidence items need review.
  - Built full interactive directory table with:
    - Status pills (Verified / Needs Review)
    - Inline editable category dropdown grouped by Macro Groups
    - AI Confidence percentage pill and reasoning explanation
    - One-click `[Approve All Pending]` bulk action
    - Live text search and filter pills (All / Needs Review / Verified)
- **Validation**:
  - Scanned active statement items: 40 unique merchants extracted, classified via Gemini REST API in under 2 seconds.
  - Tested retroactive updates with `MOIDHEEN`: changing category immediately updated all historical transactions across the unified ledger.
  - Verified Next.js production build (`npm run build`) succeeded in 1.4s with 0 errors.

## Entry 29: Zero-Flicker Optimistic Updates & Category-Grouped Merchant Layout
- **Objective**: Fix full-page reloads when editing merchant categories and organize verified merchants into distinct category groups where items dynamically migrate upon category change.
- **Frontend Enhancements**:
  - **Eliminated Full-Page Loading Spinner**: Updated `fetchGlobalData` to accept an optional `showFullSpinner` boolean. Initial load displays the spinner once, while subsequent background updates run silently.
  - **Instant Optimistic UI Updates**: `handleUpdateMerchantCategory` and `handleApproveMerchant` update local React state immediately (0ms latency), dynamically recalculating item placement and badge counts before background API sync.
  - **Grouped by Category View**: Verified merchants are now grouped by subcategory (e.g. *Food Delivery & Dining*, *Groceries & Supplies*, *Shopping & E-Commerce*, *Transfer to Friends & Contacts*) with color-coded dot badges, macro group tags, and merchant counts.
  - **Dynamic Item Migration**: Changing a merchant's category from the dropdown instantly moves the row from its current category card into the destination category card.
  - **Isolated Needs Review Section**: Low-confidence items (<50%) are grouped in a dedicated amber review card with inline `[Approve]` and `[Approve All]` buttons. Once approved or categorized, items seamlessly move into the verified groups below.
  - **Banner De-duplication**: Suppressed the global top review notification banner when already viewing the Merchant Intelligence tab.
- **Validation**:
  - Verified in browser: editing category moves the row instantly to the new category section with zero screen reload.
  - Next.js build compiled successfully in 732ms with 0 errors.

## Entry 30: Header Simplification & Single-Line Button Width Fix
- **Objective**: Remove the redundant explanatory paragraph in Merchant Intelligence header and prevent action buttons from wrapping text across two lines.
- **Frontend Changes**:
  - Removed the subtitle text under the Merchant Intelligence header.
  - Added `whitespace-nowrap shrink-0 px-4 py-2` across `Approve All Pending ({count})` and `Reset Cache & Re-run AI` buttons to ensure clean, single-line institutional fintech styling with generous width.
- **Validation**:
  - Production build compiled successfully in 737ms. Server responding 200 OK.

## Entry 31: Multi-Axis Sorting & Category Filtering in Monthly Drilldown Ledger
- **Objective**: Provide comprehensive sorting (by Category, Date, Amount) and category filtering in Monthly Drilldown so users can instantly inspect specific expense groups (e.g. Loan EMIs & Rent ₹62,800).
- **Frontend Enhancements**:
  - **Category-Filtered Drilldown**:
    - Added Category dropdown in the Transactions Ledger toolbar (`All Categories` or specific subcategories like `Loan EMIs & Rent`).
    - Made each category item in the **Expenses by Category** list clickable to immediately toggle ledger filtering.
    - Added an active filter banner showing matched transaction count, total debit sum, and a one-click `[Clear Filter]` button.
  - **Multi-Axis Sorting Controls**:
    - Added toolbar buttons: `Sort by Category` (A→Z / Z→A), `Sort by Date` (Newest / Oldest), and `Sort by Amount` (High→Low / Low→High).
    - Made table header columns (`Date`, `Category`, `Debit`) clickable with sort direction indicator arrows.
    - Category pills in the ledger rows are now clickable shortcuts to filter by that category.
- **Validation**:
  - Tested sorting by Category, Date, and Amount: verified correct ordering and grouping of Loan EMIs & Rent.
  - Next.js build compiled successfully in 1448ms with 0 errors. Server online at port 3000.

## Entry 32: Insurance Planner and Manager Architectural Design
- **Objective**: Design a comprehensive architectural plan for the finMan Insurance Planner and Manager system, expanding bank statement detection, off-statement user declarations, curated Indian product database, Gemini-powered fiduciary recommendations, and multi-persona validation framework.
- **Architectural Deliverables**:
  - **Statement Detection Engine**: Expanded regex signatures and periodic recurrence detection across five core insurance pillars (Pure Term Life, Traditional Endowment, Comprehensive Health, Motor, Personal Accident). Out-of-pocket medical spend monitoring (Apollo, PharmEasy, Dr Lal, etc.) to detect acute healthcare vulnerability.
  - **User Declaration System**: Off-statement policy management for Employer Group Medical Cover (GMC), policies paid from spouse/family accounts, or secondary bank accounts. Stored in `vault_storage/insurance_profile.json` with auto-reconciliation against detected statement debits.
  - **Curated Indian Insurance Database**: Structured catalog of high-performing IRDAI-registered policies (HDFC Life, Max Life, Star Health, HDFC ERGO, Care, Acko, etc.) tracking Claim Settlement Ratios (CSR), Incurred Claim Ratios (ICR), network hospitals, and room rent sub-limits.
  - **Gemini 3.5 Flash Lite Recommendation Engine**: Objective fiduciary advisor synthesizing financial inflows, liabilities, active EMIs, and existing policies to generate structured recommendations with tax optimization under Sections 80C and 80D.
  - **Five Validation Personas**: Detailed synthetic personas (Aarav - Intern, Priya - Single Tech Pro, Vikram - Family Breadwinner with Home Loan, Sunita - Senior Manager with Elderly Parents, Anand - MSME Entrepreneur) to validate detection and suggestions across all scenarios.
- **Status**: Design artifact published for user review (`insurance-planner-manager-design.md`).

## Entry 33: Insurance Planner and Manager Implementation & Multi-Persona Validation
- **Objective**: Build and deploy the full Insurance Planner & Manager system in finMan, including bank statement detection, off-statement user declarations, curated Indian insurance catalog, Gemini 3.5 Flash Lite recommendation engine, and interactive 5-persona test suite.
- **Backend Implementation**:
  - `backend/app/services/insurance/catalog.py`: Curated IRDAI catalog tracking Claim Settlement Ratios (CSR), Incurred Claim Ratios (ICR), network hospitals, and room rent sub-limits across Pure Term Life (Max Life STEP, HDFC Click 2 Protect, Tata AIA), Comprehensive Retail Health (HDFC ERGO Optima Secure, Care Supreme, Star Comprehensive), Super Top-Up (Medisure, Care Enhance), Motor (Acko, Go Digit), and Personal Accident.
  - `backend/app/services/insurance/personas.py`: Built 5 synthetic testing personas (Aarav - Intern, Priya - Tech Pro with Auto Loan & Corporate GMC, Vikram - Married Breadwinner with Home Loan & LIC Endowment Trap, Sunita - Senior Director with High Medical Parent Spends, Anand - MSME Entrepreneur).
  - `backend/app/services/insurance/manager.py`: Policy reconciliation engine combining statement debits with declared policies in `vault_storage/insurance_profile.json`, HLV gap computation, vehicle ownership signals, out-of-pocket medical tracking, and traditional endowment arbitrage calculator.
  - `backend/app/services/insurance/recommender.py`: Gemini 3.5 Flash Lite fiduciary advisor synthesizing financial context and matching curated policies with zero commission bias.
  - `backend/main.py`: Added REST endpoints (`/api/insurance/portfolio`, `/api/insurance/declared`, `/api/insurance/declare`, `/api/insurance/catalog`, `/api/insurance/recommendations`, `/api/insurance/personas`, `/api/insurance/personas/load/{id}`, `/api/insurance/personas/reset`).
- **Frontend Implementation**:
  - Redesigned `Insurance` tab in `frontend/src/app/page.tsx`:
    - **Interactive Persona Testing Suite**: One-click demo toolbar switching between live statement and 5 synthetic personas.
    - **Insurance Shield Overview**: Gauge (0-100), Active Life Cover vs Required HLV, Health Cover status, and 80C/80D tax savings.
    - **Active Insurance Portfolio Vault**: Filterable by category, displaying badges (`Statement Verified`, `Employer GMC`, `User Declared`), sum insured, premium, covered members, and delete actions.
    - **Interactive HLV Calculator**: 5 sliders (Income, Multiplier, Debt, Liquid Assets, Dependents) with dynamic recalculation.
    - **Traditional Endowment Arbitrage Box**: Side-by-side math demonstrating wealth and coverage difference between low-yield endowment and Pure Term + Nifty 50 Index Fund.
    - **Gemini 3.5 Flash Lite Recommendation Hub**: On-demand fiduciary risk diagnosis with prioritized recommendation cards and matched products.
    - **Curated IRDAI Catalog Viewer**: Expandable product inspection matrix.
    - **Declare Policy Modal**: Form to add off-statement employer or family policies.
- **Validation**:
  - Tested persona loading across Aarav, Priya, Vikram, Sunita, and Anand.
  - Verified Gemini 3.5 Flash Lite recommendations: returned in under 4 seconds with structured JSON matching curated products.
  - Verified Next.js production build (`npm run build`) compiled cleanly in 1573ms with zero TypeScript errors. Both backend and frontend active and responsive.

## Entry 34: Multi-Profile & Workspace Architecture Plan
- **Objective**: Design a clean, first-class Multi-Profile & Workspace System to eliminate tab-level demo switchers, isolate user data into dedicated profile sandboxes, and allow instant 1-click switching between personal profiles and test personas without file unloading or data pollution.
- **Key Architectural Decisions**:
  - **Isolated Storage Sandboxes**: Migrates `vault_storage/` to `vault_storage/profiles/{profile_id}/`, containing dedicated statements, `manifest.json`, `active_unified_ledger.csv`, `merchant_dictionary.json`, and `insurance_profile.json`.
  - **Global Header Profile Switcher**: Removes the crowded persona switcher bar from the Insurance tab. Replaces it with a global profile menu in the top navbar (`[R] Raghava ▾`).
  - **Global Workspace Synchronization**: Switching a profile updates the entire application context simultaneously (Overview, Monthly Drilldown, Goal Simulator, Insurance Planner, Statement Vault, Merchant Intelligence).
  - **Automatic Migration**: Auto-migrates existing statements safely into `raghava_personal/` with zero data loss.
- **Status**: Plan published for user review (`multi-profile-architecture-plan.md`).

## Entry 35: Multi-User Authentication & Account Persistence System Plan
- **Objective**: Redesign the profile model into a true Multi-User Account and Authentication System with persistent user databases, individual credentials, sign in / sign out flows, and pre-registered persona accounts.
- **Key Architectural Decisions**:
  - **No In-App Switchers**: Strip out all dropdown switchers and demo banners from the navigation bar and tabs.
  - **Login & Sign-Up Portal**: When unauthenticated, users see a sign-in screen with username/PIN inputs, a "Create New Account" flow, and 1-click test persona login cards.
  - **Isolated Storage Sandboxes**: Every user account (`raghava`, `vikram`, `priya`, or new friend accounts) has their own folder under `vault_storage/users/{user_id}/`.
  - **Zero Re-Analysis on Login**: All parsed statements, categorized transactions, verified merchant classifications, and insurance audits remain permanently saved. Logging back in instantly restores previous state without re-running parsing or Gemini.
  - **Auto-Migration**: Existing statement vault files safely migrate into `vault_storage/users/raghava/`.
- **Status**: Updated plan published for user review (`multi-profile-architecture-plan.md`).


## Entry 36: Full Implementation of Multi-User Account & Authentication System
- **Objective**: Implement the complete Multi-User Account & Authentication architecture for `finMan`, transitioning the app from a single-user system into an institutional multi-profile platform with independent user databases, credential-based sign in / sign out flows, isolated user vaults, and 1-click test persona logins.
- **Backend Implementation**:
  - **Account Registry & Vault Migration** (`backend/app/services/auth/users.py`):
    - Created `load_users_registry()`, `save_users_registry()`, `authenticate_user()`, `register_user()`, `get_user_by_username()`, and `list_demo_personas()`.
    - Master user registry persisted in `vault_storage/users_registry.json`.
    - Automated migration in `initialize_and_migrate_vault()`: moved legacy root `vault_storage/` files (`manifest.json`, `active_unified_ledger.csv`, `merchant_dictionary.json`, statements) into `vault_storage/users/raghava/`.
    - Generated dedicated pre-seeded sandboxes for all 5 demo personas (`vikram`, `priya`, `aarav`, `sunita`, `anand`), complete with dedicated unified ledgers, manifests, merchant dictionaries, and declared/detected insurance profiles.
  - **Scoped Endpoints** (`backend/main.py`):
    - Added auth API routes: `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/personas`, `GET /api/auth/me`.
    - Created `get_user_vault(request)`: inspects `X-User-ID` header (defaults safely to `raghava` for backwards compatibility).
    - Scoped all financial routes to the calling user's vault: `/api/overview`, `/api/months`, `/api/month-detail/{year_month}`, `/api/statements-list`, `/api/statements/{id}`, `/api/upload`, `/api/clear-statement`, `/api/subscriptions`, `/api/insurance/portfolio`, `/api/insurance/declared`, `/api/insurance/declare`, `/api/merchant-dictionary`, `/api/merchant-dictionary/stats`, `/api/merchant-dictionary/approve`, etc.
    - Updated `compute_insurance_portfolio` and declared policy storage to accept `user_vault_dir`.
- **Frontend Implementation** (`frontend/src/app/page.tsx`):
  - **Authentication State & Header Injection**:
    - Added `currentUser`, `authChecking`, `authMode`, `authLoginForm`, `authRegisterForm`, `authError`, `authLoading`, and `availablePersonas`.
    - Implemented `getAuthHeaders(userOverride?)`: injects `X-User-ID: currentUser.username` into every API request.
  - **Authentication Portal**:
    - Rendered when `!currentUser`: clean, modern Stripe/Mercury inspired login portal in `#F9FAFB` light mode.
    - Includes dual-mode Sign In / Create Profile form with username and 4-digit PIN (default `1234`).
    - Includes 1-Click Persona & Profile Logins grid: allows instant access into `Raghava` (Personal Vault with 2 real statements and 220 transactions), `Vikram Malhotra` (Tech Lead, LIC trap), `Priya Nair` (Independent Consultant, 0 health cover), `Aarav Sharma` (Intern, fresh graduate), `Sunita Sengupta` (Senior Director, elderly parents), and `Anand Vardhan` (MSME Owner, business debts).
  - **Header & Navbar Profile Pill**:
    - Replaced generic header actions with an institutional user pill displaying avatar initials, full name, and vault badge (`Personal Vault` or `Persona Profile`).
    - Added clean `Sign Out` button (`LogOut` icon) with cursor pointer.
  - **Tab Cleanup**:
    - Removed the old demo switcher toolbar from the Insurance Planner tab. Replaced it with an informative Profile Context Banner with a "Switch Profile" shortcut.
- **Verification & Testing**:
  - Tested login as `raghava` with PIN `1234`: successfully loaded 2 statements and 220 transactions.
  - Tested login as `vikram` with PIN `1234`: loaded Vikram's isolated ledger, home loan EMI, Star Health policy, and LIC endowment arbitrage calculation.
  - Tested registration flow (`POST /api/auth/register`): created a new isolated sandbox with `has_statement: false` without interfering with other profiles.
  - Verified policy declaration under `raghava`: updated Raghava's shield score from 20 to 60 while leaving Vikram's portfolio completely untouched.
  - Verified production build: `npm run build` compiled cleanly in under 2 seconds with zero TypeScript or JSX errors.
- **Status**: Complete and operational.

## Entry 37: 1-Year Comprehensive Datasets for All 5 Personas & Insurance Tab Cleanup
- **Objective**: Replace the single-month stub datasets with authentic 1-year banking statements (12 continuous months from November 2025 to October 2026) across all 5 test personas, and remove the redundant switch profile banner from the Insurance Planner tab.
- **Implementation**:
  - **1-Year Dataset Generation** (`backend/app/services/insurance/personas.py`):
    - Implemented authentic month-by-month cashflow generators covering 12 consecutive months (`2025-11` through `2026-10`).
    - **Vikram Malhotra** (245 txns): Monthly Tata Motors salary (₹2.1L), ₹58k HDFC home loan EMI, LIC traditional endowment debit in August (₹28.5k), quarterly school tuition (₹16k), groceries, utilities, and dining.
    - **Priya Nair** (231 txns): Monthly consulting retainers (₹1.35L - ₹1.65L), ₹14.8k auto loan EMI, FASTag/fuel, ₹28k apartment rent, Adobe CC, Figma, Zara, and annual motor insurance in April (₹9.4k).
    - **Aarav Sharma** (196 txns): Transitioned from intern stipend (₹45k) to FTE salary (₹60k in June 2026), flatshare rent (₹14k), Namma Metro, Rapido, GitHub Copilot, zero debts, and zero insurance.
    - **Sunita Sengupta** (218 txns): Executive MNC salary (₹3.8L), geriatric care expenses (Max Healthcare, MedPlus chronic meds, Dr. Lal PathLabs, Portea physiotherapy), domestic staff salaries, HDFC Life pure term in March (₹32k), and Care Health in June (₹44.5k).
    - **Anand Vardhan** (186 txns): Business profit transfers (₹3L - ₹3.8L), personal guarantee MSME debt (₹48k/mo), commercial vehicle EMI (₹24.5k), quarterly advance tax (₹65k), Go Digit motor insurance in February (₹18.2k), and Star Health in November (₹36k).
  - **Sandbox Seeding** (`backend/app/services/auth/users.py`):
    - Updated `initialize_and_migrate_vault()` to detect and seed 1-year datasets into `vault_storage/users/{username}/`.
    - Generated `active_unified_ledger.csv`, `{username}_statement.csv`, updated `manifest.json`, and seeded `merchant_dictionary.json` with realistic confidence scores and review flags.
  - **UI Cleanup** (`frontend/src/app/page.tsx`):
    - Removed the redundant profile banner from the Insurance Planner tab, freeing up vertical screen space.
- **Verification**:
  - Verified `GET /api/overview` across all 5 personas: each returns between 186 and 245 transactions spanning 12 months.
  - Verified `GET /api/months`: returns all 12 consecutive months (`2026-10` down to `2025-11`).
  - Tested `GET /api/month-detail/2026-01` for Vikram: returns 21 transactions, 10 subcategories, and 19 daily burn data points.
  - Verified Gemini AI recommendations: generated prioritized fiduciary recommendations (e.g., Pure Term matching for Vikram).
  - Production build: `npm run build` compiled in 758ms with 0 errors.
- **Status**: Complete and operational.

## Entry 38: Universal Bank CSV Parser, Sample Statements Folder & 1-Click Restore
- **Objective**: Provide clean, standalone 1-year sample statement CSV files for all personas in an accessible directory, enhance the universal parser to support standard banking CSV formats, and provide a 1-click restore mechanism on the upload zero-state screen.
- **Implementation**:
  - **Sample Statements Directory** (`sample_statements/`):
    - Exported 1-year CSV statements for all 5 personas:
      - `sample_statements/vikram_malhotra_1year_statement.csv` (245 txns)
      - `sample_statements/priya_nair_1year_statement.csv` (231 txns)
      - `sample_statements/aarav_sharma_1year_statement.csv` (196 txns)
      - `sample_statements/sunita_sengupta_1year_statement.csv` (218 txns)
      - `sample_statements/anand_vardhan_1year_statement.csv` (186 txns)
  - **Universal CSV Parser Upgrade** (`backend/app/services/parser/universal_parser.py`):
    - Implemented `parse_standard_bank_csv()`: automatically identifies standard banking columns (`date`, `narration`, `debit`, `credit`, `balance`), strips commas, standardizes dates, and maintains running balance.
    - Updated `parse_statement_file()` to prioritize `parse_standard_bank_csv()` before falling back to `parse_phonepe_csv()`.
  - **Zero-State Restore Button & Endpoint** (`backend/main.py` & `frontend/src/app/page.tsx`):
    - Implemented `POST /api/load-demo`: re-hydrates the active persona's 1-year dataset and updates the manifest.
    - Added a `[Restore Vikram's 1-Year Statement]` secondary button on the upload screen next to `[Browse Statement Files]`.
- **Verification**:
  - Tested uploading `vikram_malhotra_1year_statement.csv` via `POST /api/upload`: parsed all 245 transactions successfully.
  - Tested `npm run build`: compiled in 972ms with 0 errors.
- **Status**: Complete and operational.

## Entry 39: Removal of Vague Insurance Shield Score in Favor of Concrete Metrics
- **Objective**: Remove the arbitrary and vague "Insurance Shield Score" (0-100 score and badge) across the Insurance Planner tab in finMan. Replace it with direct, tangible metrics: Life Protection Deficit, Health Coverage, Annual Premium Outflow, and Section 80C/80D Tax Deductions.
- **Implementation**:
  - **Header Cleanup** (`frontend/src/app/page.tsx`):
    - Removed the vague status badge (`Evaluating Shield...` / `VULNERABLE` / `STRONG SHIELD`) from the header bar, keeping the header clean and focused with the `[Declare Policy]` action.
  - **4 Concrete Summary Cards** (`frontend/src/app/page.tsx`):
    - Replaced the vague 0-100 score card with four concrete, mathematically grounded cards:
      1. `Total Active Life Cover` (Active Cover vs Required HLV and net protection deficit in rupees).
      2. `Total Health Cover` (Total retail/GMC sum insured and out-of-pocket medical expenditures).
      3. `Annual Premium Outflow` (Exact annual premium cost across all detected and declared policies).
      4. `Tax Savings (80C & 80D)` (Annual estimated tax saved at the 30% tax bracket).
  - **AI Recommendation Engine & Verdict** (`backend/app/services/insurance/recommender.py` & `frontend/src/app/page.tsx`):
    - Removed `portfolio_health_score` from the AI verdict header badge in favor of `Fiduciary Review`.
    - Updated Gemini schema and rule-based fallback summary verdict to focus purely on protection gaps rather than synthetic scores.
- **Verification**:
  - Validated frontend render and backend API endpoints.
  - Verified no compilation errors or broken references.
- **Status**: Complete and verified.

## Entry 40: Dynamic Insurance Portfolio Re-Fetch Across User Life Cycle and Statement Uploads
- **Objective**: Ensure that insurance policies are dynamically detected and immediately reflected for any new profile upon statement upload, resolution, or tab navigation. Eliminate the bug where insurance portfolio was only fetched at login/registration and remained stale in React state when uploading statements.
- **Root Cause Analysis**:
  - The backend detection engine (`backend/app/services/insurance/manager.py`) is completely dynamic and generic: regex-scanning statement debits (`LIC OF INDIA`, `STAR HEALTH`, `HDFC LIFE`, `ICICI LOMBARD`, fuel, toll, etc.) for any user vault.
  - Verification via curl on the user's newly created `persona` profile (`curl -H "X-User-ID: persona" /api/insurance/portfolio`) proved the backend had immediately and accurately detected Vikram's LIC endowment debit (₹28,500/yr, ₹4.28L cover, ₹22.2k medical spends, FASTag debits, and full arbitrage).
  - The bug was entirely on the frontend: `fetchInsuranceData()` was only triggered during initial login. In `uploadFiles`, `handleLoadDemo`, `handleClearStatement`, and `handleUnloadSingleStatement`, only `fetchGlobalData()` was awaited. Furthermore, switching tabs to `activeTab === "insurance"` did not trigger a re-fetch. Consequently, the React `insurancePortfolio` state remained frozen in the zero-statement initial state.
- **Implementation**:
  - **Auto-Sync in Global Fetch** (`frontend/src/app/page.tsx`):
    - Positioned `fetchInsuranceData` above `fetchGlobalData` and embedded `await fetchInsuranceData(targetUser)` directly inside `fetchGlobalData` so all data mutations update insurance state automatically.
  - **Upload and Mutation Triggers** (`frontend/src/app/page.tsx`):
    - Added explicit `fetchInsuranceData()` calls inside `uploadFiles`, `handleLoadDemo`, `handleClearStatement`, and `handleUnloadSingleStatement`.
  - **Tab Switch Trigger** (`frontend/src/app/page.tsx`):
    - Added `useEffect` listening to `activeTab === "insurance"` to guarantee fresh portfolio fetching whenever the user visits the Insurance Planner.
  - **Display Formatting** (`frontend/src/app/page.tsx`):
    - Updated `Total Active Life Cover` card so covers under ₹1 Crore render clearly in Lakhs (e.g. `₹4.3 L`) rather than rounding down to `₹0.00 Cr`.
- **Verification**:
  - Verified `curl /api/insurance/portfolio` returns full detection on newly created test user `persona`.
  - Verified `npm run build` completed cleanly in 1039ms with 0 errors.
- **Status**: Complete and verified.

## Entry 41: Multi-Goal Portfolio System, Real Cashflow Grounding, and Interactive Trajectory Simulation
- **Objective**: Rebuild the Goal Simulator from a simplistic two-slider toy into a comprehensive, multi-goal financial planning engine. Ground all simulations in authentic 12-month statement analytics (mean income, mandatory living burn, true monthly surplus, and real discretionary spending categories).
- **Implementation**:
  - **Goals Engine & Service** (`backend/app/services/goals/engine.py`):
    - `get_cashflow_context()`: Dynamically extracts mean monthly income, mandatory monthly living burn (fixed EMIs, rent, utilities, essential groceries), true monthly savings surplus, and the user's top discretionary expense subcategories with actual spending figures.
    - Auto-derives a non-negotiable **6-Month Emergency Safety Vault** target directly from 6x mandatory monthly living burn with zero guesswork.
    - `load_user_goals()` / `save_user_goals()`: Persists user-defined and auto-derived goals to isolated JSON files in `vault_storage/users/{username}/goals.json`.
    - `simulate_goal_trajectory()`: Calculates month-by-month compound growth trajectories incorporating:
      - Baseline pace (nominal monthly savings without returns).
      - Optimized pace (boosted monthly contribution with discretionary spending cuts, lumpsum infusion, and compound returns at selected CAGR).
      - Optional 6% annual inflation adjustment.
      - Exact milestone completion month/year, months saved, total out-of-pocket invested, and interest earned.
  - **REST Endpoints** (`backend/main.py`):
    - `GET /api/goals`: Returns user goals and real cashflow context.
    - `POST /api/goals`: Creates or updates a goal.
    - `DELETE /api/goals/{goal_id}`: Deletes a goal.
    - `POST /api/goals/simulate`: Executes advanced trajectory simulation with dynamic discretionary cuts and compound interest.
  - **Frontend UI Redesign** (`frontend/src/app/page.tsx`):
    - **Cashflow Reality Banner**: 5-card strip displaying real monthly income, mandatory burn, true monthly surplus, total allocated to goals, and free unallocated cash.
    - **Multi-Goal Portfolio Strip**: Horizontal cards allowing users to view and switch between active goals (Emergency Fund, Vacation, Vehicle Down Payment, Custom), with category icons, target amounts, and monthly SIP contributions.
    - **Interactive Scenario Controls**:
      - Goal target amount slider with quick presets (3-Mo Emergency, 6-Mo Emergency, ₹1L, ₹2.5L, ₹5L, ₹10L).
      - Monthly allocation slider mapped to the user's real monthly surplus.
      - Dynamic discretionary spending levers pulling the user's actual top spending categories (e.g. Food Delivery & Dining, Shopping & E-Commerce) with sliders to test 0% to 50% cuts.
      - Lumpsum boost infusion slider (bonus / tax refund).
      - Investment vehicle picker: Cash / FD (6.5%), Balanced Hybrid (9.5%), Nifty 50 Index (12.0%).
      - Inflation protection toggle (6% annual inflation).
    - **Milestone Verdict & Decomposition**: Displays projected completion month/year (e.g. "October 2026"), months saved, total invested, compound growth interest, and fiduciary feasibility verdict.
    - **Interactive AreaChart (Recharts)**: Visual month-by-month accumulation curve with gradient fill, baseline pace comparison line, dashed target reference line, and hover tooltips.
    - **Create Goal Modal**: Clean modal to add custom financial goals.
- **Verification**:
  - Tested `GET /api/goals` for `persona`: accurately auto-calculated ₹5,07,608 6-Month Emergency Fund based on actual ₹84.6k/mo living burn.
  - Tested `POST /api/goals/simulate`: verified accurate compounding and timeline speedup.
  - Production build: `npm run build` compiled in 1897ms with 0 errors.
- **Status**: Complete and operational.

## Entry 42: UI Polish for Goal Simulator, Mandatory Emergency Fund Removal, and Trajectory Chart Elimination
- **Objective**: Refine the Goal Simulator and Scenario Levers UI into an institutional, modern fintech interface. Eliminate the mandatory Emergency Safety Vault auto-seeding so goals are strictly user-directed. Remove the Trajectory AreaChart per user feedback, balance discretionary trimming into a clean 3-column layout, and add seamless "Save as Tracked Goal" capabilities.
- **Implementation**:
  - **Opt-in Goal Experience (`backend/app/services/goals/engine.py` & `vault_storage`)**:
    - Removed mandatory fallback seeding in `load_user_goals()`. Empty portfolios remain `[]` unless explicitly created by the user.
    - Wiped forced emergency fund goals from storage (`persona` and `vikram`).
    - Unlocked goal deletion across all items in `frontend/src/app/page.tsx` (removed `!g.is_auto_derived` lock and auto-derived badge).
    - Added an empty-state card when zero goals exist, encouraging free scenario simulation or 1-click goal creation.
  - **Scenario Levers UI Modernization (`frontend/src/app/page.tsx`)**:
    - **Header**: Refined typography, live simulator badge, and clean subheadings.
    - **Target Amount Control**: Currency box with formatted input, streamlined slider, and quick presets (`₹50k`, `₹1 Lakh`, `₹2.5 Lakh`, `₹5 Lakh`, `₹10 Lakh`, `₹20 Lakh`) with emergency fund presets completely removed.
    - **Surplus Monthly Allocation**: Added real-time cashflow surplus health indicators (emerald pill when within surplus, amber warning with excess gap if exceeding surplus). Added 1-click surplus percentage presets (`25%`, `50%`, `75%`, `100%`).
    - **Discretionary Spending Levers**: Redesigned from an unbalanced 2-column layout into a balanced 3-column grid (`grid grid-cols-1 md:grid-cols-3 gap-3`). Added quick 1-click trim chips (`Keep all`, `Trim 25%`, `Max 50%`) with active savings tags (`+₹X/mo unlocked`).
    - **Lumpsum & CAGR Vehicle Controls**: Clean 2-column card grouping with quick chips for lumpsum infusion and segmented pills for investment return vehicle selection (`Cash / FD`, `Hybrid`, `Equity Index`).
    - **Inflation Protection Toggle**: Modern styled switch card with real purchasing power explanation and status pill (`Inflation Protected` vs `Nominal Value`).
    - **Verdict & Projection Scorecard**: High-contrast completion date card, detailed capital breakdown (principal vs compound interest vs discretionary cuts), feasibility verdict, and a primary "+ Save as Tracked Goal" action button.
    - **Trajectory Chart Removal**: Completely removed the Visual Wealth Accumulation Trajectory AreaChart block as requested to eliminate visual clutter.
- **Verification**:
  - `npm run build` compiled with 0 errors in 1688ms.
  - Verified `GET /api/goals` for `persona` returns clean `{"goals": []}`.
  - Verified `POST /api/goals/simulate` responds instantly with accurate timeline calculation.
- **Status**: Complete and verified.

## Entry 43: Resolving Merchant Intelligence Timeout and Implementing Chunked Gemini Architecture
- **Objective**: Fix the issue where all 234 merchants defaulted to 30% confidence with "Unrecognized merchant, defaulted to general shopping". Ensure genuine rule-based classification for known entities (Blinkit, Swiggy, Zepto, Apollo, etc.) and authentic live Gemini 3.5 Flash Lite inference for ambiguous merchants without any hardcoded leaks.
- **Root Cause**:
  - The previous implementation attempted to classify all 234 merchants in a single massive prompt with a hardcoded 12-second HTTP timeout. Generating structured JSON for 234 items exceeded 12 seconds, resulting in requests.exceptions.ReadTimeout.
  - The exception handler caught the timeout and returned an empty dictionary, which caused all 234 merchants to fall back to the default 30% confidence "Local Shopping & Services" entry.
  - Furthermore, clean_narration in rules.py checked the merchant dictionary before evaluating standard rules, which prevented KNOWN_PATTERNS from classifying even obvious merchants once fallback entries were present.
- **Implementation**:
  - **Rule-Based Pre-Classification (merchant_intelligence.py & rules.py)**:
    - High-certainty commercial patterns (KNOWN_PATTERNS) are evaluated first to auto-verify known brands (Blinkit, Swiggy, Zepto, KFC, Apollo Pharmacy, Uber, IRCTC, AWS, Google, PVR, etc.) with 99% confidence and "Identified via standard verified entity registry" reasoning.
    - Low-confidence unverified fallback entries in merchant_dict (<= 0.30) no longer block rule-based evaluation.
  - **Chunked Batching for Gemini (merchant_intelligence.py)**:
    - Chunked ambiguous merchant lists into batches of 25 items per request.
    - Added deterministic integer id tracking in prompt and response to prevent key mismatch or LLM string truncation.
    - Increased request timeout to 35 seconds per batch with an automatic retry on failure.
  - **Reset Cache & Re-run AI (backend/main.py)**:
    - Updated POST /api/merchant-dictionary/reset to re-scan active transactions, auto-verify rules, and dispatch ambiguous merchants to Gemini fresh.
- **Verification**:
  - Verified live execution across 234 merchants: 51 auto-verified via rules and 183 classified live across 8 chunked requests via Gemini 3.5 Flash Lite in 200 OK responses.
  - Inspected final dictionary: 232 verified merchants with rich categories (Food Delivery, Groceries, Healthcare, Transit, Subscriptions, Transfers) and only 2 genuinely obscure entries flagged for review.
- **Status**: Complete and verified.
