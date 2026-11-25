# Deploying FinSight

The frontend (Next.js) runs on **Vercel**. The backend (FastAPI) runs on **Railway** with a persistent volume.

```
Browser ──HTTPS──▶ Vercel (Next.js)  ──HTTPS + proxy secret──▶  Railway (FastAPI) ──▶ Volume /data
                   serves the app and                            accounts, uploads,
                   forwards /api/* (src/proxy.ts)                auth.db, demo template
```

- The browser only ever talks to your Vercel domain, so the login cookie is first-party and there is no CORS.
- The backend only answers requests that carry the shared proxy secret, which only Vercel knows. Calling the Railway URL directly gets `403` (except the health check).

Do the steps in order: the Vercel setup needs the Railway URL.

---

## 0. Before you start

You need:

- The GitHub repo `Raghava-Sriman/FIN` (private is fine; both Railway and Vercel can read private repos once you authorize them).
- A Railway account and a Vercel account, both logged in with GitHub.
- Your Gemini API key and model name. They are the `GEMINI_API_KEY` and `GEMINI_MODEL` values in your local `backend/.env`. Copy them from there; never commit that file.

### Generate the proxy secret

Run this once on your computer and keep the output somewhere safe (a password manager). You will paste the **same value** into Railway and Vercel.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

It must be at least 32 characters; the command above gives 64. The backend refuses to start in production without it.

---

## 1. Backend on Railway

### 1.1 Create the service

1. In Railway, click **New Project** → **Deploy from GitHub repo** → choose `Raghava-Sriman/FIN`.
   If the repo isn't listed, use **Configure GitHub App** to give Railway access to it.
2. Leave the **Root Directory** empty (the repository root). Railway picks up `railway.json` from there, which tells it to:
   - build with the `Dockerfile`
   - health-check `/api/healthz`
   - run exactly **1 replica**
3. The first deploy may start right away and fail or warn because the variables aren't set yet. That's expected; continue below.

### 1.2 Attach a volume

1. Open the service, then add a volume: right-click the service on the project canvas → **Attach Volume** (or use the command palette, `Ctrl/⌘ + K` → "volume").
2. Set the **mount path** to `/data`.

Everything the app writes lives in this volume: accounts, `auth.db`, uploaded statements, chats, goals and the demo template. Without the volume, all of that is lost on every redeploy, and the logs show a `WARNING: no Railway volume is attached`.

### 1.3 Set the variables

In the service, open **Variables** and add:

| Variable | Value | Notes |
|---|---|---|
| `FINSIGHT_ENV` | `production` | Turns off `/docs`, `/redoc`, `/openapi.json` and enforces the safety checks. (The Dockerfile also sets this; setting it here makes it visible.) |
| `FINSIGHT_DATA_DIR` | `/data` | Must match the volume mount path. |
| `FINSIGHT_PROXY_SECRET` | *the secret from step 0* | Same value as on Vercel. |
| `GEMINI_API_KEY` | *your key* | From `backend/.env`. |
| `GEMINI_MODEL` | *your model name* | From `backend/.env`. |
| `FINSIGHT_DAILY_AI_LIMIT` | `40` | AI actions per account per day (UTC). Optional; 40 is the default. |
| `FINSIGHT_GLOBAL_DAILY_AI_LIMIT` | `1000` | AI actions across all accounts per day. Optional; 1000 is the default. |

Do **not** set:

- `PORT`: Railway sets it, and the app listens on it.
- `FINSIGHT_INSECURE_COOKIES`: the backend refuses to start with it in production.
- `FINSIGHT_CORS_ORIGINS`: not needed, because the browser never calls the backend directly.

Saving the variables triggers a redeploy.

### 1.4 Give it a public URL

1. Open the service's **Settings** → **Networking** → **Generate Domain**.
2. If Railway asks for a port, use the port shown in the deploy logs line `Uvicorn running on http://0.0.0.0:<port>`. That is the `PORT` Railway assigned.
3. Copy the URL, for example `https://fin-production-1234.up.railway.app`. You need it for Vercel.

