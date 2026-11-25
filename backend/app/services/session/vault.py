"""
Request-to-vault resolution.

Every API request is mapped to an isolated storage directory ("vault").
Today the mapping is an anonymous browser session: the frontend generates a
random UUIDv4, stores it locally, and sends it in the X-Session-ID header.

`resolve_vault(request)` is the single place that decides which directory a
request may read and write. To switch to authenticated accounts later, replace
its body (e.g. derive the directory from a verified login token) and keep the
signature unchanged.
"""

import os
import re

from fastapi import HTTPException, Request

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
VAULT_ROOT = os.path.join(PROJECT_ROOT, "vault_storage")
SESSIONS_DIR = os.path.join(VAULT_ROOT, "sessions")

SESSION_HEADER = "X-Session-ID"
_SESSION_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def get_session_id(request: Request) -> str:
    """Returns the validated session ID for this request or rejects the request."""
    session_id = (request.headers.get(SESSION_HEADER) or "").strip().lower()
    if not _SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Missing or invalid session ID.")
    return session_id


def resolve_vault(request: Request) -> str:
    """Returns (and creates if needed) the storage directory for this request."""
    vault = os.path.join(SESSIONS_DIR, get_session_id(request))
    os.makedirs(vault, exist_ok=True)
    return vault
