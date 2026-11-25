"""
Deployment settings, all read from environment variables.

FINSIGHT_DATA_DIR             Directory for everything the app writes (accounts, auth.db, demo
                              template). Defaults to <project>/vault_storage. On Railway, point it
                              at the mounted volume (e.g. /data).
FINSIGHT_ENV                  "production" turns off the API docs, requires FINSIGHT_PROXY_SECRET
                              and forbids FINSIGHT_INSECURE_COOKIES.
FINSIGHT_PROXY_SECRET         Shared secret sent by the frontend proxy. When set, every request
                              except the health check must carry it.
FINSIGHT_INSECURE_COOKIES     "1" drops the Secure cookie flag (plain-HTTP LAN testing only).
FINSIGHT_CORS_ORIGINS         Comma-separated origins allowed cross-origin (off by default).
FINSIGHT_DAILY_AI_LIMIT       Gemini-backed actions per account per UTC day (default 40).
FINSIGHT_GLOBAL_DAILY_AI_LIMIT  Gemini-backed actions across all accounts per UTC day (default 1000).
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SAMPLE_STATEMENTS_DIR = os.path.join(PROJECT_ROOT, "sample_statements")

DATA_DIR = os.path.abspath(os.environ.get("FINSIGHT_DATA_DIR") or os.path.join(PROJECT_ROOT, "vault_storage"))

IS_PRODUCTION = os.environ.get("FINSIGHT_ENV", "").strip().lower() == "production"
PROXY_SECRET = os.environ.get("FINSIGHT_PROXY_SECRET", "")
INSECURE_COOKIES = os.environ.get("FINSIGHT_INSECURE_COOKIES") == "1"
COOKIE_SECURE = not INSECURE_COOKIES
CORS_ORIGINS = [o.strip() for o in os.environ.get("FINSIGHT_CORS_ORIGINS", "").split(",") if o.strip()]

MIN_PROXY_SECRET_LENGTH = 32


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be 0 or greater")
    return value


DAILY_AI_LIMIT = _int_env("FINSIGHT_DAILY_AI_LIMIT", 40)
GLOBAL_DAILY_AI_LIMIT = _int_env("FINSIGHT_GLOBAL_DAILY_AI_LIMIT", 1000)


def validate() -> None:
    """Refuses to start with an unsafe production configuration."""
    if not IS_PRODUCTION:
        return
    problems = []
    if len(PROXY_SECRET) < MIN_PROXY_SECRET_LENGTH:
        problems.append(f"FINSIGHT_PROXY_SECRET must be set to at least {MIN_PROXY_SECRET_LENGTH} characters")
    if INSECURE_COOKIES:
        problems.append("FINSIGHT_INSECURE_COOKIES must not be enabled in production")
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
