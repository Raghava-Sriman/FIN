import asyncio
import hashlib
import os
import secrets
import shutil
import json
import threading
import uuid
import datetime
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import Depends, FastAPI, UploadFile, File, Request, Response, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.analytics.engine import (
    calculate_monthly_metrics,
    detect_recurring_charges,
    simulate_goal_timeline,
    calculate_financial_health_score
)
from app.services.analytics.monthly_insights import generate_monthly_insights
from app.services.analytics.strategic_audit import generate_strategic_audit
from app.services.parser.universal_parser import parse_statement_file
from app.services.categorizer.rules import clean_narration
from app.services.categorizer.merchant_intelligence import (
    load_merchant_dictionary,
    save_merchant_dictionary,
    resolve_unknown_merchants_with_intelligence,
    normalize_merchant_key,
    AVAILABLE_SUBCATEGORIES,
    SUB_TO_MACRO,
    map_to_standard_category
)
from app.services.goals.engine import (
    get_cashflow_context,
    load_user_goals,
    get_default_goals,
    save_user_goals,
    add_user_goal,
    delete_user_goal,
    simulate_goal_trajectory
)
from app import config
from app.services.session.vault import SESSION_COOKIE, get_authenticated_user, resolve_vault
from app.services.auth.store import AuthError, authenticate, create_session, create_user, delete_session, init_db, normalize_username
from app.services.auth.demo import DEMO_PASSWORD, DEMO_SAMPLE_ID, DEMO_USERNAME, cleanup_expired, create_demo_account, delete_account, ensure_template
from app.services.auth.rate_limit import client_ip, demo_logins, login_failures, registrations
from app.services.auth.ai_quota import AiGate, prune_old_usage, try_consume, usage as ai_usage
from app.services.chat.agent import (
    load_threads,
    get_thread,
    create_new_thread,
    delete_thread,
    run_finneas_chat
)

DEMO_CLEANUP_INTERVAL_SECONDS = 3600


async def _cleanup_loop():
    """Deletes expired demo accounts and sessions at startup and then hourly."""
    while True:
        try:
            removed = await asyncio.to_thread(cleanup_expired)
            await asyncio.to_thread(prune_old_usage)
            if removed:
                print(f"[finMan Auth] Deleted {removed} expired demo account(s)")
        except Exception as e:
            print(f"[finMan Auth] Demo cleanup failed: {e}")
        await asyncio.sleep(DEMO_CLEANUP_INTERVAL_SECONDS)


def _warm_demo_template():
    try:
        ensure_template(build_demo_template)
    except Exception as e:
        print(f"[finMan Auth] Demo template will be built on first demo login: {e}")


def _warn_if_data_dir_not_persistent():
    """On Railway, data outside the mounted volume is lost on every redeploy."""
    if not os.environ.get("RAILWAY_ENVIRONMENT"):
        return
    mount = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if not mount:
        print("[finMan] WARNING: no Railway volume is attached; accounts and uploads will be lost on redeploy.")
    elif os.path.commonpath([os.path.abspath(mount), config.DATA_DIR]) != os.path.abspath(mount):
        print(f"[finMan] WARNING: FINSIGHT_DATA_DIR ({config.DATA_DIR}) is not inside the volume mounted at {mount}.")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _warn_if_data_dir_not_persistent()
    init_db()
    cleanup_task = asyncio.create_task(_cleanup_loop())
    if os.environ.get("FINSIGHT_SKIP_DEMO_WARMUP") != "1":
        threading.Thread(target=_warm_demo_template, daemon=True).start()
    yield
    cleanup_task.cancel()


# Every API route requires a logged-in session except these
PUBLIC_API_PATHS = {"/api/auth/login", "/api/auth/register", "/api/auth/demo", "/api/samples", "/api/healthz"}
# Reachable without the proxy secret, so the hosting platform can health-check the service directly
PROXY_EXEMPT_PATHS = {"/api/healthz"}
PROXY_SECRET_HEADER = "x-finsight-proxy-secret"


def require_login(request: Request):
    """Runs before every route (and before body validation), so unauthenticated requests always get 401."""
    if request.url.path not in PUBLIC_API_PATHS:
        get_authenticated_user(request)


config.validate()

app = FastAPI(
    title="FinSight AI Core Engine",
    version="2.0.0",
    lifespan=lifespan,
    dependencies=[Depends(require_login)],
    # API docs are only served outside production
    docs_url=None if config.IS_PRODUCTION else "/docs",
    redoc_url=None if config.IS_PRODUCTION else "/redoc",
    openapi_url=None if config.IS_PRODUCTION else "/openapi.json",
)
init_db()


@app.middleware("http")
async def require_proxy_secret(request: Request, call_next):
    """
    When FINSIGHT_PROXY_SECRET is set (always in production), only requests forwarded by the
    frontend proxy are served; calling the backend URL directly is refused.
    """
    if config.PROXY_SECRET and request.url.path not in PROXY_EXEMPT_PATHS:
        supplied = request.headers.get(PROXY_SECRET_HEADER, "")
        if not secrets.compare_digest(supplied.encode(), config.PROXY_SECRET.encode()):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


