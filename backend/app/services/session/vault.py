"""
Request-to-vault resolution.

Every API request is mapped to an isolated storage directory ("vault") that belongs
to the logged-in account. Identity comes only from the session cookie, which is
verified against the auth store on every request; there is no default user.

`resolve_vault(request)` is the single place that decides which directory a
request may read and write.
"""

import os
from typing import Any, Dict

from fastapi import HTTPException, Request

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
# FINSIGHT_VAULT_ROOT lets tests point all storage at a temporary directory
VAULT_ROOT = os.environ.get("FINSIGHT_VAULT_ROOT") or os.path.join(PROJECT_ROOT, "vault_storage")
ACCOUNTS_DIR = os.path.join(VAULT_ROOT, "accounts")

SESSION_COOKIE = "finsight_session"


def account_vault_path(user_id: str) -> str:
    """Storage directory for an account. user_id is a random hex ID, never user input."""
    if not user_id or not user_id.isalnum():
        raise ValueError("Invalid account id")
    return os.path.join(ACCOUNTS_DIR, user_id)


def get_authenticated_user(request: Request) -> Dict[str, Any]:
    """Returns the account for this request's session cookie, or raises 401."""
    cached = getattr(request.state, "user", None)
    if cached:
        return cached
    # Imported here to avoid a circular import (the auth store uses the paths above)
    from app.services.auth.store import get_user_for_token

    user = get_user_for_token(request.cookies.get(SESSION_COOKIE, ""))
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    request.state.user = user
    return user


def resolve_vault(request: Request) -> str:
    """Returns (and creates if needed) the storage directory of the logged-in account."""
    vault = account_vault_path(get_authenticated_user(request)["id"])
    os.makedirs(vault, exist_ok=True)
    return vault
