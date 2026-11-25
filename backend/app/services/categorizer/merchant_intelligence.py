"""
Merchant Intelligence Engine - finMan
Handles merchant dictionary persistence, Gemini 3.5 Flash Lite batch zero-shot classification,
and confidence-routed category resolution.
"""

import os
import re
import json
import datetime
import requests
from typing import Any, Callable, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Standard Subcategory to Macro Category Mapping
SUB_TO_MACRO: Dict[str, str] = {
    # Discretionary
    "Food Delivery & Dining": "Discretionary",
    "Shopping & E-Commerce": "Discretionary",
    "Entertainment & Outings": "Discretionary",
    "Travel & Vacation": "Discretionary",
    "Local Shopping & Services": "Discretionary",
    
    # Variable Essentials
    "Groceries & Supplies": "Variable Essentials",
    "Healthcare & Eyewear": "Variable Essentials",
    "Education & Academic": "Variable Essentials",
    "Fuel & Commute": "Variable Essentials",
    "Ride Hailing & Auto": "Variable Essentials",
    "Public Transit & Metro": "Variable Essentials",
    
    # Fixed Expenses
    "Utilities & Bills": "Fixed Expenses",
    "Subscriptions": "Fixed Expenses",
    "Cloud & Tech Tools": "Fixed Expenses",
    "Insurance Premiums": "Fixed Expenses",
    "Loan EMIs & Rent": "Fixed Expenses",
    
    # Transfers & P2P
    "Transfer to Friends & Contacts": "Transfers & P2P",
    
    # Daily Micro-Spends
    "Local Vendor / Street Pay": "Daily Micro-Spends",
    
    # Income
    "Bank Interest": "Income",
    "Cashbacks & Rewards": "Income",
    "Refunds & Reversals": "Income",
    "Salary": "Income",
    "Transfers In (P2P)": "Income",
}

AVAILABLE_SUBCATEGORIES = list(SUB_TO_MACRO.keys())