# The frontend calls the API same-origin through the Next.js proxy, so cross-origin
# access is off unless explicitly allowed (comma-separated origins).
if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

COOKIE_SECURE = config.COOKIE_SECURE


@app.get("/api/healthz")
def healthz():
    """Liveness check for the hosting platform. Reveals nothing about accounts or data."""
    return {"status": "ok"}


# ==========================================
# AUTHENTICATION APIS
# ==========================================

class CredentialsRequest(BaseModel):
    username: str
    password: str


def _user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {"username": user["username"], "is_demo": user["is_demo"], "expires_at": user.get("expires_at")}


def _start_session(response: Response, user: Dict[str, Any]) -> Dict[str, Any]:
    session = create_session(user)
    response.set_cookie(
        SESSION_COOKIE,
        session["token"],
        max_age=session["max_age"],
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"status": "success", "user": _user_payload(user)}


def _check_rate_limit(limiter, key):
    retry_after = limiter.retry_after(key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Please wait and try again.",
            headers={"Retry-After": str(retry_after)},
        )


@app.post("/api/auth/register")
def register_endpoint(req: CredentialsRequest, request: Request, response: Response):
    key = client_ip(request)
    _check_rate_limit(registrations, key)
    try:
        user = create_user(req.username, req.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    registrations.record(key)
    return _start_session(response, user)


@app.post("/api/auth/demo")
def demo_login_endpoint(request: Request, response: Response):
    key = client_ip(request)
    _check_rate_limit(demo_logins, key)
    demo_logins.record(key)
    user = create_demo_account(build_demo_template)
    return _start_session(response, user)


@app.post("/api/auth/login")
def login_endpoint(req: CredentialsRequest, request: Request, response: Response):
    username = normalize_username(req.username)
    if username == DEMO_USERNAME and secrets.compare_digest(req.password.encode(), DEMO_PASSWORD.encode()):
        return demo_login_endpoint(request, response)

    key = (client_ip(request), username)
    _check_rate_limit(login_failures, key)
    user = authenticate(username, req.password)
    if not user:
        login_failures.record(key)
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    login_failures.reset(key)
    return _start_session(response, user)


@app.post("/api/auth/logout")
def logout_endpoint(request: Request, response: Response):
    user = get_authenticated_user(request)
    delete_session(request.cookies.get(SESSION_COOKIE, ""))
    if user["is_demo"]:
        delete_account(user["id"])
    response.delete_cookie(SESSION_COOKIE, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    return {"status": "logged_out"}


@app.get("/api/auth/me")
def me_endpoint(request: Request):
    user = get_authenticated_user(request)
    return {"user": _user_payload(user), "ai_usage": ai_usage(user["id"])}


def _ai_gate(request: Request) -> AiGate:
    return AiGate(get_authenticated_user(request)["id"])


def load_manifest(vault: str) -> List[Dict[str, Any]]:
    manifest_path = os.path.join(vault, "manifest.json")
    if not os.path.exists(manifest_path):
        return []
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_manifest(manifest: List[Dict[str, Any]], vault: str):
    manifest_path = os.path.join(vault, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def rebuild_active_ledger(vault: str) -> Optional[pd.DataFrame]:
    """
    Stitches all active statements in the user's vault into a continuous,
    chronologically sorted, deduplicated master ledger.
    """
    manifest = load_manifest(vault)
    active_path = os.path.join(vault, "active_unified_ledger.csv")
    
    if not manifest:
        if os.path.exists(active_path):
            try:
                os.remove(active_path)
            except Exception:
                pass
        return None
        
    dfs = []
    for item in manifest:
        csv_file = os.path.join(vault, item.get("stored_file", ""))
        if os.path.exists(csv_file):
            try:
                df_item = pd.read_csv(csv_file)
                df_item["_statement_id"] = item["id"]
                df_item["_statement_filename"] = item["filename"]
                dfs.append(df_item)
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
            
    if not dfs:
        if os.path.exists(active_path):
            try:
                os.remove(active_path)
            except Exception:
                pass
        return None
        
    unified = pd.concat(dfs, ignore_index=True)
    unified['date'] = pd.to_datetime(unified['date'], errors='coerce')
    unified = unified.dropna(subset=['date']).sort_values('date').reset_index(drop=True)
    unified['date'] = unified['date'].dt.strftime('%Y-%m-%d')
    
    unified['debit'] = pd.to_numeric(unified.get('debit', 0.0), errors='coerce').fillna(0.0)
    unified['credit'] = pd.to_numeric(unified.get('credit', 0.0), errors='coerce').fillna(0.0)
    
    unified = unified.drop_duplicates(subset=['date', 'narration', 'debit', 'credit']).reset_index(drop=True)
    
    running = float(unified['balance'].iloc[0]) if 'balance' in unified.columns and not unified['balance'].isna().all() else 50000.0
    balances = []
    curr = running
    for idx, row in unified.iterrows():
        if idx == 0 and 'balance' in unified.columns and not pd.isna(row['balance']) and float(row['balance']) != 0.0:
            curr = float(row['balance'])
        else:
            curr = curr + float(row['credit']) - float(row['debit'])
        balances.append(round(curr, 2))
    unified['balance'] = balances
    
    merchant_dict = load_merchant_dictionary(vault)
    cats = [
        clean_narration(
            r['narration'], 
            float(r.get('debit', 0.0) or 0.0), 
            float(r.get('credit', 0.0) or 0.0),
            merchant_dict=merchant_dict
        ) 
        for _, r in unified.iterrows()
    ]
    unified['merchant'] = [c[0] for c in cats]
    unified['category'] = [c[1] for c in cats]
    unified['sub_category'] = [c[2] for c in cats]
    
    unified.to_csv(active_path, index=False)
    return unified

def get_current_df(vault: str) -> Optional[pd.DataFrame]:
    active_path = os.path.join(vault, "active_unified_ledger.csv")
    if not os.path.exists(active_path):
        return rebuild_active_ledger(vault)
    try:
        df = pd.read_csv(active_path)
        return df
    except Exception:
        return None

def get_display_name(vault: str) -> str:
    manifest = load_manifest(vault)
    if not manifest:
        return "No Statements Uploaded"
    if len(manifest) == 1:
        return manifest[0]["filename"]
    short_names = [m["filename"].replace('.pdf', '').replace('.csv', '') for m in manifest]
    return f"{len(manifest)} Statements ({', '.join(short_names)})"

@app.get("/api/health")
def health_check(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    return {
        "status": "online",
        "has_statement": df is not None and len(df) > 0,
        "active_statement": get_display_name(vault)
    }

# ==========================================
# OVERVIEW & ANALYTICS APIS
# ==========================================

@app.get("/api/overview")
def get_overview(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None or len(df) == 0:
        return {"has_statement": False}
        
    if "sub_category" not in df.columns:
        df["sub_category"] = df.get("category", "Discretionary")
    if "merchant" not in df.columns:
        df["merchant"] = df.get("narration", "").apply(lambda n: str(n)[:25])

    monthly = calculate_monthly_metrics(df)
    
    total_inflow = float(df['credit'].sum())
    total_outflow = float(df['debit'].sum())
    net_savings = total_inflow - total_outflow
    # Safe bounded cumulative savings rate (-100% to +100%)
    if total_inflow > 0:
        overall_savings_rate = round((net_savings / total_inflow) * 100, 1)
        safe_savings_rate = max(-100.0, min(100.0, overall_savings_rate))
    else:
        safe_savings_rate = -100.0 if total_outflow > 0 else 0.0
    
    has_balance = 'balance' in df.columns and len(df) > 0 and pd.notna(df['balance'].iloc[-1])
    end_balance = float(df['balance'].iloc[-1]) if has_balance else max(0.0, net_savings)
    
    score = calculate_financial_health_score(
        savings_rate=safe_savings_rate,
        emergency_fund_months=round(end_balance / (total_outflow / 12.0), 1) if total_outflow > 0 else 0.0,
        dti_ratio=0.24
    )
    
    cat_summary = df[df['debit'] > 0].groupby('category')['debit'].sum().sort_values(ascending=False).reset_index()
    categories_data = [
        {"name": row['category'], "value": round(float(row['debit']), 2)}
        for _, row in cat_summary.iterrows()
    ]
    
    subcat_summary = df[df['debit'] > 0].groupby('sub_category')['debit'].sum().sort_values(ascending=False).reset_index()
    top_subcats = subcat_summary.head(7)
    others_sum = float(subcat_summary.iloc[7:]['debit'].sum()) if len(subcat_summary) > 7 else 0.0
    
    subcategories_data = [
        {"name": row['sub_category'], "value": round(float(row['debit']), 2)}
        for _, row in top_subcats.iterrows()
    ]
    if others_sum > 0:
        subcategories_data.append({"name": "Other Living Expenses", "value": round(others_sum, 2)})
    
    monthly_data = monthly.to_dict(orient="records")
    return {
        "has_statement": True,
        "total_inflow": total_inflow,
        "total_outflow": total_outflow,
        "net_savings": net_savings,
        "end_balance": end_balance,
        "savings_rate": safe_savings_rate,
        "health_score": score,
        "monthly_trend": monthly_data,
        "monthly_metrics": monthly_data,
        "active_file": get_display_name(vault),
        "category_breakdown": categories_data,
        "subcategory_breakdown": subcategories_data,
        "transactions_count": len(df),
        "statement_period": f"{df['date'].min()} to {df['date'].max()}"
    }

@app.get("/api/months")
def get_available_months(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {"months": []}
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    months = sorted(df['year_month'].unique().tolist(), reverse=True)
    return {"months": months}

@app.get("/api/month-detail/{year_month}")
def get_month_detail(year_month: str, request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {"error": "No statement loaded"}
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    
    m_df = df[df['year_month'] == year_month].copy()
    if m_df.empty:
        return {"error": "Month not found"}
        
    if "sub_category" not in m_df.columns:
        m_df["sub_category"] = m_df.get("category", "Discretionary")
        
    inflow = float(m_df['credit'].sum())
    outflow = float(m_df['debit'].sum())
    savings = inflow - outflow
    savings_rate = round((savings / inflow) * 100, 1) if inflow > 0 else 0.0
    
    debits = m_df[m_df['debit'] > 0]
    subcats = debits.groupby('sub_category')['debit'].sum().sort_values(ascending=False).reset_index()
    subcat_breakdown = [
        {"name": row['sub_category'], "value": round(float(row['debit']), 2)}
        for _, row in subcats.iterrows()
    ]
    
    m_df['day'] = m_df['date'].dt.strftime('%d %b')
    daily_spend = m_df[m_df['debit'] > 0].groupby('day')['debit'].sum().reset_index()
    daily_trend = [
        {"day": row['day'], "spend": round(float(row['debit']), 2)}
        for _, row in daily_spend.iterrows()
    ]
    
    txs = m_df.sort_values(by='date', ascending=False).to_dict(orient='records')
    for t in txs:
        t['date'] = str(t['date'])[:10]
        
    return {
        "month": year_month,
        "inflow": inflow,
        "outflow": outflow,
        "net_savings": savings,
        "savings_rate": savings_rate,
        "transaction_count": len(m_df),
        "subcategories": subcat_breakdown,
        "daily_trend": daily_trend,
        "transactions": txs
    }

@app.get("/api/month-insights/{year_month}")
@app.post("/api/month-insights/{year_month}")
def get_month_insights(year_month: str, request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {"error": "No statement loaded"}
    gate = _ai_gate(request)
    result = generate_monthly_insights(df, year_month, use_ai=gate())
    result["ai_limited"] = gate.denied
    return result

@app.get("/api/statements-list")
def get_statements_list(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    manifest = load_manifest(vault)
    if df is None or not manifest:
        return {"has_statement": False, "statements": []}
    return {
        "has_statement": True,
        "active_statement": get_display_name(vault),
        "total_rows": len(df),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "balance": float(df['balance'].iloc[-1]),
        "statements": manifest
    }

@app.delete("/api/statements/{statement_id}")
def delete_statement(statement_id: str, request: Request):
    vault = resolve_vault(request)
    manifest = load_manifest(vault)
    target = None
    remaining = []
    for item in manifest:
        if item["id"] == statement_id:
            target = item
        else:
            remaining.append(item)
            
    if not target:
        return {"status": "error", "message": "Statement not found"}
        
    stored_path = os.path.join(vault, target.get("stored_file", ""))
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except Exception:
            pass
            
    save_manifest(remaining, vault)
    unified_df = rebuild_active_ledger(vault)
    has_statement = unified_df is not None and len(unified_df) > 0
    
    return {
        "status": "success",
        "deleted_id": statement_id,
        "deleted_filename": target.get("filename"),
        "has_statement": has_statement,
        "remaining_count": len(remaining),
        "statements": remaining
    }

AUDIT_CACHE_FILE = "strategic_audit_cache.json"


def _statements_signature(vault: str) -> str:
    """Changes whenever statements are added or removed (not on category edits)."""
    ids = sorted(item.get("id", "") for item in load_manifest(vault))
    return hashlib.sha256("|".join(ids).encode()).hexdigest()


def _strategic_audit(request: Request, force_refresh: bool) -> Dict[str, Any]:
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {}
    cache_path = os.path.join(vault, AUDIT_CACHE_FILE)
    signature = _statements_signature(vault)
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if cached.get("signature") == signature:
                return cached["result"]
        except (OSError, ValueError, KeyError):
            pass

    gate = _ai_gate(request)
    try:
        result = generate_strategic_audit(df, use_ai=gate())
    except Exception as e:
        print(f"[finMan] Strategic audit error: {e}. Falling back to rule engine.")
        return detect_recurring_charges(df)
    if gate.denied:
        # Rule-based result: not cached, so the AI audit runs once the limit resets
        return {**result, "ai_limited": True}
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump({"signature": signature, "result": result}, fh)
    return result


@app.get("/api/subscriptions")
@app.get("/api/strategic-audit")
def get_subscriptions(request: Request):
    return _strategic_audit(request, force_refresh=False)


@app.post("/api/strategic-audit")
def refresh_strategic_audit(request: Request):
    return _strategic_audit(request, force_refresh=True)

# ----------------- GOALS & WHAT-IF SIMULATOR ENDPOINTS -----------------

class CreateGoalRequest(BaseModel):
    id: Optional[str] = None
    title: str
    category: str = "CUSTOM"
    target_amount: float
    monthly_allocation: float
    lumpsum_infusion: float = 0.0
    target_return_cagr: float = 7.0
    description: Optional[str] = ""

class AdvancedGoalSimRequest(BaseModel):
    target_amount: float
    monthly_allocation: float = 0.0
    discretionary_cuts: Dict[str, float] = {}
    lumpsum_infusion: float = 0.0
    return_cagr: float = 7.0
    inflation_rate: float = 0.0

@app.get("/api/goals")
def get_user_goals_endpoint(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    context = get_cashflow_context(df)
    goals = load_user_goals(vault, df)
    templates = get_default_goals(vault, df)
    return {
        "cashflow_context": context,
        "goals": goals,
        "templates": templates
    }

@app.post("/api/goals")
def create_or_update_goal_endpoint(req: CreateGoalRequest, request: Request):
    vault = resolve_vault(request)
    goal_data = req.dict()
    saved = add_user_goal(goal_data, vault)
    return {"status": "success", "goal": saved}

@app.delete("/api/goals/{goal_id}")
def delete_goal_endpoint(goal_id: str, request: Request):
    vault = resolve_vault(request)
    deleted = delete_user_goal(goal_id, vault)
    return {"status": "success" if deleted else "not_found"}

@app.post("/api/goals/simulate")
def simulate_goal_advanced_endpoint(req: AdvancedGoalSimRequest, request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    context = get_cashflow_context(df)
    surplus = context["avg_monthly_surplus"] if context.get("has_data") else 0.0

    return simulate_goal_trajectory(
        target_amount=req.target_amount,
        monthly_allocation=req.monthly_allocation,
        discretionary_cuts=req.discretionary_cuts,
        lumpsum=req.lumpsum_infusion,
        return_cagr=req.return_cagr,
        inflation_rate=req.inflation_rate,
        avg_monthly_surplus=surplus
    )

# Backward-compatible wrapper for legacy calls
class GoalSimRequest(BaseModel):
    target_amount: float
    monthly_dining_cut: float = 0.0
    cancel_duplicate_subs: bool = False
    cancel_zombie_gym: bool = False

@app.post("/api/simulate-goal")
def simulate_goal(req: GoalSimRequest, request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    context = get_cashflow_context(df)
    surplus = context["avg_monthly_surplus"] if context["has_data"] else 45000.0
    
    additional_cuts = {}
    if req.monthly_dining_cut > 0:
        additional_cuts["Dining & Delivery"] = req.monthly_dining_cut
    if req.cancel_duplicate_subs:
        additional_cuts["Subscriptions"] = 119.0
    if req.cancel_zombie_gym:
        additional_cuts["Gym Membership"] = 2499.0
        
    return simulate_goal_trajectory(
        target_amount=req.target_amount,
        monthly_allocation=surplus,
        discretionary_cuts=additional_cuts,
        return_cagr=7.0
    )

def ingest_statement_file(
    source_path: str,
    display_name: str,
    vault: str,
    is_demo: bool = False,
    skipped_rows: Optional[List[Dict[str, Any]]] = None,
    ai_gate: Optional[AiGate] = None
) -> Optional[Dict[str, Any]]:
    """
    Parses one statement file, resolves its merchants, and stores it in the vault.
    Returns the manifest entry, or None if no transactions could be extracted.
    Rows that could not be read are appended to `skipped_rows`, tagged with the file name.
    The caller is responsible for appending the entry to the manifest and rebuilding the ledger.
    """
    file_skipped: List[Dict[str, Any]] = []
    try:
        parsed = parse_statement_file(source_path, file_skipped)
    except Exception as e:
        print(f"Error parsing {display_name}: {e}")
        return None
    if skipped_rows is not None:
        skipped_rows.extend({"filename": display_name, **row} for row in file_skipped)
    if not parsed:
        return None

    df_parsed = pd.DataFrame(parsed)
    df_parsed['date'] = pd.to_datetime(df_parsed['date'], errors='coerce')
    df_parsed = df_parsed.dropna(subset=['date']).sort_values('date').reset_index(drop=True)
    if df_parsed.empty:
        return None
    df_parsed['date'] = df_parsed['date'].dt.strftime('%Y-%m-%d')
    df_parsed['debit'] = pd.to_numeric(df_parsed.get('debit', 0.0), errors='coerce').fillna(0.0)
    df_parsed['credit'] = pd.to_numeric(df_parsed.get('credit', 0.0), errors='coerce').fillna(0.0)

    # Collect unique debit merchants to resolve via Intelligence Engine
    debit_rows = df_parsed[df_parsed['debit'] > 0]
    merchants_to_check = []
    for _, r in debit_rows.iterrows():
        narr = str(r['narration'])
        raw_m, _, _ = clean_narration(narr, float(r.get('debit', 0.0) or 0.0), float(r.get('credit', 0.0) or 0.0))
        merchants_to_check.append({
            "name": raw_m,
            "sample_narration": narr
        })

    resolve_unknown_merchants_with_intelligence(merchants_to_check, vault, ai_gate=ai_gate)

    stmt_id = f"stmt_{uuid.uuid4().hex[:8]}"
    stored_file = f"{stmt_id}.csv"
    df_parsed.to_csv(os.path.join(vault, stored_file), index=False)

    return {
        "id": stmt_id,
        "filename": display_name,
        "date_range": f"{df_parsed['date'].min()} to {df_parsed['date'].max()}",
        "transactions_count": len(df_parsed),
        "inflow": round(float(df_parsed['credit'].sum()), 2),
        "outflow": round(float(df_parsed['debit'].sum()), 2),
        "stored_file": stored_file,
        "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "is_demo": is_demo
    }

MAX_SKIPPED_ROWS_RETURNED = 100

def remove_all_statements(vault: str):
    """Deletes every stored statement in the vault and clears the manifest."""
    for item in load_manifest(vault):
        stored_file = os.path.join(vault, item.get("stored_file", ""))
        if os.path.exists(stored_file):
            try:
                os.remove(stored_file)
            except Exception:
                pass
    save_manifest([], vault)

@app.post("/api/upload")
async def upload_statement(
    request: Request,
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None)
):
    vault = resolve_vault(request)
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
        
    if not upload_list:
        return {"status": "error", "message": "No files provided"}
        
    manifest = load_manifest(vault)
    added_statements = []
    skipped_rows: List[Dict[str, Any]] = []
    gate = _ai_gate(request)

    for f in upload_list:
        if not f.filename:
            continue
        ext = os.path.splitext(f.filename)[1].lower()
        temp_path = os.path.join(vault, f"temp_{uuid.uuid4().hex}{ext}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        try:
            meta = ingest_statement_file(temp_path, f.filename, vault, skipped_rows=skipped_rows, ai_gate=gate)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        if meta:
            manifest.append(meta)
            added_statements.append(meta)

    save_manifest(manifest, vault)
    unified_df = rebuild_active_ledger(vault)

    # Rows that had an amount but no readable date; the list is capped to keep the response small
    skipped_report = {
        "skipped_rows_count": len(skipped_rows),
        "skipped_rows": skipped_rows[:MAX_SKIPPED_ROWS_RETURNED],
        "ai_limited": gate.denied,
    }

    if unified_df is None or len(unified_df) == 0:
        return {"status": "error", "message": "No valid transactions extracted from files", **skipped_report}

    return {
        "status": "success",
        "added_count": len(added_statements),
        "total_statements": len(manifest),
        "transactions_parsed": len(unified_df),
        "date_range": f"{unified_df['date'].min()} to {unified_df['date'].max()}",
        "statements": manifest,
        **skipped_report
    }

@app.post("/api/clear-statement")
def clear_statement(request: Request):
    vault = resolve_vault(request)
    remove_all_statements(vault)
    rebuild_active_ledger(vault)
    return {"status": "cleared", "has_statement": False}

SAMPLE_STATEMENTS_DIR = config.SAMPLE_STATEMENTS_DIR

def list_sample_statements() -> List[Dict[str, str]]:
    """Lists the bundled sample statements as {id, label} pairs."""
    if not os.path.isdir(SAMPLE_STATEMENTS_DIR):
        return []
    samples = []
    for name in sorted(os.listdir(SAMPLE_STATEMENTS_DIR)):
        if not name.lower().endswith(".csv"):
            continue
        sample_id = os.path.splitext(name)[0]
        person = sample_id.replace("_1year_statement", "").replace("_", " ").title()
        samples.append({"id": sample_id, "label": f"{person} (1-year statement)"})
    return samples

def build_demo_template(sample_path: str, target_dir: str):
    """Ingests the demo sample statement into target_dir exactly as a sample load would."""
    label = next((s["label"] for s in list_sample_statements() if s["id"] == DEMO_SAMPLE_ID), "Demo statement")
    meta = ingest_statement_file(sample_path, label, target_dir, is_demo=True)
    if not meta:
        raise RuntimeError("Demo sample statement could not be parsed")
    save_manifest([meta], target_dir)
    rebuild_active_ledger(target_dir)

class LoadSampleRequest(BaseModel):
    sample_id: str

@app.get("/api/samples")
def get_samples():
    return {"samples": list_sample_statements()}

@app.post("/api/load-sample")
def load_sample_statement(req: LoadSampleRequest, request: Request):
    """Replaces the current session's statements with one of the bundled sample statements."""
    sample = next((s for s in list_sample_statements() if s["id"] == req.sample_id), None)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample statement not found")

    vault = resolve_vault(request)
    remove_all_statements(vault)
    source_path = os.path.join(SAMPLE_STATEMENTS_DIR, f"{sample['id']}.csv")
    gate = _ai_gate(request)
    meta = ingest_statement_file(source_path, sample["label"], vault, is_demo=True, ai_gate=gate)
    if not meta:
        raise HTTPException(status_code=500, detail="Sample statement could not be parsed")

    save_manifest([meta], vault)
    unified_df = rebuild_active_ledger(vault)
    return {
        "status": "success",
        "has_statement": unified_df is not None and len(unified_df) > 0,
        "statements": [meta],
        "ai_limited": gate.denied
    }

# ==========================================
# MERCHANT INTELLIGENCE & DICTIONARY APIS
# ==========================================

class MerchantUpdateRequest(BaseModel):
    sub_category: str
    category: Optional[str] = None

@app.get("/api/merchant-dictionary")
def get_merchant_dictionary(request: Request, status: Optional[str] = None, search: Optional[str] = None):
    vault = resolve_vault(request)
    dictionary = load_merchant_dictionary(vault)
    items = list(dictionary.values())
    
    if search:
        s_lower = search.lower().strip()
        items = [
            it for it in items 
            if s_lower in it.get("merchant_key", "").lower() 
            or s_lower in it.get("display_name", "").lower() 
            or s_lower in it.get("sub_category", "").lower()
            or s_lower in it.get("sample_narration", "").lower()
        ]
        
    if status == "pending":
        items = [it for it in items if it.get("needs_review") or not it.get("verified")]
    elif status == "verified":
        items = [it for it in items if it.get("verified") and not it.get("needs_review")]
        
    items.sort(key=lambda x: (not x.get("needs_review", False), x.get("display_name", "")))
    return {"merchants": items, "total": len(items)}

@app.get("/api/merchant-dictionary/stats")
def get_merchant_dictionary_stats(request: Request):
    vault = resolve_vault(request)
    dictionary = load_merchant_dictionary(vault)
    items = list(dictionary.values())
    pending_count = sum(1 for it in items if it.get("needs_review") or not it.get("verified"))
    verified_count = sum(1 for it in items if it.get("verified") and not it.get("needs_review"))
    return {
        "total": len(items),
        "pending_review": pending_count,
        "verified": verified_count,
        "categories": AVAILABLE_SUBCATEGORIES,
        "macro_map": SUB_TO_MACRO
    }

@app.put("/api/merchant-dictionary/{merchant_key}")
def update_merchant_category(merchant_key: str, req: MerchantUpdateRequest, request: Request):
    vault = resolve_vault(request)
    dictionary = load_merchant_dictionary(vault)
    key_norm = normalize_merchant_key(merchant_key)
    
    macro, subcat = map_to_standard_category(req.sub_category, req.category or "")
    now_iso = datetime.datetime.now().isoformat()
    if key_norm in dictionary:
        entry = dictionary[key_norm]
        entry["category"] = macro
        entry["sub_category"] = subcat
        entry["confidence"] = 1.0
        entry["source"] = "user"
        entry["verified"] = True
        entry["needs_review"] = False
        entry["reasoning"] = "Verified and assigned by user"
        entry["updated_at"] = now_iso
    else:
        entry = {
            "merchant_key": key_norm,
            "display_name": merchant_key,
            "category": macro,
            "sub_category": subcat,
            "confidence": 1.0,
            "reasoning": "Created and assigned by user",
            "source": "user",
            "verified": True,
            "needs_review": False,
            "sample_narration": "",
            "updated_at": now_iso
        }
        dictionary[key_norm] = entry
        
    save_merchant_dictionary(vault, dictionary)
    rebuild_active_ledger(vault)
    return {"status": "success", "merchant": entry}

@app.post("/api/merchant-dictionary/{merchant_key}/approve")
def approve_merchant(merchant_key: str, request: Request):
    vault = resolve_vault(request)
    dictionary = load_merchant_dictionary(vault)
    key_norm = normalize_merchant_key(merchant_key)
    if key_norm not in dictionary:
        return {"status": "error", "message": "Merchant not found"}
        
    entry = dictionary[key_norm]
    entry["verified"] = True
    entry["needs_review"] = False
    entry["updated_at"] = datetime.datetime.now().isoformat()
    save_merchant_dictionary(vault, dictionary)
    rebuild_active_ledger(vault)
    return {"status": "approved", "merchant": entry}

@app.post("/api/merchant-dictionary/approve-all")
def approve_all_merchants(request: Request):
    vault = resolve_vault(request)
    dictionary = load_merchant_dictionary(vault)
    count = 0
    now_iso = datetime.datetime.now().isoformat()
    for entry in dictionary.values():
        if entry.get("needs_review") or not entry.get("verified"):
            entry["verified"] = True
            entry["needs_review"] = False
            entry["updated_at"] = now_iso
            count += 1
            
    save_merchant_dictionary(vault, dictionary)
    rebuild_active_ledger(vault)
    return {"status": "success", "approved_count": count}

@app.post("/api/merchant-dictionary/scan-active")
def scan_active_statements(request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    if df is None or len(df) == 0:
        return {"status": "error", "message": "No active statements"}
        
    debit_rows = df[df['debit'] > 0]
    merchants_to_check = []
    for _, r in debit_rows.iterrows():
        narr = str(r['narration'])
        raw_m, _, _ = clean_narration(narr, float(r.get('debit', 0.0) or 0.0), float(r.get('credit', 0.0) or 0.0))
        merchants_to_check.append({
            "name": raw_m,
            "sample_narration": narr
        })
        
    gate = _ai_gate(request)
    dictionary = resolve_unknown_merchants_with_intelligence(merchants_to_check, vault, ai_gate=gate)
    rebuild_active_ledger(vault)
    
    items = list(dictionary.values())
    pending_count = sum(1 for it in items if it.get("needs_review") or not it.get("verified"))
    return {
        "status": "success",
        "total_merchants": len(items),
        "pending_review": pending_count,
        "ai_limited": gate.denied
    }

@app.post("/api/merchant-dictionary/reset")
def reset_merchant_cache(request: Request):
    vault = resolve_vault(request)
    old_dict = load_merchant_dictionary(vault)
    dict_path = os.path.join(vault, "merchant_dictionary.json")
    if os.path.exists(dict_path):
        try:
            os.remove(dict_path)
        except Exception:
            pass
    save_merchant_dictionary(vault, {})
    
    # Re-scan active statements or existing items and re-run rules + Gemini AI classification
    df = get_current_df(vault)
    merchants_to_check = []
    if df is not None and len(df) > 0:
        debit_rows = df[df['debit'] > 0]
        for _, r in debit_rows.iterrows():
            narr = str(r['narration'])
            raw_m, _, _ = clean_narration(narr, float(r.get('debit', 0.0) or 0.0), float(r.get('credit', 0.0) or 0.0))
            merchants_to_check.append({
                "name": raw_m,
                "sample_narration": narr
            })
    elif old_dict:
        for k, v in old_dict.items():
            merchants_to_check.append({
                "name": v.get("display_name") or v.get("merchant_key", ""),
                "sample_narration": v.get("sample_narration", "")
            })

    gate = _ai_gate(request)
    if merchants_to_check:
        resolve_unknown_merchants_with_intelligence(merchants_to_check, vault, force_reclassify=True, ai_gate=gate)

    rebuild_active_ledger(vault)
    dictionary = load_merchant_dictionary(vault)
    return {"status": "reset", "merchants": list(dictionary.values()), "ai_limited": gate.denied}

# ----------------- FINNEAS AGENT ENDPOINTS -----------------

class CreateThreadRequest(BaseModel):
    title: Optional[str] = "New Financial Discussion"

class AttachmentItem(BaseModel):
    name: str
    type: str
    size: Optional[int] = 0
    data: str # base64 payload

class FinneasChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: Optional[str] = ""
    attachments: Optional[List[AttachmentItem]] = None

@app.get("/api/finneas/threads")
def get_finneas_threads_endpoint(request: Request):
    vault = resolve_vault(request)
    return {"threads": load_threads(vault)}

@app.post("/api/finneas/threads")
def create_finneas_thread_endpoint(req: CreateThreadRequest, request: Request):
    vault = resolve_vault(request)
    new_thread = create_new_thread(title=req.title or "New Financial Discussion", user_vault_dir=vault)
    return {"status": "success", "thread": new_thread}

@app.get("/api/finneas/threads/{thread_id}")
def get_finneas_thread_endpoint(thread_id: str, request: Request):
    vault = resolve_vault(request)
    thread = get_thread(thread_id, vault)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"thread": thread}

@app.delete("/api/finneas/threads/{thread_id}")
def delete_finneas_thread_endpoint(thread_id: str, request: Request):
    vault = resolve_vault(request)
    success = delete_thread(thread_id, vault)
    return {"status": "success" if success else "not_found"}

@app.post("/api/finneas/chat")
def finneas_chat_endpoint(req: FinneasChatRequest, request: Request):
    vault = resolve_vault(request)
    df = get_current_df(vault)
    msg_text = (req.message or "").strip()

    if not msg_text and not req.attachments:
        raise HTTPException(status_code=400, detail="Message or attachment required")

    if not msg_text and req.attachments:
        doc_names = ", ".join(att.name for att in req.attachments[:2])
        msg_text = f"Please analyze the attached document(s) ({doc_names}), extract key terms, fine print, and provide an institutional fiduciary breakdown."

    thread_id = req.thread_id
    if not thread_id:
        title_summary = msg_text[:36] if msg_text else "Document Analysis"
        new_th = create_new_thread(title=title_summary + "...", user_vault_dir=vault)
        thread_id = new_th["id"]

    attachments_payload = [att.dict() for att in req.attachments] if req.attachments else None

    result = run_finneas_chat(
        thread_id=thread_id,
        user_message=msg_text,
        df=df,
        user_vault_dir=vault,
        attachments=attachments_payload,
        ai_allowed=try_consume(get_authenticated_user(request)["id"])
    )
    return result

@app.get("/api/finneas/attachments/{att_id}/{filename}")
def get_finneas_attachment(att_id: str, filename: str, request: Request):
    vault = resolve_vault(request)
    att_dir = os.path.join(vault, "attachments")
    # Safe match pattern
    target_path = os.path.join(att_dir, f"{att_id}_{filename}")
    if not os.path.exists(target_path):
        # Fallback check matching att_id prefix
        matched = [f for f in os.listdir(att_dir) if f.startswith(f"{att_id}_")] if os.path.exists(att_dir) else []
        if matched:
            target_path = os.path.join(att_dir, matched[0])
        else:
            raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(target_path, filename=filename)
