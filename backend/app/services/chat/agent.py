"""
Finneas Agent: Multi-Turn Conversational Fiduciary Agent.
Maintains persistent conversation threads in user vaults, calls statement tools via Gemini 3.5,
and ensures all advice is rigorously grounded in the user's authentic cashflow ledger.
"""

import os
import json
import re
import datetime
import base64
import uuid
from typing import Dict, Any, List, Optional
import requests
import pandas as pd

from app.services.chat.tools import (
    GEMINI_TOOLS_DECLARATIONS,
    execute_finneas_tool
)

def _get_threads_file(user_vault_dir: Optional[str] = None) -> str:
    if not user_vault_dir:
        raise ValueError("[Finneas Agent] user_vault_dir must be specified to maintain strict per-user profile isolation.")
    if not os.path.exists(user_vault_dir):
        os.makedirs(user_vault_dir, exist_ok=True)
    return os.path.join(user_vault_dir, "finneas_threads.json")

def load_threads(user_vault_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads all chat threads for the user from persistent vault."""
    filepath = _get_threads_file(user_vault_dir)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("threads", [])
    except Exception as e:
        print(f"[Finneas Agent] Error reading {filepath}: {e}")
        return []

def save_threads(threads: List[Dict[str, Any]], user_vault_dir: Optional[str] = None) -> bool:
    """Saves chat threads to persistent vault."""
    filepath = _get_threads_file(user_vault_dir)
    try:
        data = {"threads": threads}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[Finneas Agent] Error writing {filepath}: {e}")
        return False

def get_thread(thread_id: str, user_vault_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single thread by ID."""
    threads = load_threads(user_vault_dir)
    for t in threads:
        if t["id"] == thread_id:
            return t
    return None

def create_new_thread(title: str = "New Financial Discussion", user_vault_dir: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new empty conversation thread."""
    threads = load_threads(user_vault_dir)
    now_iso = datetime.datetime.now().isoformat()
    new_id = f"thread_{int(datetime.datetime.now().timestamp())}_{len(threads) + 1}"
    
    thread = {
        "id": new_id,
        "title": title,
        "created_at": now_iso,
        "updated_at": now_iso,
        "messages": []
    }
    threads.insert(0, thread) # Most recent first
    save_threads(threads, user_vault_dir)
    return thread

def delete_thread(thread_id: str, user_vault_dir: Optional[str] = None) -> bool:
    """Deletes a conversation thread by ID."""
    threads = load_threads(user_vault_dir)
    initial_len = len(threads)
    threads = [t for t in threads if t["id"] != thread_id]
    if len(threads) < initial_len:
        save_threads(threads, user_vault_dir)
        return True
    return False

# ----------------- FINNEAS AGENT EXECUTION LOOP -----------------

FINNEAS_SYSTEM_PROMPT = """You are Finn-eas ("Finance made easy"), the sharp, encouraging, and friendly fiduciary mascot for FinSight.
Your mission is to make personal finance effortless, crystal-clear, and completely free of complex jargon, sales hype, or banking double-speak.

Core Operating Guidelines:
1. ALWAYS GROUND IN USER'S REAL DATA: You have direct access to tools that query the user's authentic bank statement transactions, cashflow surplus, loan liabilities, subscriptions, and savings goals. ALWAYS invoke the appropriate tool to retrieve real numbers before giving an answer.
2. NEVER INVENT OR HALLUCINATE LEDGER NUMBERS: If asked "How much did I spend at McDonalds?", call `search_transactions`. If asked about category velocity, call `get_category_trends`. If asked about loan safety, call `evaluate_loan_affordability`.
3. SALARY & INFLOWS: If the user asks about their salary, earnings, income, payroll, or deposits for any month (e.g. "what was my salary on month of august?"), ALWAYS call `get_salary_and_inflows` specifying the month. Report the exact salary credit if found, or explain what other incoming transfers occurred if no formal employer salary credit was detected.
4. TOP MERCHANTS & FOOD STALLS: When asked which merchant, food stall, or store the user spent the most on (e.g. "which food stall did I spend the most last month?"), call `get_top_merchants` with category="food" and month="last month". State the #1 destination clearly with exact amount spent, order count, and a ranked list of the top contenders.
5. FIDUCIARY LOYALTY: You work 100% for the user, not a bank. If a loan EMI will overwhelm their surplus, truthfully declare it unsafe.
6. DOCUMENT COMPARISON: When the user attaches files (PDFs, quotes, offer letters, bills, images, loan sanction letters):
- Thoroughly inspect all terms, tables, fine print, interest rates, fees, penalties, lock-in periods, and payment schedules.
- If comparing two or more options, present a clear, structured side-by-side markdown comparison table highlighting the amounts, rates, fees, tenure, and any hidden charges or restrictive clauses.
- Conclude with a definitive, unbiased fiduciary recommendation on which option is genuinely superior and how it aligns with their real cashflow.
7. ABSOLUTELY NO EMOJIS: Never use any emojis, symbols, or pictographs anywhere in your responses (no smiles, food icons, medals, money bags, or sparklers). Keep all responses strictly text and markdown.
8. ABSOLUTELY NO EM DASHES: Never use em dashes ("—") or en dashes ("–"). Use standard hyphens ("-"), colons (":"), or parentheses "()" instead.
9. CRISP TONE & NUMBER FORMATTING: Speak with warmth, clarity, and direct intelligence. Format Indian rupee amounts with commas (e.g. ₹41,884, ₹15 Lakhs). Keep explanations direct and actionable.
10. STAY IN SCOPE: This app analyses spending, cashflow, subscriptions, loans and savings goals. It does not give insurance advice (which policy or cover to buy, comparing policies), tax planning (deductions, tax-saving schemes, regimes, filing), or investment advice (which funds, stocks or assets to choose). If asked for any of these, including through an attached document, politely say that this is outside what this app does, do not answer the question itself, and offer to help with a related spending question instead (e.g. "I can show you how much you have spent on insurance premiums this year"). Factual questions about the user's own transactions in these categories (such as how much they paid in premiums or invested via SIPs) are spending questions and should be answered normally with the tools.
"""

def _clean_response_text(text: str) -> str:
    """
    Enforces strict user preference:
    1. Replaces em dashes ('—') and en dashes ('–') with standard hyphen/colon.
    2. Strips all emoji characters and pictorial symbols.
    """
    if not text:
        return text

    # 1. Replace em dash and en dash
    cleaned = text.replace("—", " - ").replace("–", " - ")

    # 2. Strip single asterisks around words (*word* -> word) leaving **bold** intact
    cleaned = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'\1', cleaned)
    cleaned = re.sub(r'(?<!\*)\*(?!\*|\s)', '', cleaned)

    # 3. Strip Unicode emojis, pictographs, medals, flags
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols (food, faces, etc.)
        "\U0001FA00-\U0001FA6F"  # chess, symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended
        "\U00002600-\U000026FF"  # misc symbols
        "]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub("", cleaned)

    # Clean double spaces or double hyphens created by removals
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r' - - ', ' - ', cleaned)
    return cleaned.strip()

def _summarize_tool_execution(tool_name: str, args: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Creates a clean human-readable badge summary of a tool execution."""
    if tool_name == "get_top_merchants":
        cat = args.get("category")
        m = args.get("month")
        top = result.get("top_merchants", [])
        top_name = top[0]["merchant"] if top else "None"
        amt = top[0]["total_spent"] if top else 0.0
        desc = f"Ranked top {cat or 'spending'} destinations"
        if m:
            desc += f" in {m}"
        if top:
            desc += f": #{top[0]['rank']} {top_name} (₹{amt:,.0f})"
        return desc
    if tool_name == "get_salary_and_inflows":
        m = args.get("month") or "ledger"
        tot = result.get("total_month_inflow") or result.get("total_salary_amount", 0.0)
        sal = result.get("total_salary_amount", 0.0)
        if result.get("salary_detected"):
            return f"Audited {m} payroll: Detected ₹{sal:,.0f} salary (₹{tot:,.0f} total inflow)"
        else:
            return f"Audited {m} inflows: Total ₹{tot:,.0f} credits (no employer salary)"
    elif tool_name == "search_transactions":
        query = args.get("query", "")
        count = result.get("matches_count", 0)
        total = result.get("total_amount") or result.get("total_spent", 0.0)
        return f"Searched ledger for '{query}': Found {count} transactions (₹{total:,.0f} total)"
    elif tool_name == "get_category_trends":
        cat = args.get("category", "")
        total = result.get("total_category_spent", 0.0)
        return f"Analyzed trend for '{cat}' (₹{total:,.0f} total)"
    elif tool_name == "get_cashflow_summary":
        surplus = result.get("avg_monthly_surplus", 0.0)
        return f"Checked cashflow ledger: Net surplus +₹{surplus:,.0f}/mo"
    elif tool_name == "evaluate_loan_affordability":
        verdict = result.get("verdict", "")
        emi = args.get("monthly_emi", 0.0)
        return f"Audited loan feasibility for ₹{emi:,.0f}/mo EMI: {verdict}"
    elif tool_name == "simulate_goal":
        months = result.get("months_required") or result.get("optimized_months") or args.get("target_months") or 12
        return f"Simulated goal trajectory: Achievable in {months} months"
    elif tool_name == "get_subscriptions_and_burdens":
        count = result.get("subscriptions_count", 0)
        return f"Scanned recurring debits: {count} active subscriptions"
    elif tool_name == "get_top_merchants":
        return "Ranked top merchant spend destinations"
    return f"Executed tool: {tool_name}"

OUT_OF_SCOPE_PATTERN = re.compile(
    r"\b(insurance|insure|insurer|term plan|health cover|life cover|tax|taxes|80c|80d|itr|deductions?|"
    r"invest|investing|investment|investments|mutual funds?|stocks?|shares|equity|crypto|elss|ppf|nps|portfolio)\b"
)
SPENDING_QUESTION_PATTERN = re.compile(r"\b(spend|spent|spending|paid|pay|paying|how much|total|debits?|transactions?)\b")
OUT_OF_SCOPE_REPLY = (
    "That is outside what this app does: I can't give insurance, tax planning or investment advice. "
    "I can help with your spending though, for example how much you have paid in insurance premiums or "
    "investments this year, which categories are growing, or how much you could save toward a goal."
)

def _is_out_of_scope_request(text_lower: str) -> bool:
    """True for advice requests on insurance, tax or investments that are not questions about the user's own spending."""
    return bool(OUT_OF_SCOPE_PATTERN.search(text_lower)) and not SPENDING_QUESTION_PATTERN.search(text_lower)

def _generate_fallback_response(
    user_message: str,
    df: Optional[pd.DataFrame]
) -> Dict[str, Any]:
    """
    Deterministic rule-based response generator when Gemini API key is missing or network times out.
    """
    text_lower = user_message.lower()
    executed_tools = []

    # Out-of-scope advice requests (insurance, tax planning, investments)
    if _is_out_of_scope_request(text_lower):
        return {"content": OUT_OF_SCOPE_REPLY, "executed_tools": []}

    # 0. Salary & Inflow check
    if any(k in text_lower for k in ["salary", "earn", "income", "payroll", "credited", "inflow", "inflows"]):
        months_map = [
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
        ]
        found_m = None
        for m in months_map:
            if m in text_lower:
                found_m = m.capitalize()
                break
        res = execute_finneas_tool("get_salary_and_inflows", {"month": found_m}, df)
        executed_tools.append({
            "tool_name": "get_salary_and_inflows",
            "args": {"month": found_m},
            "summary": _summarize_tool_execution("get_salary_and_inflows", {"month": found_m}, res)
        })
        if res.get("found_for_month"):
            m_name = res.get("month_queried")
            tot = res.get("total_month_inflow", 0.0)
            if res.get("salary_detected"):
                sal = res.get("total_salary_amount", 0.0)
                reply = f"In **{m_name}**, your detected employer salary was **₹{sal:,.2f}**:\n\n"
                for s in res.get("salary_credits", []):
                    reply += f"- Credited on **{s['date']}**: ₹{s['amount']:,.2f} (*{s['narration']}*)\n"
                if res.get("other_credits_count", 0) > 0:
                    reply += f"\nYou also received **₹{res.get('other_credits_total', 0):,.2f}** in other credits (total {m_name} inflow: **₹{tot:,.2f}**)."
            else:
                reply = f"I scanned your ledger for **{m_name}**: No formal employer salary deposit was detected.\n\n"
                reply += f"- **Total Incoming Credits**: ₹{tot:,.2f} across {res.get('other_credits_count', 0)} transactions\n"
                if res.get("credit_sources_breakdown"):
                    reply += "- **Sources**: " + ", ".join([f"{k}: ₹{v:,.2f}" for k, v in res["credit_sources_breakdown"].items()]) + "\n\n"
                if res.get("all_credits_sample"):
                    reply += f"### Sample incoming credits received in {m_name}:\n"
                    for c in res["all_credits_sample"][:5]:
                        reply += f"- **{c['date']}**: ₹{c['amount']:,.2f} (*{c['narration'][:45]}*)\n"
        else:
            reply = res.get("message", "No inflow transactions found for the requested period.")
        return {"content": reply, "executed_tools": executed_tools}

    # 0.5. Top merchants / food stall query
    if any(k in text_lower for k in ["food stall", "stall", "merchant", "most", "spent the most", "highest spend", "top spend"]):
        cat = "food" if any(f in text_lower for f in ["food", "stall", "dining", "eating", "restaurant", "cafe", "biri", "biryani"]) else None
        m = "last month" if any(w in text_lower for w in ["last month", "previous month", "recent month"]) else None
        res = execute_finneas_tool("get_top_merchants", {"category": cat, "month": m, "limit": 5}, df)
        executed_tools.append({
            "tool_name": "get_top_merchants",
            "args": {"category": cat, "month": m},
            "summary": _summarize_tool_execution("get_top_merchants", {"category": cat, "month": m}, res)
        })
        if res.get("top_merchants"):
            top = res["top_merchants"]
            top_1 = top[0]
            period_str = f"in {res.get('month_filter')}" if res.get('month_filter') else "across your statement ledger"
            cat_str = "food destination" if cat else "merchant"
            reply = f"Based on your statement ledger, the {cat_str} you spent the most at {period_str} was **{top_1['merchant']}** with **₹{top_1['total_spent']:,.2f}** spent across {top_1['transactions_count']} orders (average order: ₹{top_1['average_ticket']:,.2f}).\n\n"
            reply += f"### Top {cat_str.capitalize()}s Ranked:\n"
            for r in top:
                reply += f"{r['rank']}. **{r['merchant']}**: ₹{r['total_spent']:,.2f} ({r['transactions_count']} orders, avg ₹{r['average_ticket']:,.2f})\n"
            return {"content": reply, "executed_tools": executed_tools}

    # 1. Search transactions / specific merchant query
    if any(k in text_lower for k in ["mcdonald", "spent on", "how much", "bought", "starbucks", "swiggy", "zomato", "amazon", "uber", "ola", "flipkart", "blinkit", "zepto"]):
        # Extract potential keyword
        match = re.search(r"(?:spent on|at|for|on)\s+([a-zA-Z0-9\s&]+?)(?:\s+over|\s+in|\s+last|\?|$)", user_message, re.IGNORECASE)
        query = match.group(1).strip() if match else "MCDONALDS"
        res = execute_finneas_tool("search_transactions", {"query": query, "months_back": 3}, df)
        executed_tools.append({
            "tool_name": "search_transactions",
            "args": {"query": query},
            "summary": _summarize_tool_execution("search_transactions", {"query": query}, res)
        })
        if res.get("found"):
            reply = f"Here is what I found in your statement ledger for **{query}** over the last 3 months:\n\n"
            reply += f"- **Total Spend**: ₹{res['total_spent']:,.2f}\n"
            reply += f"- **Transactions Count**: {res['matches_count']} orders\n"
            reply += f"- **Average Order**: ₹{res['average_ticket']:,.2f}\n"
            reply += f"- **Largest Single Purchase**: ₹{res['highest_transaction']:,.2f}\n\n"
            if res.get("monthly_breakdown"):
                reply += "### Monthly Breakdown:\n"
                for ym, amt in res["monthly_breakdown"].items():
                    reply += f"- **{ym}**: ₹{amt:,.2f}\n"
        else:
            reply = f"I scanned your loaded statement ledger, but couldn't find any transactions matching **'{query}'**. You might want to check the spelling or check if this was paid via a different bank account!"
        return {"content": reply, "executed_tools": executed_tools}

    # 2. Category trends
    if any(k in text_lower for k in ["trend", "food", "dining", "shopping", "groceries", "fuel", "entertainment"]):
        cat = "Food Delivery & Dining" if any(k in text_lower for k in ["food", "dining", "eating"]) else "Shopping"
        res = execute_finneas_tool("get_category_trends", {"category": cat}, df)
        executed_tools.append({
            "tool_name": "get_category_trends",
            "args": {"category": cat},
            "summary": _summarize_tool_execution("get_category_trends", {"category": cat}, res)
        })
        reply = f"Here is your historical spend velocity for **{cat}**:\n\n"
        reply += f"- **Total Category Spend**: ₹{res.get('total_category_spent', 0):,.2f}\n\n"
        if res.get("monthly_trend"):
            reply += "### Month-over-Month Velocity:\n"
            for m in res["monthly_trend"]:
                reply += f"- **{m['month']}**: ₹{m['total_spend']:,.2f} ({m['transactions_count']} transactions)\n"
        if res.get("top_sub_categories"):
            reply += "\n### Top Merchants in this Category:\n"
            for sm in res["top_sub_categories"]:
                reply += f"- **{sm['name']}**: ₹{sm['total_spend']:,.2f}\n"
        return {"content": reply, "executed_tools": executed_tools}

    # 3. Loan Affordability
    if any(k in text_lower for k in ["loan", "emi", "afford a", "borrow"]):
        emi_match = re.search(r"(\d[\d,]*)\s*(?:/mo|emi|per month)", text_lower)
        loan_match = re.search(r"(\d[\d,]*)\s*(?:lakh|lac|k|thousand|inr)", text_lower)
        
        emi = 12000.0
        if emi_match:
            try:
                emi = float(emi_match.group(1).replace(",", ""))
            except Exception:
                emi = 12000.0

        res = execute_finneas_tool("evaluate_loan_affordability", {"requested_loan_amount": 400000, "monthly_emi": emi}, df)
        executed_tools.append({
            "tool_name": "evaluate_loan_affordability",
            "args": {"monthly_emi": emi},
            "summary": _summarize_tool_execution("evaluate_loan_affordability", {"monthly_emi": emi}, res)
        })
        reply = f"### Loan Affordability Audit (EMI: ₹{emi:,.0f}/mo)\n\n"
        reply += f"**Verdict**: **{res['verdict']}**\n\n"
        reply += f"- **Current Monthly Statement Surplus**: +₹{res['current_monthly_surplus']:,.0f}/mo\n"
        reply += f"- **Remaining Surplus After EMI**: ₹{res['remaining_surplus_after_emi']:,.0f}/mo\n"
        reply += f"- **Surplus Consumption**: {res['debt_to_surplus_percentage']}% of your savings capacity\n\n"
        reply += f"💡 **Fiduciary Take**: {res['fiduciary_advice']}"
        return {"content": reply, "executed_tools": executed_tools}

    # 4. Cashflow Summary
    res = execute_finneas_tool("get_cashflow_summary", {}, df)
    executed_tools.append({
        "tool_name": "get_cashflow_summary",
        "args": {},
        "summary": _summarize_tool_execution("get_cashflow_summary", {}, res)
    })
    reply = f"Hi! Based on your active bank statement ledger, here is your financial snapshot:\n\n"
    reply += f"- **Monthly Inflow**: ₹{res.get('avg_monthly_income', 0):,.2f}/mo\n"
    reply += f"- **Monthly Living Burn**: ₹{res.get('avg_monthly_expense', 0):,.2f}/mo\n"
    reply += f"- **Net Monthly Surplus**: +₹{res.get('avg_monthly_surplus', 0):,.2f}/mo\n"
    reply += f"- **Ending Bank Balance Cushion**: ₹{res.get('ending_liquid_balance', 0):,.2f}\n\n"
    reply += "Feel free to ask me to drill down into any specific merchant, category trend, loan calculation, or goal planning!"
    return {"content": reply, "executed_tools": executed_tools}

def run_finneas_chat(
    thread_id: str,
    user_message: str,
    df: Optional[pd.DataFrame],
    user_vault_dir: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Orchestrates multi-turn conversation with Finneas.
    Executes tools dynamically via Gemini function calling and updates persistent thread history.
    Supports native multimodal analysis (PDFs, images) for document comparison and fine-print audit.
    """
    threads = load_threads(user_vault_dir)
    thread = None
    for t in threads:
        if t["id"] == thread_id:
            thread = t
            break

    if not thread:
        thread = create_new_thread(title=user_message[:36] + "...", user_vault_dir=user_vault_dir)
        thread_id = thread["id"]
        threads = load_threads(user_vault_dir)

    now_iso = datetime.datetime.now().isoformat()
    
    # Save attachments to disk in user's vault and build metadata
    saved_attachments = []
    if attachments:
        att_dir = os.path.join(user_vault_dir, "attachments")
        os.makedirs(att_dir, exist_ok=True)

        for att in attachments:
            att_id = f"att_{uuid.uuid4().hex[:8]}"
            orig_name = att.get("name", "document")
            mime_type = att.get("type", "application/octet-stream")
            raw_b64 = att.get("data", "")
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]

            safe_name = "".join(c for c in orig_name if c.isalnum() or c in "._- ")
            disk_filename = f"{att_id}_{safe_name}"
            disk_path = os.path.join(att_dir, disk_filename)

            try:
                with open(disk_path, "wb") as f:
                    f.write(base64.b64decode(raw_b64))
                file_size = os.path.getsize(disk_path)
            except Exception as e:
                print(f"[Finneas Agent] Error saving attachment to disk: {e}")
                file_size = att.get("size", 0)

            saved_attachments.append({
                "id": att_id,
                "name": orig_name,
                "type": mime_type,
                "size": file_size,
                "url": f"/api/finneas/attachments/{att_id}/{safe_name}"
            })

    # Auto-title on first user message
    if len(thread.get("messages", [])) == 0:
        clean_title = user_message.strip()
        if len(clean_title) > 36:
            clean_title = clean_title[:33] + "..."
        elif not clean_title and saved_attachments:
            clean_title = f"Audit: {saved_attachments[0]['name'][:28]}"
        thread["title"] = clean_title or "Document Audit"

    # Append user message with attachments metadata
    user_msg_entry = {
        "id": f"msg_u_{int(datetime.datetime.now().timestamp() * 1000)}",
        "role": "user",
        "content": user_message,
        "attachments": saved_attachments,
        "timestamp": now_iso
    }
    thread["messages"].append(user_msg_entry)

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    req_timeout = 45 if attachments else 15

    executed_tools = []
    final_content = ""

    if not api_key:
        fallback = _generate_fallback_response(user_message, df)
        final_content = fallback["content"]
        executed_tools = fallback["executed_tools"]
    else:
        # Build contents from message history
        gemini_contents = []
        for m in thread["messages"][-6:]: # Keep recent 6 turns for context
            role = "user" if m["role"] == "user" else "model"
            parts = []

            # If this is the current active user turn and attachments were provided, attach inlineData
            if m.get("id") == user_msg_entry["id"] and attachments:
                for att in attachments:
                    raw_b64 = att.get("data", "")
                    if "," in raw_b64:
                        raw_b64 = raw_b64.split(",", 1)[1]
                    mime_type = att.get("type", "application/pdf")
                    parts.append({
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": raw_b64
                        }
                    })

            parts.append({"text": m.get("content", "")})
            gemini_contents.append({
                "role": role,
                "parts": parts
            })

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "systemInstruction": {
                "parts": [{"text": FINNEAS_SYSTEM_PROMPT}]
            },
            "contents": gemini_contents,
            "tools": [{"functionDeclarations": GEMINI_TOOLS_DECLARATIONS}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 3072
            }
        }

        # Multi-hop tool execution loop
        max_hops = 6
        current_hop = 0

        while current_hop < max_hops:
            current_hop += 1
            try:
                resp = requests.post(endpoint, json=payload, timeout=req_timeout)
                if resp.status_code != 200:
                    print(f"[Finneas Agent] Gemini returned {resp.status_code}: {resp.text}")
                    fallback = _generate_fallback_response(user_message, df)
                    final_content = fallback["content"]
                    executed_tools = fallback["executed_tools"]
                    break

                res_json = resp.json()
                candidates = res_json.get("candidates", [])
                if not candidates:
                    break

                first_candidate = candidates[0]
                content_obj = first_candidate.get("content", {})
                parts = content_obj.get("parts", [])

                # Check if Gemini requested a functionCall
                function_call = None
                text_parts = []
                for p in parts:
                    if "functionCall" in p:
                        function_call = p["functionCall"]
                    elif "text" in p:
                        text_parts.append(p["text"])

                if not function_call:
                    final_content = "".join(text_parts).strip()
                    break

                # Execute requested function
                fn_name = function_call.get("name")
                fn_args = function_call.get("args", {})
                
                tool_output = execute_finneas_tool(fn_name, fn_args, df)
                executed_tools.append({
                    "tool_name": fn_name,
                    "args": fn_args,
                    "summary": _summarize_tool_execution(fn_name, fn_args, tool_output)
                })

                # Append model message with complete candidate content (preserves thoughtSignature, id, etc.)
                payload["contents"].append(content_obj)

                # Append function response to contents with role: "user"
                payload["contents"].append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": fn_name,
                            "response": {
                                "name": fn_name,
                                "content": tool_output
                            }
                        }
                    }]
                })

            except Exception as e:
                print(f"[Finneas Agent] Error during agent hop: {e}")
                fallback = _generate_fallback_response(user_message, df)
                final_content = fallback["content"]
                executed_tools = fallback["executed_tools"]
                break

        # If loop reached max_hops or broke without generating text, force a synthesis call
        if not final_content and executed_tools:
            try:
                # Omit functionDeclarations so Gemini outputs pure text response based on gathered tool data
                synthesis_payload = {
                    "systemInstruction": {
                        "parts": [{"text": FINNEAS_SYSTEM_PROMPT}]
                    },
                    "contents": payload["contents"],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 3072
                    }
                }
                synth_resp = requests.post(endpoint, json=synthesis_payload, timeout=req_timeout)
                if synth_resp.status_code == 200:
                    cand = synth_resp.json().get("candidates", [])
                    if cand:
                        text_pts = [p.get("text", "") for p in cand[0].get("content", {}).get("parts", [])]
                        final_content = "".join(text_pts).strip()
            except Exception as e:
                print(f"[Finneas Agent] Error during synthesis turn: {e}")

    if not final_content:
        final_content = "I've analyzed your financial ledger. Let me know if you would like me to drill down further into any specific transactions, trends, or loans!"

    # Clean response text to strictly remove emojis, em dashes, and raw single asterisks
    final_content = _clean_response_text(final_content)
    for t in executed_tools:
        if "summary" in t and isinstance(t["summary"], str):
            t["summary"] = _clean_response_text(t["summary"])

    # Append assistant response to thread
    bot_msg_entry = {
        "id": f"msg_a_{int(datetime.datetime.now().timestamp() * 1000)}",
        "role": "assistant",
        "content": final_content,
        "executed_tools": executed_tools,
        "timestamp": datetime.datetime.now().isoformat()
    }
    thread["messages"].append(bot_msg_entry)
    thread["updated_at"] = datetime.datetime.now().isoformat()

    # Save updated threads
    save_threads(threads, user_vault_dir)

    return {
        "thread_id": thread_id,
        "thread_title": thread["title"],
        "user_message": user_msg_entry,
        "assistant_message": bot_msg_entry
    }