### 1.5 Check the backend

Watch the **Deploy Logs**. A good start looks like:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:<port>
[finMan Intelligence] Batch classifying ... merchants with Gemini...
```

The last line is the demo template being built in `/data` on first start. It happens once and takes a few seconds.

Then, from your computer (replace the URL with yours):

```bash
curl https://YOUR-RAILWAY-URL/api/healthz     # expect: {"status":"ok"}
curl -i https://YOUR-RAILWAY-URL/api/samples  # expect: HTTP 403 (no proxy secret)
curl -i https://YOUR-RAILWAY-URL/docs         # expect: HTTP 403
```

If the service keeps restarting, check the logs for `Unsafe production configuration`. It means `FINSIGHT_PROXY_SECRET` is missing or too short.

---

## 2. Frontend on Vercel

### 2.1 Create the project

1. In Vercel, click **Add New…** → **Project** → import `Raghava-Sriman/FIN`.
2. Set **Root Directory** to `frontend`. Vercel detects Next.js; leave the build settings at their defaults.

### 2.2 Set the variables

Under **Environment Variables** (before the first deploy, or later in **Settings → Environment Variables**), add:

| Variable | Value | Environments |
|---|---|---|
| `BACKEND_URL` | your Railway URL, e.g. `https://fin-production-1234.up.railway.app` (no trailing slash) | Production (and Preview if you want preview deployments to work) |
| `FINSIGHT_PROXY_SECRET` | *the same secret as on Railway* | Same as above |

Important:

- Do **not** add a `NEXT_PUBLIC_` prefix. These two variables are only read on the server, by `src/proxy.ts`, and never reach the browser.
- Variables are read when each request comes in, but Vercel only applies changed variables to **new** deployments. After changing one, redeploy: **Deployments** → latest → **Redeploy**.

### 2.3 Deploy

Click **Deploy**. When it finishes, open the production URL, for example `https://fin-xyz.vercel.app`.

---

## 3. Check that everything works

Do these on the live site.

1. **Login page.** The site opens on the login page with the Demo account card.
2. **Demo.** Click **Try the demo**. The app loads with the "Demo account" banner, and the walkthrough starts.
3. **Cookie.** In browser DevTools → **Application** (Chrome/Edge) or **Storage** (Firefox) → **Cookies** → your Vercel domain, `finsight_session` should show:
   - **HttpOnly** ✓
   - **Secure** ✓
   - **SameSite** `Lax`
4. **Accounts.** Sign up for a real account, upload a statement or load a sample, then log out and log back in. Your data should still be there.
5. **Persistence.** In Railway, redeploy the backend (**Deployments** → latest → **Redeploy**), then log in again. Your account and data must survive. If they don't, the volume isn't attached at `/data` (see 1.2).
6. **Direct backend access is blocked:**
   ```bash
   curl -i https://YOUR-RAILWAY-URL/api/samples   # 403
   ```
7. **Chat.** Ask Finneas a question. You should get an AI answer. With the default limit, an account gets 40 AI actions per day.

---

## 4. Running it

### Keep one replica

Do not scale the backend beyond **1 replica** or add workers. Three things live in the single process:

- the login, sign-up and demo **rate limits** (in memory, reset on each deploy)
- the **hourly cleanup** that deletes demo accounts older than 24 hours (it also runs at every startup)
- SQLite (`/data/auth.db`), which expects one writer process

A Railway volume can only be attached to one replica anyway.

### AI limits

- An "AI action" is one chat message, one monthly-insights generation, one strategic-audit generation, or one merchant classification for an upload, sample load or reset.
- When an account or the whole site reaches its daily limit, nothing breaks:
  - chat answers with the rule-based assistant and a note
  - insights and the audit show rule-based summaries with a note
  - unknown merchants are flagged for review
- Counters reset at midnight UTC.
- To change the limits, edit `FINSIGHT_DAILY_AI_LIMIT` / `FINSIGHT_GLOBAL_DAILY_AI_LIMIT` on Railway. The service redeploys.

### Rotating the proxy secret

