"""
Daily limits on Gemini-backed actions, so visitors cannot drain the API quota.

One "AI action" is one user request that calls Gemini: a chat message, a monthly-insights
generation, a strategic-audit generation, or merchant classification for one upload/reset
(however many Gemini batches it needs). Counts are per UTC day, per account and across all
accounts (FINSIGHT_DAILY_AI_LIMIT, FINSIGHT_GLOBAL_DAILY_AI_LIMIT). When a limit is reached
the app falls back to its rule-based features instead of failing.
"""

import datetime
import sqlite3
from contextlib import closing
from typing import Any, Dict, Optional

from app import config
from app.services.auth import store

GLOBAL_KEY = "__all_accounts__"
RETENTION_DAYS = 7

LIMIT_REACHED_MESSAGE = (
    "You've reached today's limit for AI features. It resets at midnight UTC. "
    "Everything else keeps working, and rule-based summaries are shown in the meantime."
)


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _count(conn: sqlite3.Connection, key: str, day: str) -> int:
    row = conn.execute("SELECT count FROM ai_usage WHERE account_key = ? AND day = ?", (key, day)).fetchone()
    return int(row[0]) if row else 0


def try_consume(user_id: str) -> bool:
    """Records one AI action for the account if both daily limits allow it. Returns whether it was allowed."""
    day = _today()
    conn = sqlite3.connect(store.DB_PATH, timeout=10, isolation_level=None)
    with closing(conn):
        conn.execute("BEGIN IMMEDIATE")  # serialises concurrent check-and-increment
        try:
            if (_count(conn, user_id, day) >= config.DAILY_AI_LIMIT
                    or _count(conn, GLOBAL_KEY, day) >= config.GLOBAL_DAILY_AI_LIMIT):
                conn.execute("ROLLBACK")
                return False
            for key in (user_id, GLOBAL_KEY):
                conn.execute(
                    """
                    INSERT INTO ai_usage (account_key, day, count) VALUES (?, ?, 1)
                    ON CONFLICT(account_key, day) DO UPDATE SET count = count + 1
                    """,
                    (key, day),
                )
            conn.execute("COMMIT")
            return True
        except Exception:
            conn.execute("ROLLBACK")
            raise


def usage(user_id: str) -> Dict[str, Any]:
    with closing(sqlite3.connect(store.DB_PATH, timeout=10)) as conn:
        used = _count(conn, user_id, _today())
    return {"used": used, "limit": config.DAILY_AI_LIMIT, "remaining": max(0, config.DAILY_AI_LIMIT - used)}


def prune_old_usage(now: Optional[datetime.datetime] = None) -> None:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cutoff = (now - datetime.timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    with closing(sqlite3.connect(store.DB_PATH, timeout=10)) as conn, conn:
        conn.execute("DELETE FROM ai_usage WHERE day < ?", (cutoff,))


class AiGate:
    """
    Lets one request use AI at most once against the quota, and only if AI is actually needed:
    the first call consumes (or is refused), later calls return the same answer.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._allowed: Optional[bool] = None

    def __call__(self) -> bool:
        if self._allowed is None:
            self._allowed = try_consume(self.user_id)
        return self._allowed

    @property
    def denied(self) -> bool:
        return self._allowed is False
