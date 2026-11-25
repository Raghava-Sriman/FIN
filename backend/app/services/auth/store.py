"""
Accounts and login sessions, stored in SQLite (<FINSIGHT_DATA_DIR>/auth.db).

- Passwords are hashed with Argon2id (argon2-cffi).
- Session tokens are 256-bit random values; only their SHA-256 hash is stored, so a
  leaked database does not contain usable tokens.
- Every session and every demo account has a server-side expiry.
"""

import hashlib
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing
from typing import Any, Dict, List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "auth.db")

USER_SESSION_TTL_SECONDS = 7 * 24 * 3600
DEMO_TTL_SECONDS = 24 * 3600

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,32}$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
RESERVED_USERNAME_PREFIX = "demo"

_hasher = PasswordHasher()
# Verified against when the username does not exist, so response time does not reveal which usernames exist
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


class AuthError(ValueError):
    """A registration or validation problem that is safe to show to the user."""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with closing(_connect()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                expires_at REAL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            """
        )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "is_demo": bool(row["is_demo"]),
        "expires_at": row["expires_at"],
    }


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def validate_new_credentials(username: str, password: str) -> str:
    """Returns the normalized username or raises AuthError."""
    name = normalize_username(username)
    if not USERNAME_PATTERN.match(name):
        raise AuthError("Username must be 3-32 characters: lowercase letters, numbers or underscores.")
    if name.startswith(RESERVED_USERNAME_PREFIX):
        raise AuthError("That username is reserved. Please choose another.")
    if not (MIN_PASSWORD_LENGTH <= len(password or "") <= MAX_PASSWORD_LENGTH):
        raise AuthError(f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters.")
    return name


def create_user(username: str, password: str) -> Dict[str, Any]:
    """Registers a normal account. Raises AuthError if invalid or taken."""
    name = validate_new_credentials(username, password)
    user_id = uuid.uuid4().hex
    try:
        with closing(_connect()) as conn, conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, is_demo, created_at) VALUES (?, ?, ?, 0, ?)",
                (user_id, name, _hasher.hash(password), time.time()),
            )
    except sqlite3.IntegrityError:
        raise AuthError("That username is already taken.")
    return {"id": user_id, "username": name, "is_demo": False, "expires_at": None}


def create_demo_user() -> Dict[str, Any]:
    """Creates a throwaway demo account that expires after DEMO_TTL_SECONDS. It has no usable password."""
    user_id = uuid.uuid4().hex
    name = f"demo_{user_id[:12]}"
    expires_at = time.time() + DEMO_TTL_SECONDS
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO users (id, username, password_hash, is_demo, created_at, expires_at) VALUES (?, ?, ?, 1, ?, ?)",
            (user_id, name, _hasher.hash(secrets.token_urlsafe(32)), time.time(), expires_at),
        )
    return {"id": user_id, "username": name, "is_demo": True, "expires_at": expires_at}


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Returns the account if the credentials are valid, otherwise None (same timing either way)."""
    name = normalize_username(username)
    password = password or ""
    if len(password) > MAX_PASSWORD_LENGTH:
        return None
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ? AND is_demo = 0", (name,)).fetchone()
    try:
        _hasher.verify(row["password_hash"] if row else _DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return None
    if not row:
        return None
    if _hasher.check_needs_rehash(row["password_hash"]):
        with closing(_connect()) as conn, conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (_hasher.hash(password), row["id"]))
    return _public_user(row)


def create_session(user: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a login session. Returns the raw token (sent once, as a cookie) and its lifetime."""
    now = time.time()
    expires_at = now + USER_SESSION_TTL_SECONDS
    if user.get("expires_at"):
        expires_at = min(expires_at, user["expires_at"])
    token = secrets.token_urlsafe(32)
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user["id"], now, expires_at),
        )
    return {"token": token, "expires_at": expires_at, "max_age": int(expires_at - now)}


def get_user_for_token(token: str) -> Optional[Dict[str, Any]]:
    """Returns the account for a valid, unexpired session token, otherwise None."""
    if not token or len(token) > 256:
        return None
    now = time.time()
    with closing(_connect()) as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
              AND (users.expires_at IS NULL OR users.expires_at > ?)
            """,
            (_hash_token(token), now, now),
        ).fetchone()
    return _public_user(row) if row else None


def delete_session(token: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token or ""),))


def delete_user(user_id: str) -> None:
    """Deletes an account and (via cascade) all of its sessions."""
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def expired_demo_user_ids(now: Optional[float] = None) -> List[str]:
    now = time.time() if now is None else now
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT id FROM users WHERE is_demo = 1 AND expires_at <= ?", (now,)).fetchall()
    return [r["id"] for r in rows]


def delete_expired_sessions(now: Optional[float] = None) -> int:
    now = time.time() if now is None else now
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,)).rowcount