def normalize_merchant_key(name: str) -> str:
    """Normalize raw merchant string to a clean uppercase key."""
    if not name:
        return "UNKNOWN"
    clean = str(name).strip().upper()
    # Remove excessive punctuation and whitespace
    clean = re.sub(r'[/\\_,-]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean or "UNKNOWN"

def get_dictionary_path(vault_dir: str) -> str:
    return os.path.join(vault_dir, "merchant_dictionary.json")

def load_merchant_dictionary(vault_dir: str) -> Dict[str, Any]:
    dict_path = get_dictionary_path(vault_dir)
    if not os.path.exists(dict_path):
        return {}
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading merchant dictionary: {e}")
        return {}

def save_merchant_dictionary(vault_dir: str, dictionary: Dict[str, Any]) -> bool:
    dict_path = get_dictionary_path(vault_dir)
    try:
        with open(dict_path, "w", encoding="utf-8") as f:
            json.dump(dictionary, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving merchant dictionary: {e}")
        return False

def map_to_standard_category(sub_cat_candidate: str, cat_candidate: str = "") -> Tuple[str, str]:
    """Map LLM returned category string to standard finMan categories."""
    cand_lower = (sub_cat_candidate or "").lower().strip()
    
    # Exact or substring match in standard keys
    for std_sub, macro in SUB_TO_MACRO.items():
        if cand_lower == std_sub.lower():
            return macro, std_sub
        if cand_lower in std_sub.lower() or std_sub.lower() in cand_lower:
            return macro, std_sub
            
    # Fuzzy heuristic matching on common synonyms
    if any(w in cand_lower for w in ["food", "dining", "restaurant", "cafe", "bakery", "biryani", "canteen", "mess"]):
        return "Discretionary", "Food Delivery & Dining"
    if any(w in cand_lower for w in ["grocery", "kirana", "supermarket", "provisions"]):
        return "Variable Essentials", "Groceries & Supplies"
    if any(w in cand_lower for w in ["health", "medical", "pharmacy", "doctor", "clinic", "eyewear", "glasses"]):
        return "Variable Essentials", "Healthcare & Eyewear"
    if any(w in cand_lower for w in ["education", "hostel", "college", "school", "tuition", "academic"]):
        return "Variable Essentials", "Education & Academic"
    if any(w in cand_lower for w in ["shopping", "retail", "clothing", "apparel", "ecommerce", "e-commerce"]):
        return "Discretionary", "Shopping & E-Commerce"
    if any(w in cand_lower for w in ["ride", "cab", "auto", "taxi"]):
        return "Variable Essentials", "Ride Hailing & Auto"
    if any(w in cand_lower for w in ["metro", "bus", "train", "transit"]):
        return "Variable Essentials", "Public Transit & Metro"
    if any(w in cand_lower for w in ["subscription", "streaming", "ott", "saas"]):
        return "Fixed Expenses", "Subscriptions"
    if any(w in cand_lower for w in ["cloud", "hosting", "developer", "aws", "tech tool"]):
        return "Fixed Expenses", "Cloud & Tech Tools"
    if any(w in cand_lower for w in ["utility", "electric", "water", "recharge", "broadband", "bill"]):
        return "Fixed Expenses", "Utilities & Bills"
    if any(w in cand_lower for w in ["transfer", "friend", "personal", "p2p"]):
        return "Transfers & P2P", "Transfer to Friends & Contacts"
    if any(w in cand_lower for w in ["local", "vendor", "street", "stall"]):
        return "Daily Micro-Spends", "Local Vendor / Street Pay"

    # Default fallback
    return "Discretionary", "Local Shopping & Services"

def call_gemini_batch_classifier(merchants_to_resolve: List[Dict[str, str]], batch_size: int = 25) -> Dict[str, Dict[str, Any]]:
    """
    Calls Gemini 3.5 Flash Lite via Google Generative Language REST API in chunked batches.
    Input: list of {"merchant_key": "...", "normalized_key": "...", "sample_narration": "..."}
    Returns mapping: {normalized_key: {"category": ..., "sub_category": ..., "confidence": ..., "reasoning": ...}}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[finMan Intelligence] GEMINI_API_KEY not configured. Skipping LLM call.")
        return {}

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    categories_list = "\n".join(f"- {sub}" for sub in AVAILABLE_SUBCATEGORIES)
    results_map: Dict[str, Dict[str, Any]] = {}

    total_chunks = (len(merchants_to_resolve) + batch_size - 1) // batch_size
    for b_idx in range(0, len(merchants_to_resolve), batch_size):
        chunk = merchants_to_resolve[b_idx:b_idx + batch_size]
        chunk_num = (b_idx // batch_size) + 1
        print(f"[finMan Intelligence] Classifying chunk {chunk_num}/{total_chunks} ({len(chunk)} items)...")

        batch_input = [
            {
                "id": i + 1,
                "merchant": it.get("merchant_key", ""),
                "narration": it.get("sample_narration", "")
            }
            for i, it in enumerate(chunk)
        ]

        prompt = f"""You are FinSight's Indian Fintech Merchant Intelligence model.
Analyze each Indian bank and UPI merchant/vendor and categorize into one of these standard sub-categories:

Standard Sub-Categories:
{categories_list}

Merchants to classify:
{json.dumps(batch_input, indent=2)}

Guidelines:
1. UPI handles (like @hdfc, @airp, @ybl) or merchant codes (e.g. cf.isthara, zomato1pay, Vyapar.175) give direct business clues.
2. If it's a known Indian restaurant/food chain/mess/bakery (e.g., Zaitoon, Isthara, SRS Biryani, Unavagam, Frankie), classify as "Food Delivery & Dining".
3. If it's an educational campus hostel/college service (e.g., IITM HOS), classify as "Education & Academic".
4. If it's an individual student or person (e.g., student roll numbers, personal names, P2P transfers), classify as "Transfer to Friends & Contacts".
5. If it's a grocery/supermarket/quick-commerce service (e.g., Blinkit, Zepto, Swiggy Instamart, Kirana), classify as "Groceries & Supplies".
6. If it's pharmacy/medical (e.g., Apollo Pharmacy, Ashwini Pharmacy), classify as "Healthcare & Eyewear".
7. If it's movie theatre / entertainment (e.g., PVR INOX, District Movies), classify as "Entertainment & Outings".
8. If it's bus/train/metro/flight (e.g., IRCTC, Redbus, Chennai Metro, TSRTC), classify as "Public Transit & Metro" or "Travel & Vacation".
9. If it's recharge or utility bill (e.g., Mobile recharged, Reliance Jio), classify as "Utilities & Bills".
10. If it's a local shop/vendor that cannot be identified from public Indian merchant context, classify as "Local Shopping & Services" or "Local Vendor / Street Pay" and assign a lower confidence (< 0.50).
11. Confidence should be between 0.0 and 1.0 based on certainty.

Return ONLY a valid JSON array of objects with the exact schema:
[
  {{"id": 1, "sub_category": "one of the standard sub-categories", "confidence": 0.95, "reasoning": "brief 1-sentence reason"}}
]"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        # Attempt call with 1 retry on timeout or network error
        chunk_success = False
        for attempt in range(2):
            try:
                resp = requests.post(endpoint, json=payload, timeout=35)
                if resp.status_code != 200:
                    print(f"[finMan Intelligence] Chunk {chunk_num} API status {resp.status_code}: {resp.text[:150]}")
                    continue

                resp_data = resp.json()
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    continue

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    continue

                raw_text = parts[0].get("text", "")
                parsed_results = json.loads(raw_text)

                for r in parsed_results:
                    item_id = r.get("id")
                    if item_id is not None and 1 <= item_id <= len(chunk):
                        target_key = chunk[item_id - 1]["normalized_key"]
                    else:
                        target_key = normalize_merchant_key(r.get("merchant_key", ""))

                    subcat = r.get("sub_category", "Local Shopping & Services")
                    macro, validated_subcat = map_to_standard_category(subcat)
                    conf = float(r.get("confidence", 0.5))
                    reasoning = str(r.get("reasoning", "")).strip()

                    results_map[target_key] = {
                        "category": macro,
                        "sub_category": validated_subcat,
                        "confidence": round(conf, 2),
                        "reasoning": reasoning
                    }
                chunk_success = True
                break
            except Exception as e:
                print(f"[finMan Intelligence] Chunk {chunk_num} attempt {attempt+1} exception: {e}")

        if not chunk_success:
            print(f"[finMan Intelligence] Chunk {chunk_num} failed after retries.")

    return results_map

def resolve_unknown_merchants_with_intelligence(
    merchants_info: List[Dict[str, str]], 
    vault_dir: str,
    confidence_threshold: float = 0.50,
    force_reclassify: bool = False,
    ai_gate: Optional[Callable[[], bool]] = None
) -> Dict[str, Any]:
    """
    Main pipeline entrypoint:
    1. Checks existing merchant_dictionary.json
    2. Identifies standard commercial merchants via verified entity rules (KNOWN_PATTERNS)
       (e.g., Blinkit, Swiggy, Zepto, KFC, Apollo, Uber, IRCTC, AWS, Jio, etc.) with 99% confidence.
    3. Identifies truly ambiguous / unknown local merchants.
    4. Batches ambiguous merchants to Gemini 3.5 Flash Lite in 25-item chunks for genuine live AI classification.
    5. Applies confidence threshold (>= 0.5 auto-accept, < 0.5 flag review).
    6. Persists updated dictionary.
    If `ai_gate` is given it is called before using Gemini; when it returns False (daily AI
    limit reached) ambiguous merchants get rule-based fallback entries flagged for review.
    """
    from app.services.categorizer.rules import KNOWN_PATTERNS

    dictionary = load_merchant_dictionary(vault_dir)
    unresolved_items: List[Dict[str, str]] = []
    seen_keys = set()
    now_iso = datetime.datetime.now().isoformat()

    for item in merchants_info:
        raw_name = item.get("name", "")
        key = normalize_merchant_key(raw_name)
        if not key or key == "UNKNOWN":
            continue

        sample_narr = item.get("sample_narration", "")

        # 1. Check if matched by standard high-certainty rules
        matched_rule = False
        for pat, cat, subcat in KNOWN_PATTERNS:
            if re.search(pat, sample_narr) or re.search(pat, raw_name):
                # Auto-verify via known rule
                if key not in dictionary or dictionary[key].get("source") == "fallback" or force_reclassify:
                    dictionary[key] = {
                        "merchant_key": key,
                        "display_name": raw_name,
                        "category": cat,
                        "sub_category": subcat,
                        "confidence": 0.99,
                        "reasoning": "Identified via standard verified entity registry",
                        "source": "rule",
                        "verified": True,
                        "needs_review": False,
                        "sample_narration": sample_narr,
                        "updated_at": now_iso
                    }
                matched_rule = True
                break

        if matched_rule:
            continue

        # 2. If already known and genuine (from LLM or user verified), skip re-classifying unless force_reclassify
        if not force_reclassify and key in dictionary:
            entry = dictionary[key]
            if entry.get("source") == "llm" or entry.get("verified"):
                continue

        # 3. Truly ambiguous merchant -> send to Gemini
        if key not in seen_keys:
            seen_keys.add(key)
            unresolved_items.append({
                "merchant_key": raw_name,
                "normalized_key": key,
                "sample_narration": sample_narr
            })

    if not unresolved_items:
        save_merchant_dictionary(vault_dir, dictionary)
        return dictionary

    if ai_gate is not None and not ai_gate():
        print(f"[finMan Intelligence] Daily AI limit reached; {len(unresolved_items)} merchants flagged for review.")
        llm_results = {}
    else:
        print(f"[finMan Intelligence] Batch classifying {len(unresolved_items)} ambiguous merchants with Gemini...")
        llm_results = call_gemini_batch_classifier(unresolved_items, batch_size=25)

    now_iso = datetime.datetime.now().isoformat()

    for item in unresolved_items:
        key = item["normalized_key"]
        raw_name = item["merchant_key"]
        sample_narr = item["sample_narration"]

        if key in llm_results:
            info = llm_results[key]
            conf = info["confidence"]
            needs_review = conf < confidence_threshold
            
            dictionary[key] = {
                "merchant_key": key,
                "display_name": raw_name,
                "category": info["category"],
                "sub_category": info["sub_category"],
                "confidence": conf,
                "reasoning": info["reasoning"],
                "source": "llm",
                "verified": not needs_review, # auto-verified if >= threshold
                "needs_review": needs_review,
                "sample_narration": sample_narr,
                "updated_at": now_iso
            }
        else:
            # Fallback if LLM failed or missed this item
            dictionary[key] = {
                "merchant_key": key,
                "display_name": raw_name,
                "category": "Discretionary",
                "sub_category": "Local Shopping & Services",
                "confidence": 0.30,
                "reasoning": "Unrecognized merchant, defaulted to general shopping",
                "source": "fallback",
                "verified": False,
                "needs_review": True,
                "sample_narration": sample_narr,
                "updated_at": now_iso
            }

    save_merchant_dictionary(vault_dir, dictionary)
    return dictionary
