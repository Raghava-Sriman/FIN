"""
Login, sessions, demo accounts and access control.
Requires the dev dependencies: python -m pip install -r requirements-dev.txt
Run from backend/: python -m unittest discover -s tests -v
"""

import hashlib
import os
import sqlite3
import time
import unittest
from unittest import mock

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import _env
import main
from app.services.auth import demo, rate_limit, store
from app.services.session.vault import SESSION_COOKIE, account_vault_path

BASE_URL = "https://testserver"  # Secure cookies are only sent over HTTPS


def new_client() -> TestClient:
    return TestClient(main.app, base_url=BASE_URL)


def directory_checksum(path: str) -> str:
    digest = hashlib.sha256()
    for root, _, files in sorted(os.walk(path)):
        for name in sorted(files):
            full = os.path.join(root, name)
            digest.update(os.path.relpath(full, path).encode())
            with open(full, "rb") as fh:
                digest.update(fh.read())
    return digest.hexdigest()


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # No network calls: only the Gemini request is stubbed, the rule-based classification still runs
        patcher = mock.patch(
            "app.services.categorizer.merchant_intelligence.call_gemini_batch_classifier", return_value={}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        for limiter in (rate_limit.login_failures, rate_limit.registrations, rate_limit.demo_logins):
            limiter._events.clear()

    def register(self, client, username, password="correct horse 9"):
        return client.post("/api/auth/register", json={"username": username, "password": password})


class PasswordAndLoginTests(AuthTestCase):
    def test_password_is_stored_as_argon2id_hash(self):
        self.assertEqual(self.register(new_client(), "hash_check").status_code, 200)
        with sqlite3.connect(store.DB_PATH) as conn:
            stored = conn.execute("SELECT password_hash FROM users WHERE username = 'hash_check'").fetchone()[0]
        self.assertTrue(stored.startswith("$argon2id$"))
        self.assertNotIn("correct horse 9", stored)

    def test_session_cookie_flags(self):
        res = self.register(new_client(), "cookie_check")
        cookie = res.headers["set-cookie"].lower()
        self.assertIn(f"{SESSION_COOKIE}=", cookie)
        for flag in ("httponly", "secure", "samesite=lax", "path=/"):
            self.assertIn(flag, cookie)

    def test_login_with_correct_password(self):
        self.register(new_client(), "login_ok")
        client = new_client()
        res = client.post("/api/auth/login", json={"username": "LOGIN_OK", "password": "correct horse 9"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(client.get("/api/auth/me").json()["user"]["username"], "login_ok")

    def test_wrong_password_and_unknown_user_get_the_same_401(self):
        self.register(new_client(), "login_bad")
        wrong = new_client().post("/api/auth/login", json={"username": "login_bad", "password": "wrong password"})
        unknown = new_client().post("/api/auth/login", json={"username": "nobody_here", "password": "wrong password"})
        self.assertEqual((wrong.status_code, unknown.status_code), (401, 401))
        self.assertEqual(wrong.json(), unknown.json())
        self.assertNotIn("set-cookie", wrong.headers)

    def test_registration_validation(self):
        client = new_client()
        self.assertEqual(self.register(client, "x").status_code, 400)  # too short
        self.assertEqual(self.register(client, "valid_name", "short").status_code, 400)
        self.assertEqual(self.register(client, "demo").status_code, 400)  # reserved
        self.assertEqual(self.register(client, "demo_lookalike").status_code, 400)  # reserved prefix
        self.assertEqual(self.register(client, "../etc").status_code, 400)
        self.assertEqual(self.register(client, "taken_name").status_code, 200)
        self.assertEqual(self.register(new_client(), "taken_name").status_code, 400)

    def test_repeated_failures_are_rate_limited(self):
        self.register(new_client(), "limited_user")
        client = new_client()
        for _ in range(rate_limit.login_failures.max_events):
            self.assertEqual(client.post("/api/auth/login", json={"username": "limited_user", "password": "nope nope"}).status_code, 401)
        blocked = client.post("/api/auth/login", json={"username": "limited_user", "password": "correct horse 9"})
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("retry-after", blocked.headers)

    def test_logout_invalidates_the_session(self):
        client = new_client()
        self.register(client, "logout_user")
        self.assertEqual(client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(client.get("/api/auth/me").status_code, 401)


class AccessControlTests(AuthTestCase):
    def _protected_requests(self):
        for route in main.app.routes:
            if not isinstance(route, APIRoute) or route.path in main.PUBLIC_API_PATHS:
                continue
            path = route.path
            for param in route.param_convertors:
                path = path.replace("{" + param + "}", "x")
            for method in sorted(route.methods):
                yield method, path

    def test_every_protected_route_rejects_missing_fake_and_expired_tokens(self):
        expired_client = new_client()
        self.register(expired_client, "soon_expired")
        with sqlite3.connect(store.DB_PATH) as conn:
            conn.execute("UPDATE sessions SET expires_at = ?", (time.time() - 1,))

        requests = list(self._protected_requests())
        self.assertGreater(len(requests), 25)
        for method, path in requests:
            with self.subTest(method=method, path=path):
                self.assertEqual(new_client().request(method, path).status_code, 401)
                fake = new_client()
                fake.cookies.set(SESSION_COOKIE, "not-a-real-token", domain="testserver")
                self.assertEqual(fake.request(method, path).status_code, 401)
                self.assertEqual(expired_client.request(method, path).status_code, 401)

    def test_public_routes(self):
        self.assertEqual(new_client().get("/api/samples").status_code, 200)

    def test_accounts_cannot_see_each_other(self):
        alice, bob = new_client(), new_client()
        self.register(alice, "alice_user")
        self.register(bob, "bob_user")
        alice.post("/api/goals", json={"title": "Alice goal", "target_amount": 1000, "monthly_allocation": 100})
        self.assertEqual(len(alice.get("/api/goals").json()["goals"]), 1)
        self.assertEqual(bob.get("/api/goals").json()["goals"], [])


class DemoAccountTests(AuthTestCase):
    def test_demo_credentials_on_login_form_start_a_demo(self):
        client = new_client()
        res = client.post("/api/auth/login", json={"username": "demo", "password": demo.DEMO_PASSWORD})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["user"]["is_demo"])
        self.assertTrue(client.get("/api/statements-list").json()["has_statement"])

    def test_simultaneous_demos_are_isolated_and_template_is_untouched(self):
        a, b = new_client(), new_client()
        self.assertEqual(a.post("/api/auth/demo").status_code, 200)
        self.assertEqual(b.post("/api/auth/demo").status_code, 200)
        template_before = directory_checksum(demo.TEMPLATE_DIR)
        sample_before = directory_checksum(os.path.dirname(demo.DEMO_SAMPLE_PATH))

        # Visitor A changes everything it can
        a.post("/api/goals", json={"title": "A's goal", "target_amount": 5000, "monthly_allocation": 500})
        merchant = a.get("/api/merchant-dictionary").json()["merchants"][0]["merchant_key"]
        a.put(f"/api/merchant-dictionary/{merchant}", json={"sub_category": "Travel & Vacation"})
        a.post("/api/finneas/threads", json={"title": "A's chat"})
        upload = ("extra.csv", b"Date,Narration,Debit,Credit,Balance\n01/10/2026,UPI/A ONLY,999,,1000\n")
        a.post("/api/upload", files={"files": upload})
        a_statements = a.get("/api/statements-list").json()["statements"]
        self.assertEqual(len(a_statements), 2)

        # Visitor B sees none of it
        self.assertEqual(b.get("/api/goals").json()["goals"], [])
        self.assertEqual(b.get("/api/finneas/threads").json()["threads"], [])
        self.assertEqual(len(b.get("/api/statements-list").json()["statements"]), 1)
        b_merchant = next(m for m in b.get("/api/merchant-dictionary").json()["merchants"] if m["merchant_key"] == merchant)
        self.assertNotEqual(b_merchant["sub_category"], "Travel & Vacation")

        # A deleting its statements does not affect B, the template or the sample file
        a.post("/api/clear-statement")
        self.assertTrue(b.get("/api/statements-list").json()["has_statement"])
        self.assertEqual(directory_checksum(demo.TEMPLATE_DIR), template_before)
        self.assertEqual(directory_checksum(os.path.dirname(demo.DEMO_SAMPLE_PATH)), sample_before)

        # A fresh demo starts from the original data again
        c = new_client()
        c.post("/api/auth/demo")
        self.assertEqual(len(c.get("/api/statements-list").json()["statements"]), 1)

    def test_demo_logout_deletes_its_data(self):
        client = new_client()
        client.post("/api/auth/demo")
        user_id = self._latest_demo_id()
        self.assertTrue(os.path.isdir(account_vault_path(user_id)))
        client.post("/api/auth/logout")
        self.assertFalse(os.path.exists(account_vault_path(user_id)))

    def test_expired_demo_is_cleaned_up(self):
        client = new_client()
        client.post("/api/auth/demo")
        user_id = self._latest_demo_id()
        demo.cleanup_expired()  # this demo is still within its 24 hours
        self.assertTrue(os.path.isdir(account_vault_path(user_id)))
        self.assertEqual(client.get("/api/auth/me").status_code, 200)

        removed = demo.cleanup_expired(now=time.time() + store.DEMO_TTL_SECONDS + 1)
        self.assertGreaterEqual(removed, 1)
        self.assertFalse(os.path.exists(account_vault_path(user_id)))
        self.assertEqual(client.get("/api/auth/me").status_code, 401)

    def test_demo_session_expires_with_the_account(self):
        client = new_client()
        client.post("/api/auth/demo")
        with sqlite3.connect(store.DB_PATH) as conn:
            conn.execute("UPDATE users SET expires_at = ? WHERE id = ?", (time.time() - 1, self._latest_demo_id()))
        self.assertEqual(client.get("/api/auth/me").status_code, 401)

    def _latest_demo_id(self) -> str:
        with sqlite3.connect(store.DB_PATH) as conn:
            return conn.execute("SELECT id FROM users WHERE is_demo = 1 ORDER BY created_at DESC LIMIT 1").fetchone()[0]


class StorageLocationTests(unittest.TestCase):
    def test_tests_use_a_temporary_vault(self):
        self.assertTrue(store.DB_PATH.startswith(_env.DATA_DIR))
        self.assertTrue(demo.TEMPLATE_DIR.startswith(_env.DATA_DIR))


if __name__ == "__main__":
    unittest.main()
