"""
Demo accounts.

A demo template (parsed statement, categorized ledger and merchant dictionary) is
built once from the demo sample statement into vault_storage/demo_template/. Each
demo login creates a new throwaway account and copies the template into that
account's own vault, so visitors never share data and nothing writes to the
template or to the original sample file. Demo accounts expire after 24 hours and
are deleted by `cleanup_expired`.
"""

import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
from typing import Any, Callable, Dict

from app.services.auth import store
from app.services.session.vault import PROJECT_ROOT, VAULT_ROOT, account_vault_path

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
DEMO_SAMPLE_ID = "vikram_malhotra_1year_statement"
DEMO_SAMPLE_PATH = os.path.join(PROJECT_ROOT, "sample_statements", f"{DEMO_SAMPLE_ID}.csv")
TEMPLATE_DIR = os.path.join(VAULT_ROOT, "demo_template")
_MARKER = "template.json"

_template_lock = threading.Lock()


def _sample_checksum() -> str:
    with open(DEMO_SAMPLE_PATH, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _template_is_current(checksum: str) -> bool:
    try:
        with open(os.path.join(TEMPLATE_DIR, _MARKER), encoding="utf-8") as fh:
            return json.load(fh).get("sample_sha256") == checksum
    except (OSError, ValueError):
        return False


def ensure_template(build: Callable[[str, str], None]) -> str:
    """
    Builds the demo template if it is missing or the sample file changed.
    `build(sample_path, target_dir)` must ingest the sample into target_dir.
    """
    checksum = _sample_checksum()
    with _template_lock:
        if _template_is_current(checksum):
            return TEMPLATE_DIR
        os.makedirs(VAULT_ROOT, exist_ok=True)
        staging = tempfile.mkdtemp(prefix="demo_template_build_", dir=VAULT_ROOT)
        try:
            build(DEMO_SAMPLE_PATH, staging)
            with open(os.path.join(staging, _MARKER), "w", encoding="utf-8") as fh:
                json.dump({"sample_id": DEMO_SAMPLE_ID, "sample_sha256": checksum, "built_at": time.time()}, fh)
            shutil.rmtree(TEMPLATE_DIR, ignore_errors=True)
            os.replace(staging, TEMPLATE_DIR)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    return TEMPLATE_DIR


def create_demo_account(build: Callable[[str, str], None]) -> Dict[str, Any]:
    """Creates a fresh demo account with its own copy of the demo data and returns it."""
    template = ensure_template(build)
    user = store.create_demo_user()
    vault = account_vault_path(user["id"])
    try:
        shutil.copytree(template, vault, ignore=shutil.ignore_patterns(_MARKER))
    except Exception:
        delete_account(user["id"])
        raise
    return user


def delete_account(user_id: str) -> None:
    """Deletes an account, its sessions and its stored data."""
    store.delete_user(user_id)
    shutil.rmtree(account_vault_path(user_id), ignore_errors=True)


def cleanup_expired(now: float = None) -> int:
    """Deletes demo accounts past their 24-hour lifetime and any expired sessions. Returns accounts removed."""
    expired = store.expired_demo_user_ids(now)
    for user_id in expired:
        delete_account(user_id)
    store.delete_expired_sessions(now)
    return len(expired)
