"""
finMan Multi-User Authentication and Persistent Vault Manager.
Handles user registration, authentication, isolated storage sandboxing,
auto-migration of personal statements, and pre-seeding of demo personas.
"""

import os
import json
import shutil
import glob
from typing import Dict, Any, List, Optional
import pandas as pd

from app.services.insurance.personas import PERSONAS, generate_persona_transactions

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
VAULT_DIR = os.path.join(PROJECT_ROOT, "vault_storage")
USERS_DIR = os.path.join(VAULT_DIR, "users")
REGISTRY_PATH = os.path.join(VAULT_DIR, "users_registry.json")

DEFAULT_USERS: List[Dict[str, Any]] = [
    {
        "id": "usr_azizul",
        "username": "azizul",
        "name": "Azizul Hoque",
        "email": "azizul@finman.local",
        "pin": "1234",
        "is_persona": False,
        "avatar_initials": "AH",
        "color": "blue",
        "tagline": "Personal Financial Vault",
        "annual_income": 1260000.0,
        "outstanding_loans": 680000.0,
        "liquid_assets": 500000.0,
        "dependents": 2
    },
    {
        "id": "usr_vikram",
        "username": "vikram",
        "name": "Vikram Malhotra",
        "email": "vikram@finman.local",
        "pin": "1234",
        "is_persona": True,
        "avatar_initials": "VM",
        "color": "amber",
        "tagline": "34y, Married with Home Loan & LIC Trap",
        "persona_key": "vikram_young_family",
        "annual_income": 2520000.0,
        "outstanding_loans": 4800000.0,
        "liquid_assets": 1250000.0,
        "dependents": 2
    },
    {
        "id": "usr_priya",
        "username": "priya",
        "name": "Priya Nair",
        "email": "priya@finman.local",
        "pin": "1234",
        "is_persona": True,
        "avatar_initials": "PN",
        "color": "purple",
        "tagline": "27y, Single Tech Pro with Car Loan & GMC",
        "persona_key": "priya_tech_pro",
        "annual_income": 1620000.0,
        "outstanding_loans": 520000.0,
        "liquid_assets": 420000.0,
        "dependents": 0
    },
    {
        "id": "usr_aarav",
        "username": "aarav",
        "name": "Aarav Sharma",
        "email": "aarav@finman.local",
        "pin": "1234",
        "is_persona": True,
        "avatar_initials": "AS",
        "color": "emerald",
        "tagline": "22y, College Intern with Zero Dependents",
        "persona_key": "aarav_intern",
        "annual_income": 540000.0,
        "outstanding_loans": 0.0,
        "liquid_assets": 65000.0,
        "dependents": 0
    },
    {
        "id": "usr_sunita",
        "username": "sunita",
        "name": "Sunita Sengupta",
        "email": "sunita@finman.local",
        "pin": "1234",
        "is_persona": True,
        "avatar_initials": "SS",
        "color": "rose",
        "tagline": "43y, Senior Director with Elderly Parents",
        "persona_key": "sunita_senior_parents",
        "annual_income": 4560000.0,
        "outstanding_loans": 0.0,
        "liquid_assets": 4500000.0,
        "dependents": 3
    },
    {
        "id": "usr_anand",
        "username": "anand",
        "name": "Anand Vardhan",
        "email": "anand@finman.local",
        "pin": "1234",
        "is_persona": True,
        "avatar_initials": "AV",
        "color": "indigo",
        "tagline": "39y, MSME Owner with Business Loans",
        "persona_key": "anand_entrepreneur",
        "annual_income": 3840000.0,
        "outstanding_loans": 3500000.0,
        "liquid_assets": 1800000.0,
        "dependents": 3
    }
]

def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def load_users_registry() -> List[Dict[str, Any]]:
    """Loads all user accounts from the persistent registry."""
    _ensure_dir(VAULT_DIR)
    if not os.path.exists(REGISTRY_PATH):
        save_users_registry(DEFAULT_USERS)
        return DEFAULT_USERS
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", DEFAULT_USERS)
    except Exception as e:
        print(f"[finMan Auth] Error loading registry: {e}")
        return DEFAULT_USERS

