import os
import shutil
import json
import uuid
import datetime
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.analytics.engine import (
    calculate_monthly_metrics,
    detect_recurring_charges,
    analyze_insurance_gaps,
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
from app.services.insurance.catalog import get_catalog_products, find_product_by_id
from app.services.insurance.personas import generate_persona_transactions
from app.services.insurance.manager import (
    load_declared_policies,
    add_declared_policy,
    delete_declared_policy,
    clear_declared_policies,
    set_declared_policies,
    compute_insurance_portfolio
)
from app.services.insurance.recommender import call_gemini_insurance_advisor
from app.services.goals.engine import (
    get_cashflow_context,
    load_user_goals,
    get_default_goals,
    save_user_goals,
    add_user_goal,
    delete_user_goal,
    simulate_goal_trajectory
)
from app.services.auth.users import (
    authenticate_user,
    register_user,
    get_user_by_username,
    list_demo_personas,
    get_user_vault_path,
    initialize_and_migrate_vault
)
from app.services.chat.agent import (
    load_threads,
    get_thread,
    create_new_thread,
    delete_thread,
    run_finneas_chat
)

app = FastAPI(title="FinSight AI Core Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize master vault & auto-migrate existing data on startup
initialize_and_migrate_vault()

def get_user_vault(request: Optional[Request] = None, user_id: Optional[str] = None) -> str:
    """Resolves the user's isolated vault directory."""
    target_user = user_id
    if not target_user and request:
        target_user = request.headers.get("X-User-ID") or request.headers.get("x-user-id") or request.query_params.get("user_id")
    clean_user = (target_user or "azizul").strip().lower()
    return get_user_vault_path(clean_user)

def load_manifest(user_vault: Optional[str] = None) -> List[Dict[str, Any]]:
    vault = user_vault or get_user_vault()
    manifest_path = os.path.join(vault, "manifest.json")
    if not os.path.exists(manifest_path):
        return []
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_manifest(manifest: List[Dict[str, Any]], user_vault: Optional[str] = None):
    vault = user_vault or get_user_vault()
    manifest_path = os.path.join(vault, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def rebuild_active_ledger(user_vault: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Stitches all active statements in the user's vault into a continuous,
    chronologically sorted, deduplicated master ledger.
    """
    vault = user_vault or get_user_vault()
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

def get_current_df(user_vault: Optional[str] = None) -> Optional[pd.DataFrame]:
    vault = user_vault or get_user_vault()
    active_path = os.path.join(vault, "active_unified_ledger.csv")
    if not os.path.exists(active_path):
        return rebuild_active_ledger(vault)
    try:
        df = pd.read_csv(active_path)
        return df
    except Exception:
        return None

def get_display_name(user_vault: Optional[str] = None) -> str:
    vault = user_vault or get_user_vault()
    manifest = load_manifest(vault)
    if not manifest:
        return "No Statements Uploaded"
    if len(manifest) == 1:
        return manifest[0]["filename"]
    short_names = [m["filename"].replace('.pdf', '').replace('.csv', '') for m in manifest]
    return f"{len(manifest)} Statements ({', '.join(short_names)})"

# ==========================================
# AUTHENTICATION & MULTI-USER APIS
# ==========================================

class LoginRequest(BaseModel):
    username: str
    pin: str

class RegisterRequest(BaseModel):
    name: str
    username: str
    pin: str = "1234"
    email: str = ""

@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest):
    user = authenticate_user(req.username, req.pin)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or PIN.")
    # Warm up active ledger for this user
    vault = get_user_vault(user_id=user["username"])
    rebuild_active_ledger(vault)
    return {
        "status": "success",
        "user": user,
        "token": f"finman_{user['username']}"
    }

@app.post("/api/auth/register")
def register_endpoint(req: RegisterRequest):
    try:
        user = register_user(
            name=req.name,
            username=req.username,
            pin=req.pin,
            email=req.email
        )
        vault = get_user_vault(user_id=user["username"])
        rebuild_active_ledger(vault)
        return {
            "status": "success",
            "user": user,
            "token": f"finman_{user['username']}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/personas")
def get_personas_list_endpoint():
    return {"personas": list_demo_personas()}

@app.get("/api/auth/me")
def get_current_user_profile(request: Request):
    user_id = request.headers.get("X-User-ID", "azizul").strip().lower()
    user = get_user_by_username(user_id)
    if not user:
        user = authenticate_user("azizul", "1234")
    return {"user": user}

@app.get("/api/health")
def health_check(request: Request):
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
        dti_ratio=0.24,
        has_insurance_gap=True
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
    vault = get_user_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {"months": []}
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    months = sorted(df['year_month'].unique().tolist(), reverse=True)
    return {"months": months}

@app.get("/api/month-detail/{year_month}")
def get_month_detail(year_month: str, request: Request):
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {"error": "No statement loaded"}
    return generate_monthly_insights(df, year_month)

@app.get("/api/statements-list")
def get_statements_list(request: Request):
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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

@app.get("/api/subscriptions")
@app.get("/api/strategic-audit")
@app.post("/api/strategic-audit")
def get_subscriptions(request: Request):
    vault = get_user_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {}
    try:
        return generate_strategic_audit(df)
    except Exception as e:
        print(f"[finMan] Strategic audit error: {e}. Falling back to rule engine.")
        return detect_recurring_charges(df)

@app.get("/api/insurance")
def get_insurance(request: Request):
    vault = get_user_vault(request)
    df = get_current_df(vault)
    if df is None:
        return {}
    return analyze_insurance_gaps(df, annual_income=1260000.0, outstanding_loans=680000.0)

# ==========================================
# INSURANCE PLANNER & MANAGER APIS
# ==========================================

class DeclarePolicyRequest(BaseModel):
    category: str
    insurer_name: str
    plan_name: str
    sum_insured: float
    annual_premium: float = 0.0
    source: str = "PERSONAL_RETAIL"
    is_employer_provided: bool = False
    covered_members: Optional[List[str]] = None
    has_room_rent_capping: bool = False
    renewal_date: Optional[str] = None
    notes: Optional[str] = None

class PortfolioQueryRequest(BaseModel):
    annual_income: Optional[float] = None
    outstanding_loans: Optional[float] = None
    liquid_assets: Optional[float] = None
    dependents_count: Optional[int] = None
    income_multiplier: Optional[float] = None

@app.get("/api/insurance/portfolio")
def get_insurance_portfolio(
    request: Request,
    annual_income: Optional[float] = None,
    outstanding_loans: Optional[float] = None,
    liquid_assets: Optional[float] = None,
    dependents_count: Optional[int] = None,
    income_multiplier: Optional[float] = None
):
    vault = get_user_vault(request)
    df = get_current_df(vault)
    user_id = request.headers.get("X-User-ID", "azizul").strip().lower()
    user = get_user_by_username(user_id) or {}
    
    user_income = float(user.get("annual_income", 1260000.0))
    user_loans = float(user.get("outstanding_loans", 0.0))
    user_assets = float(user.get("liquid_assets", 500000.0))
    user_dependents = int(user.get("dependents", 2))
    user_mult = 12.0

    res = compute_insurance_portfolio(
        df=df,
        annual_income=annual_income,
        outstanding_loans=outstanding_loans,
        liquid_assets=liquid_assets,
        dependents_count=dependents_count if dependents_count is not None else user_dependents,
        income_multiplier=income_multiplier if income_multiplier is not None else user_mult,
        user_vault_dir=vault
    )
    return res

@app.post("/api/insurance/portfolio")
def query_insurance_portfolio(req: PortfolioQueryRequest, request: Request):
    return get_insurance_portfolio(
        request=request,
        annual_income=req.annual_income,
        outstanding_loans=req.outstanding_loans,
        liquid_assets=req.liquid_assets,
        dependents_count=req.dependents_count,
        income_multiplier=req.income_multiplier
    )

@app.get("/api/insurance/declared")
def get_declared_policies_endpoint(request: Request):
    vault = get_user_vault(request)
    return {"policies": load_declared_policies(vault)}

@app.post("/api/insurance/declare")
def declare_policy_endpoint(req: DeclarePolicyRequest, request: Request):
    vault = get_user_vault(request)
    new_pol = add_declared_policy(req.dict(), vault)
    return {"status": "success", "policy": new_pol}

@app.delete("/api/insurance/declare/{policy_id}")
def delete_declared_policy_endpoint(policy_id: str, request: Request):
    vault = get_user_vault(request)
    success = delete_declared_policy(policy_id, vault)
    return {"status": "success" if success else "not_found"}

@app.get("/api/insurance/catalog")
def get_catalog_endpoint(category: Optional[str] = None):
    return {"products": get_catalog_products(category)}

@app.post("/api/insurance/recommendations")
def get_insurance_recommendations(request: Request, req: Optional[PortfolioQueryRequest] = None):
    vault = get_user_vault(request)
    user_id = request.headers.get("X-User-ID", "azizul").strip().lower()
    user = get_user_by_username(user_id) or {}

    portfolio = get_insurance_portfolio(
        request=request,
        annual_income=req.annual_income if req else None,
        outstanding_loans=req.outstanding_loans if req else None,
        liquid_assets=req.liquid_assets if req else None,
        dependents_count=req.dependents_count if req else None,
        income_multiplier=req.income_multiplier if req else None
    )
    profile = {
        "age": user.get("age", 30),
        "marital_status": "Married" if (req and req.dependents_count and req.dependents_count > 0) else "Single"
    }

    ai_result = call_gemini_insurance_advisor(portfolio, profile)
    return {
        "portfolio": portfolio,
        "ai_recommendations": ai_result
    }

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
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
    goal_data = req.dict()
    saved = add_user_goal(goal_data, vault)
    return {"status": "success", "goal": saved}

@app.delete("/api/goals/{goal_id}")
def delete_goal_endpoint(goal_id: str, request: Request):
    vault = get_user_vault(request)
    deleted = delete_user_goal(goal_id, vault)
    return {"status": "success" if deleted else "not_found"}

@app.post("/api/goals/simulate")
def simulate_goal_advanced_endpoint(req: AdvancedGoalSimRequest, request: Request):
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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

@app.post("/api/upload")
async def upload_statement(
    request: Request,
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None)
):
    vault = get_user_vault(request)
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
        
    if not upload_list:
        return {"status": "error", "message": "No files provided"}
        
    manifest = load_manifest(vault)
    added_statements = []
    
    for f in upload_list:
        if not f.filename:
            continue
        temp_path = os.path.join(vault, f"temp_{f.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
            
        try:
            parsed = parse_statement_file(temp_path)
        except Exception as e:
            print(f"Error parsing {f.filename}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            continue
            
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if not parsed:
            continue
            
        df_parsed = pd.DataFrame(parsed)
        df_parsed['date'] = pd.to_datetime(df_parsed['date'], errors='coerce')
        df_parsed = df_parsed.dropna(subset=['date']).sort_values('date').reset_index(drop=True)
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
            
        resolve_unknown_merchants_with_intelligence(merchants_to_check, vault)
        
        stmt_id = f"stmt_{uuid.uuid4().hex[:8]}"
        stored_file = f"{stmt_id}.csv"
        stored_path = os.path.join(vault, stored_file)
        df_parsed.to_csv(stored_path, index=False)
        
        meta = {
            "id": stmt_id,
            "filename": f.filename,
            "date_range": f"{df_parsed['date'].min()} to {df_parsed['date'].max()}",
            "transactions_count": len(df_parsed),
            "inflow": round(float(df_parsed['credit'].sum()), 2),
            "outflow": round(float(df_parsed['debit'].sum()), 2),
            "stored_file": stored_file,
            "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "is_demo": False
        }
        manifest.append(meta)
        added_statements.append(meta)
        
    save_manifest(manifest, vault)
    unified_df = rebuild_active_ledger(vault)
    
    if unified_df is None or len(unified_df) == 0:
        return {"status": "error", "message": "No valid transactions extracted from files"}
        
    return {
        "status": "success",
        "added_count": len(added_statements),
        "total_statements": len(manifest),
        "transactions_parsed": len(unified_df),
        "date_range": f"{unified_df['date'].min()} to {unified_df['date'].max()}",
        "statements": manifest
    }

@app.post("/api/clear-statement")
def clear_statement(request: Request):
    vault = get_user_vault(request)
    manifest = load_manifest(vault)
    for item in manifest:
        stored_file = os.path.join(vault, item.get("stored_file", ""))
        if os.path.exists(stored_file):
            try:
                os.remove(stored_file)
            except Exception:
                pass
    save_manifest([], vault)
    rebuild_active_ledger(vault)
    return {"status": "cleared", "has_statement": False}

@app.post("/api/load-demo")
def load_demo_statement_endpoint(request: Request):
    """Loads or restores the pre-seeded 1-year statement for the current user or demo persona."""
    vault = get_user_vault(request)
    user_id = request.headers.get("X-User-ID", "azizul").strip().lower()
    user = get_user_by_username(user_id) or {}

    if user.get("is_persona") and user.get("persona_key"):
        pkey = user["persona_key"]
        df = generate_persona_transactions(pkey)
        stmt_filename = f"{user['username']}_statement.csv"
        df.to_csv(os.path.join(vault, "active_unified_ledger.csv"), index=False)
        df.to_csv(os.path.join(vault, stmt_filename), index=False)

        manifest_data = [{
            "id": f"stmt_{user['username']}_01",
            "filename": f"{user['name']} 1-Year Bank Statement",
            "stored_file": stmt_filename,
            "tx_count": len(df),
            "file_size": os.path.getsize(os.path.join(vault, stmt_filename)),
            "uploaded_at": "2026-10-22T00:00:00Z",
            "date_range": f"{df['date'].min()} to {df['date'].max()}"
        }]
        save_manifest(manifest_data, vault)
        return {"status": "success", "message": f"Loaded 1-year statement for {user['name']}", "has_statement": True}
    else:
        demo_src = os.path.join(PROJECT_ROOT, "sample_statements", "vikram_malhotra_1year_statement.csv")
        if os.path.exists(demo_src):
            df = pd.read_csv(demo_src)
            stmt_filename = "demo_salaried_statement.csv"
            df.to_csv(os.path.join(vault, "active_unified_ledger.csv"), index=False)
            df.to_csv(os.path.join(vault, stmt_filename), index=False)
            manifest_data = [{
                "id": "stmt_demo_01",
                "filename": "Sample 1-Year Salaried Bank Statement",
                "stored_file": stmt_filename,
                "tx_count": len(df),
                "file_size": os.path.getsize(os.path.join(vault, stmt_filename)),
                "uploaded_at": "2026-10-22T00:00:00Z"
            }]
            save_manifest(manifest_data, vault)
            return {"status": "success", "message": "Loaded sample 1-year salaried statement", "has_statement": True}
        return {"status": "error", "message": "Demo file not found"}

# ==========================================
# MERCHANT INTELLIGENCE & DICTIONARY APIS
# ==========================================

class MerchantUpdateRequest(BaseModel):
    sub_category: str
    category: Optional[str] = None

@app.get("/api/merchant-dictionary")
def get_merchant_dictionary(request: Request, status: Optional[str] = None, search: Optional[str] = None):
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
    vault = get_user_vault(request)
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
        
    dictionary = resolve_unknown_merchants_with_intelligence(merchants_to_check, vault)
    rebuild_active_ledger(vault)
    
    items = list(dictionary.values())
    pending_count = sum(1 for it in items if it.get("needs_review") or not it.get("verified"))
    return {
        "status": "success",
        "total_merchants": len(items),
        "pending_review": pending_count
    }

@app.post("/api/merchant-dictionary/reset")
def reset_merchant_cache(request: Request):
    vault = get_user_vault(request)
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

    if merchants_to_check:
        resolve_unknown_merchants_with_intelligence(merchants_to_check, vault, force_reclassify=True)

    rebuild_active_ledger(vault)
    dictionary = load_merchant_dictionary(vault)
    return {"status": "reset", "merchants": list(dictionary.values())}

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
    vault = get_user_vault(request)
    return {"threads": load_threads(vault)}

@app.post("/api/finneas/threads")
def create_finneas_thread_endpoint(req: CreateThreadRequest, request: Request):
    vault = get_user_vault(request)
    new_thread = create_new_thread(title=req.title or "New Financial Discussion", user_vault_dir=vault)
    return {"status": "success", "thread": new_thread}

@app.get("/api/finneas/threads/{thread_id}")
def get_finneas_thread_endpoint(thread_id: str, request: Request):
    vault = get_user_vault(request)
    thread = get_thread(thread_id, vault)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"thread": thread}

@app.delete("/api/finneas/threads/{thread_id}")
def delete_finneas_thread_endpoint(thread_id: str, request: Request):
    vault = get_user_vault(request)
    success = delete_thread(thread_id, vault)
    return {"status": "success" if success else "not_found"}

@app.post("/api/finneas/chat")
def finneas_chat_endpoint(req: FinneasChatRequest, request: Request):
    vault = get_user_vault(request)
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
        attachments=attachments_payload
    )
    return result

@app.get("/api/finneas/attachments/{att_id}/{filename}")
def get_finneas_attachment(att_id: str, filename: str, request: Request):
    vault = get_user_vault(request)
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
