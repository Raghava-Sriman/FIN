# FinSight evals

These measure how well the app categorizes transactions and how faithfully Finneas reports numbers. They are separate from the unit tests in `backend/tests/`.

| File | What it is |
|---|---|
| `generate_student_statement.py` | Writes the synthetic student statement and its ground-truth labels to `data/`. Deterministic for a given `--seed`. |
| `data/student_statement.csv` | The statement, in HDFC-style CSV format, as it would be uploaded. |
| `data/student_labels.csv` | One row per transaction: expected sub-category and top-level category, hard-case group, `ambiguous`, and a note. |
| `finneas_questions.py` | The 20 grounding questions, how each expected answer is computed, the 5 out-of-scope questions, and the grading rules. |
| `run_evals.py` | Runs everything and writes `reports/eval_report_<time>.md` plus raw results as JSON. |
| `private/` | Your real labelled transactions. **Gitignored; never commit it.** |
| `reports/` | Generated reports. **Gitignored.** |

## Running

From `backend/`, with the virtual environment's Python:

```bash
python evals/generate_student_statement.py        # only needed if you change the generator
python evals/run_evals.py                         # synthetic + Finneas, 3 AI runs
python evals/run_evals.py --only real --real evals/private/real_labeled.csv
python evals/run_evals.py --skip-ai               # rules only, no Gemini calls
```

- Gemini is used through `GEMINI_API_KEY` / `GEMINI_MODEL` in `backend/.env`.
- A full synthetic run with 3 AI runs makes about 100–150 Gemini calls and takes roughly 10–20 minutes.
- Everything happens in a temporary directory. Nothing is written to `vault_storage/`.

## Your real data: `private/real_labeled.csv`

An empty template with the header is in `private/real_labeled.csv`. Fill in one row per transaction:

| Column | Required | Format |
|---|---|---|
| `date` | yes | Any common format; day first is assumed (`05/03/2026` is 5 March). |
| `narration` | yes | The description exactly as your bank shows it. |
| `debit` | yes | Money out, as a number, or empty. |
| `credit` | yes | Money in, as a number, or empty. |
| `correct_category` | yes | One of the names below, spelled exactly. |
| `ambiguous` | yes | `yes` if the right category can't be told from the narration and amount alone (for example a QR code payee, or a personal name that was actually a shop), otherwise `no`. |
| `hard_case` | no | `allowance`, `friends`, `refund_cashback` or `cryptic`, to get the hard-case breakdown for your data too. |

Rows with a category that isn't in the list are skipped and counted in the report. The report shows only aggregate numbers. Mismatches are described by shape (channel, kind of payee, amount range), never by name, handle, reference number or exact amount.

### Valid category names

| `correct_category` | Top-level category |
|---|---|
| Food Delivery & Dining | Discretionary |
| Shopping & E-Commerce | Discretionary |
| Entertainment & Outings | Discretionary |
| Travel & Vacation | Discretionary |
| Local Shopping & Services | Discretionary |
| Groceries & Supplies | Variable Essentials |
| Healthcare & Eyewear | Variable Essentials |
| Education & Academic | Variable Essentials |
| Fuel & Commute | Variable Essentials |
| Ride Hailing & Auto | Variable Essentials |
| Public Transit & Metro | Variable Essentials |
| Utilities & Bills | Fixed Expenses |
| Subscriptions | Fixed Expenses |
| Cloud & Tech Tools | Fixed Expenses |
| Insurance Premiums | Fixed Expenses |
| Loan EMIs & Rent | Fixed Expenses |
| Transfer to Friends & Contacts | Transfers & P2P |
| Local Vendor / Street Pay | Daily Micro-Spends |
| Bank Interest | Income |
| Cashbacks & Rewards | Income |
| Refunds & Reversals | Income |
| Salary | Income |
| Transfers In (P2P) | Income |

These are the app's standard sub-categories (`SUB_TO_MACRO` in `app/services/categorizer/merchant_intelligence.py`). Pocket money from family goes under **Transfers In (P2P)**; a stipend goes under **Salary**.

## How grading works

- **Categorization:** ledger rows are matched to labels on (date, narration, debit, credit), then compared at sub-category level and at top-level category level.
- **Review flags:** counted per merchant. A flagged merchant is "genuinely ambiguous" if any of its transactions is labelled `ambiguous`.
- **Finneas:** see the docstring in `finneas_questions.py`. Amounts must match to the whole rupee.
