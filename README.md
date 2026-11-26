<div align="center">

<img src="finneas.gif" alt="Finneas, the FinSight assistant" width="160" />

# FinSight

**Upload your bank statements. See where your money goes. Ask Finneas about it.**

FinSight is a personal finance assistant for Indian bank and UPI statements. It reads your statements, sorts every transaction into a category, shows your spending month by month, tracks your savings goals, and lets you ask questions about your money in plain language.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.11-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white)
![Deploy](https://img.shields.io/badge/deploy-Vercel%20%2B%20Railway-000)

</div>

---

## Why FinSight?

Most people don't know where their money goes. Tracking apps make you type in every expense, and account aggregators want access to your bank login. FinSight takes a different route: you upload the statement your bank already gives you, and it does the rest.

One rule runs through the whole app: **all the arithmetic is done by ordinary Python code, never by the AI.** The AI (Google Gemini) is used only to recognise merchants and to explain the numbers in plain language. Every total Finneas mentions comes from a calculation the app has already done.

## Features

| | |
|---|---|
| 📄 **Statement upload** | PDF, CSV, XLS and XLSX. Built-in parsers for SBI (YONO and NetBanking), PhonePe, Google Pay, Paytm and standard bank CSV/Excel formats. Upload several statements and they are merged into one ledger. |
| 🏷️ **Automatic categorization** | Rules handle the common cases (food delivery, rides, rent, subscriptions…); Gemini classifies the merchants the rules don't know. Anything uncertain is flagged for you to review. |
| 🗂️ **Merchant dictionary** | See every merchant the app has learned, correct a category once, and it applies everywhere. |
| 📊 **Dashboard** | Income, spending and savings at a glance, with charts across all your months. |
| 📅 **Monthly breakdown** | Drill into any month by category or sub-category, with AI-written insights for that month. |
| 🔁 **Subscriptions** | Recurring charges and EMIs are detected automatically. |
| 🧭 **Strategic audit** | A whole-picture review of your finances with concrete suggestions. |
| 🎯 **Goals** | Set a savings goal, pick a risk level (cash/FD, hybrid, equity) and see how long it will take. New statements update your progress. |
| 💬 **Finneas, the chat assistant** | Ask things like *"How much did I spend on food in March?"* or *"Which month did I spend the most?"*. Finneas answers using tools that query your real data, and says so plainly when it can't answer instead of guessing. |
| 👤 **Accounts and demo** | Sign up for your own private account, or click **Try the demo** to explore with a year of sample data and a guided walkthrough. |

## How it works

```
 Your statement (PDF / CSV / Excel)
            │
            ▼
   ┌─────────────────┐     ┌──────────────────────┐
   │ Universal parser │ ──▶ │ Categorizer          │
   │ (one per format) │     │ rules  →  Gemini     │
   └─────────────────┘     │  →  review flags     │
                            └──────────┬───────────┘
                                       ▼
                    ┌───────────────────────────────────┐
                    │ Analytics engine (pandas)          │
                    │ totals · trends · subscriptions ·  │
                    │ goals · monthly insights · audit   │
                    └──────────────┬────────────────────┘
                                   ▼
             Dashboard  ·  Spend  ·  Goals  ·  Finneas chat
```

**Deployed setup:** the browser only talks to the Next.js app on Vercel. Vercel forwards `/api/*` calls to the FastAPI backend on Railway with a shared secret, so the backend can't be called directly. Accounts, statements and chats live on a Railway volume.

## Tech stack

| Part | Built with |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Recharts, Lucide icons |
| Backend | FastAPI, pandas, NumPy, pdfplumber, pypdf, openpyxl, xlrd |
| AI | Google Gemini (merchant classification, insights, chat) |
| Auth | Argon2id password hashing, HttpOnly session cookies, SQLite |
| Hosting | Vercel (frontend), Railway with Docker (backend) |

## Getting started

### What you need

- Python 3.11
- Node.js 20 or later
- A Google Gemini API key (the app still runs without one, but AI features fall back to rule-based answers)

### 1. Clone the repo

```bash
git clone https://github.com/Raghava-Sriman/FIN.git
cd FIN
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\python -m pip install -r requirements-dev.txt
# macOS / Linux
.venv/bin/python -m pip install -r requirements-dev.txt
```

Create `backend/.env` with your Gemini settings:

```env
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=your-gemini-model-name
```

Then run it:

```bash
# Windows
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
# macOS / Linux
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. Click **Try the demo**, or sign up and upload a statement. No statement handy? Load one of the sample statements from the app.

> **macOS / Linux shortcut:** `./start.sh` starts both servers and, if you have `cloudflared` installed, prints a link you can open on your phone. `./stop.sh` stops everything.

## Sample data

[`sample_statements/`](sample_statements/) has five synthetic one-year statements for made-up people with different incomes and habits. They contain no real banking data. You can load any of them from inside the app.

## Tests and evals

From `backend/`:

```bash
python -m unittest discover -s tests -v     # unit tests
python evals/run_evals.py --skip-ai         # categorization accuracy, no Gemini calls
python evals/run_evals.py                   # full run, including Finneas answer accuracy
```

The eval suite measures how accurately transactions are categorized and whether Finneas reports numbers correctly, using a synthetic student statement with known answers. See [backend/evals/README.md](backend/evals/README.md).

## Deployment

The frontend deploys to Vercel and the backend to Railway (Dockerfile and `railway.json` are included). The full step-by-step guide, environment variables and troubleshooting table are in **[DEPLOY.md](DEPLOY.md)**.

## Project structure

```
FIN/
├── backend/
│   ├── main.py                    # FastAPI app and all API routes
│   ├── app/
│   │   ├── config.py              # settings read from environment variables
│   │   └── services/
│   │       ├── parser/            # statement parsers (PDF, CSV, Excel)
│   │       ├── categorizer/       # rules + Gemini merchant classification
│   │       ├── analytics/         # totals, monthly insights, strategic audit
│   │       ├── goals/             # goal tracking and simulation
│   │       ├── chat/              # Finneas agent and its data tools
│   │       ├── auth/              # accounts, demo, rate limits, AI quotas
│   │       └── session/           # per-account data storage
│   ├── tests/                     # unit tests
│   └── evals/                     # accuracy evaluations
├── frontend/
│   └── src/
│       ├── app/                   # main page and layout
│       ├── components/            # login, walkthrough, Finneas mascot and chat
│       └── proxy.ts               # forwards /api/* to the backend
├── sample_statements/             # synthetic demo statements
├── Dockerfile                     # backend image for Railway
├── railway.json                   # Railway deploy settings
└── DEPLOY.md                      # deployment guide
```

## Privacy

- Each account's statements, chats and goals are stored separately and are visible only to that account.
- Passwords are hashed with Argon2id; sessions use HttpOnly, Secure cookies.
- Merchant names and transaction details are sent to Gemini to classify merchants and answer chat questions. Keep that in mind before uploading real statements to a deployed instance.
- Demo accounts are deleted automatically after 24 hours.

## More documentation

| File | What's in it |
|---|---|
| [DEPLOY.md](DEPLOY.md) | Deploying to Vercel and Railway |
| [plan.md](plan.md) | Original product plan and technical specification |
| [goal_tracking_architecture.md](goal_tracking_architecture.md) | How goals are tracked as new statements arrive |
| [UI_guidelines.md](UI_guidelines.md) | Design guidelines for the interface |
| [journal.md](journal.md) | Development log and design decisions |