1. Generate a new secret (step 0).
2. Update `FINSIGHT_PROXY_SECRET` on **both** Railway and Vercel.
3. Redeploy both. Between the two redeploys, API calls fail with 403 for a minute or two.

### Rebuilding the demo data

The demo template is built once in `/data/demo_template`. If Gemini was unavailable at that moment, the demo's merchants keep rule-based categories (many flagged "needs review"). To rebuild it:

1. Delete `/data/demo_template`. One way is the Railway CLI: `railway ssh`, then `rm -rf /data/demo_template`.
2. Restart the service. Existing demo accounts are unaffected; new demo logins get the rebuilt data.

The template also rebuilds automatically if `sample_statements/vikram_malhotra_1year_statement.csv` changes.

### Backups

Your users' data lives only in the Railway volume. Turn on volume backups in Railway (the volume's **Backups** tab) if you want point-in-time copies.

### Limits to know about

- **Uploads.** Vercel limits request bodies to about 4.5 MB. The app keeps a statement upload batch under 4 MB and chat attachments under 3 MB per message, with a clear message if a file is too large.
- **Rate limits.** They use the visitor IP that Vercel reports in `x-forwarded-for`, forwarded to the backend by the proxy. They reset whenever the backend redeploys.

---

## 5. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Every API call returns **403** | `FINSIGHT_PROXY_SECRET` differs between Vercel and Railway, or Vercel wasn't redeployed after changing it. |
| Login seems to work but you're immediately back on the login page | The cookie wasn't stored. Make sure you're on the `https://` Vercel URL, and that `FINSIGHT_INSECURE_COOKIES` isn't set. |
| Vercel shows **502/504** for API calls | `BACKEND_URL` is wrong (typo, trailing slash, `http://` instead of `https://`) or the Railway service is down. Check Railway logs and `/api/healthz`. |
| Railway service crash-loops with `Unsafe production configuration` | `FINSIGHT_PROXY_SECRET` missing or shorter than 32 characters, or `FINSIGHT_INSECURE_COOKIES` set. |
| Accounts disappear after a redeploy | No volume, or `FINSIGHT_DATA_DIR` doesn't match the mount path. The logs warn about this at startup. |
| Chat always says the AI limit is reached | Today's per-account or global limit was used up; wait for midnight UTC or raise the limits. |
| AI answers are all rule-based but the limit isn't reached | `GEMINI_API_KEY`/`GEMINI_MODEL` missing or wrong on Railway, or Gemini is temporarily unavailable (look for `status 503` in the logs). |

---

## 6. Local development (unchanged)

```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m uvicorn main:app --host 127.0.0.1 --port 8000

# frontend (another terminal)
cd frontend && npm ci && npm run dev
```

Locally:

- No proxy secret is needed.
- Data goes to `vault_storage/`.
- `BACKEND_URL` defaults to `http://127.0.0.1:8000`.

Run the backend tests with `python -m unittest discover -s tests` from `backend/`.

## Environment variable reference

| Where | Variable | Required | Default |
|---|---|---|---|
| Railway | `FINSIGHT_ENV` | yes (`production`) | `production` in the Docker image |
| Railway | `FINSIGHT_DATA_DIR` | yes (`/data`) | `/data` in the Docker image; `vault_storage/` locally |
| Railway + Vercel | `FINSIGHT_PROXY_SECRET` | yes, same value, 32+ characters | none |
| Railway | `GEMINI_API_KEY`, `GEMINI_MODEL` | yes, for AI features | none |
| Railway | `FINSIGHT_DAILY_AI_LIMIT` | no | `40` |
| Railway | `FINSIGHT_GLOBAL_DAILY_AI_LIMIT` | no | `1000` |
| Railway | `PORT` | set by Railway | `8000` |
| Vercel | `BACKEND_URL` | yes | `http://127.0.0.1:8000` |
| Railway (avoid) | `FINSIGHT_CORS_ORIGINS` | no | off |
| local only | `FINSIGHT_INSECURE_COOKIES=1` | plain-HTTP LAN testing only; rejected in production | off |