def save_users_registry(users: List[Dict[str, Any]]) -> bool:
    """Saves user accounts to the persistent registry."""
    _ensure_dir(VAULT_DIR)
    try:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, indent=2)
        return True
    except Exception as e:
        print(f"[finMan Auth] Error writing registry: {e}")
        return False

def get_user_vault_path(username: str) -> str:
    """Returns the dedicated directory path for a specific user."""
    clean_username = username.strip().lower()
    user_dir = os.path.join(USERS_DIR, clean_username)
    _ensure_dir(user_dir)
    return user_dir

def initialize_and_migrate_vault():
    """
    Auto-migrates existing statements into the azizul user account,
    and pre-seeds synthetic demo accounts.
    """
    _ensure_dir(VAULT_DIR)
    _ensure_dir(USERS_DIR)

    # 1. Initialize registry if missing
    registry = load_users_registry()

    # 2. Migrate existing root vault data into azizul account
    azizul_dir = get_user_vault_path("azizul")
    root_manifest = os.path.join(VAULT_DIR, "manifest.json")
    azizul_manifest = os.path.join(azizul_dir, "manifest.json")

    if os.path.exists(root_manifest) and not os.path.exists(azizul_manifest):
        print("[finMan Auth] Migrating root vault statements to azizul account...")
        # Copy manifest
        shutil.copy2(root_manifest, azizul_manifest)
        
        # Copy active ledger if exists
        root_ledger = os.path.join(VAULT_DIR, "active_unified_ledger.csv")
        if os.path.exists(root_ledger):
            shutil.copy2(root_ledger, os.path.join(azizul_dir, "active_unified_ledger.csv"))

        # Copy merchant dictionary if exists
        root_dict = os.path.join(VAULT_DIR, "merchant_dictionary.json")
        if os.path.exists(root_dict):
            shutil.copy2(root_dict, os.path.join(azizul_dir, "merchant_dictionary.json"))

        # Copy insurance profile if exists
        root_ins = os.path.join(VAULT_DIR, "insurance_profile.json")
        if os.path.exists(root_ins):
            shutil.copy2(root_ins, os.path.join(azizul_dir, "insurance_profile.json"))

        # Copy all CSV/PDF files in root vault
        for ext in ("*.csv", "*.pdf"):
            for f in glob.glob(os.path.join(VAULT_DIR, ext)):
                dest = os.path.join(azizul_dir, os.path.basename(f))
                if not os.path.exists(dest):
                    shutil.copy2(f, dest)

        print("[finMan Auth] Migration to azizul account completed successfully.")

    # 3. Pre-seed demo persona accounts
    for u in registry:
        if u.get("is_persona") and u.get("persona_key"):
            pkey = u["persona_key"]
            p_dir = get_user_vault_path(u["username"])
            p_manifest = os.path.join(p_dir, "manifest.json")

            needs_seed = True
            ledger_file = os.path.join(p_dir, "active_unified_ledger.csv")
            if os.path.exists(p_manifest) and os.path.exists(ledger_file):
                try:
                    df_check = pd.read_csv(ledger_file)
                    if len(df_check) >= 150:
                        needs_seed = False
                except Exception:
                    needs_seed = True

            if needs_seed:
                p_info = PERSONAS.get(pkey)
                if p_info:
                    print(f"[finMan Auth] Pre-seeding demo persona {u['username']} with 1-year dataset...")
                    df_persona = generate_persona_transactions(pkey)
                    if "sub_category" not in df_persona.columns:
                        df_persona["sub_category"] = df_persona["category"]
                    if "merchant" not in df_persona.columns:
                        df_persona["merchant"] = df_persona["narration"].apply(lambda n: str(n)[:25])
                    
                    # 1. Save master ledger
                    df_persona.to_csv(ledger_file, index=False)

                    # 2. Save statement CSV
                    stmt_filename = f"{u['username']}_statement.csv"
                    stmt_path = os.path.join(p_dir, stmt_filename)
                    df_persona.to_csv(stmt_path, index=False)

                    # 3. Create manifest
                    manifest_data = [
                        {
                            "id": f"stmt_{u['username']}_01",
                            "filename": f"{u['name']} Bank Statement",
                            "stored_file": stmt_filename,
                            "tx_count": len(df_persona),
                            "file_size": os.path.getsize(stmt_path),
                            "uploaded_at": "2026-10-22T00:00:00Z"
                        }
                    ]
                    with open(p_manifest, "w", encoding="utf-8") as f:
                        json.dump(manifest_data, f, indent=2)

                    # 4. Save insurance profile with persona declared policies
                    ins_file = os.path.join(p_dir, "insurance_profile.json")
                    with open(ins_file, "w", encoding="utf-8") as f:
                        json.dump({"declared_policies": p_info.get("declared_policies", [])}, f, indent=2)

                    # 5. Default merchant dictionary
                    dict_file = os.path.join(p_dir, "merchant_dictionary.json")
                    with open(dict_file, "w", encoding="utf-8") as f:
                        json.dump({}, f, indent=2)

def authenticate_user(username: str, pin: str) -> Optional[Dict[str, Any]]:
    """Authenticates credentials against the user registry."""
    clean_user = username.strip().lower()
    users = load_users_registry()
    for u in users:
        if u["username"].lower() == clean_user:
            if str(u.get("pin", "1234")).strip() == str(pin).strip():
                # Return sanitized user profile
                return {
                    "id": u["id"],
                    "username": u["username"],
                    "name": u["name"],
                    "email": u.get("email", ""),
                    "is_persona": u.get("is_persona", False),
                    "avatar_initials": u.get("avatar_initials", u["name"][:2].upper()),
                    "color": u.get("color", "blue"),
                    "tagline": u.get("tagline", ""),
                    "annual_income": u.get("annual_income", 1200000.0),
                    "outstanding_loans": u.get("outstanding_loans", 0.0),
                    "liquid_assets": u.get("liquid_assets", 500000.0),
                    "dependents": u.get("dependents", 0)
                }
    return None

def register_user(name: str, username: str, pin: str, email: str = "") -> Dict[str, Any]:
    """Registers a new user account with an isolated personal vault."""
    clean_user = username.strip().lower()
    users = load_users_registry()
    
    # Check if username exists
    for u in users:
        if u["username"].lower() == clean_user:
            raise ValueError(f"Username '{clean_user}' is already registered.")

    initials = "".join([part[0].upper() for part in name.strip().split() if part])[:2] or clean_user[:2].upper()
    
    new_user = {
        "id": f"usr_{clean_user}",
        "username": clean_user,
        "name": name.strip(),
        "email": email.strip() or f"{clean_user}@finman.local",
        "pin": pin.strip() or "1234",
        "is_persona": False,
        "avatar_initials": initials,
        "color": "blue",
        "tagline": "Personal Financial Vault",
        "annual_income": 1200000.0,
        "outstanding_loans": 0.0,
        "liquid_assets": 500000.0,
        "dependents": 0
    }

    users.append(new_user)
    save_users_registry(users)
    
    # Create user folder
    u_dir = get_user_vault_path(clean_user)
    with open(os.path.join(u_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
    with open(os.path.join(u_dir, "merchant_dictionary.json"), "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
    with open(os.path.join(u_dir, "insurance_profile.json"), "w", encoding="utf-8") as f:
        json.dump({"declared_policies": []}, f, indent=2)

    return new_user

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetches user details by username."""
    clean_user = username.strip().lower()
    users = load_users_registry()
    for u in users:
        if u["username"].lower() == clean_user:
            return u
    return None

def list_demo_personas() -> List[Dict[str, Any]]:
    """Returns all pre-seeded demo persona user profiles."""
    users = load_users_registry()
    return [u for u in users if u.get("is_persona")]

# Auto-initialize and migrate on module import
initialize_and_migrate_vault()
