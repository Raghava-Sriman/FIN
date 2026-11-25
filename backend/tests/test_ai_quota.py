"""
Daily limits on Gemini-backed actions and the strategic-audit cache.
Run from backend/: python -m unittest discover -s tests -v
"""

import unittest
import uuid
from unittest import mock

import _env  # noqa: F401  (must come before importing main: keeps storage in a temp dir)
import main
from app import config
from app.services.auth import ai_quota, rate_limit
from fastapi.testclient import TestClient

STATEMENT = (
    "Date,Narration,Debit,Credit,Balance\n"
    "01/10/2026,UPI/MYSTERY SHOP 1,450,,49550\n"
    "05/10/2026,UPI/MYSTERY SHOP 2,300,,49250\n"
    "06/10/2026,NEFT SALARY,,90000,139250\n"
)


def logged_in_client() -> TestClient:
    for limiter in (rate_limit.registrations, rate_limit.login_failures, rate_limit.demo_logins):
        limiter._events.clear()
    client = TestClient(main.app, base_url="https://testserver")
    res = client.post("/api/auth/register", json={"username": f"q_{uuid.uuid4().hex[:10]}", "password": "long enough pw"})
    assert res.status_code == 200, res.text
    return client


def limits(per_account: int, global_cap: int = 10_000):
    return [
        mock.patch.object(config, "DAILY_AI_LIMIT", per_account),
        mock.patch.object(config, "GLOBAL_DAILY_AI_LIMIT", global_cap),
    ]


class QuotaCounterTests(unittest.TestCase):
    def setUp(self):
        # A fresh global counter per test, so other tests' usage doesn't count against the cap
        for p in limits(3, 5) + [mock.patch.object(ai_quota, "GLOBAL_KEY", f"global_{uuid.uuid4().hex}")]:
            p.start()
            self.addCleanup(p.stop)

    def test_per_account_limit(self):
        user = f"acct_{uuid.uuid4().hex}"
        self.assertEqual([ai_quota.try_consume(user) for _ in range(4)], [True, True, True, False])
        self.assertEqual(ai_quota.usage(user), {"used": 3, "limit": 3, "remaining": 0})

    def test_global_cap_applies_across_accounts(self):
        results = [ai_quota.try_consume(f"acct_{uuid.uuid4().hex}") for _ in range(6)]
        self.assertEqual(results, [True] * 5 + [False])

    def test_gate_consumes_at_most_once(self):
        user = f"acct_{uuid.uuid4().hex}"
        gate = ai_quota.AiGate(user)
        self.assertFalse(gate.denied)
        self.assertTrue(all(gate() for _ in range(5)))
        self.assertEqual(ai_quota.usage(user)["used"], 1)


class EndpointLimitTests(unittest.TestCase):
    def setUp(self):
        # No network: no Gemini key, and the Gemini functions fail the test if they are reached
        env = mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""})
        env.start()
        self.addCleanup(env.stop)
        self.gemini_batch = mock.patch(
            "app.services.categorizer.merchant_intelligence.call_gemini_batch_classifier", return_value={}
        )
        self.batch_mock = self.gemini_batch.start()
        self.addCleanup(self.gemini_batch.stop)

    def _set_limit(self, n):
        for p in limits(n):
            p.start()
            self.addCleanup(p.stop)

    def test_chat_over_limit_answers_without_ai(self):
        self._set_limit(1)
        client = logged_in_client()
        first = client.post("/api/finneas/chat", json={"message": "What is my cashflow?"}).json()
        self.assertNotIn("limit for AI", first["assistant_message"]["content"])
        with mock.patch("app.services.chat.agent.requests.post", side_effect=AssertionError("Gemini called")):
            second = client.post("/api/finneas/chat", json={"message": "What is my cashflow?"}).json()
        self.assertIn("reached today's limit for AI answers", second["assistant_message"]["content"])
        self.assertEqual(client.get("/api/auth/me").json()["ai_usage"]["remaining"], 0)

    def test_upload_over_limit_skips_gemini_and_flags_merchants(self):
        self._set_limit(0)
        client = logged_in_client()
        res = client.post("/api/upload", files={"files": ("oct.csv", STATEMENT.encode())}).json()
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["ai_limited"])
        self.batch_mock.assert_not_called()
        merchants = client.get("/api/merchant-dictionary").json()["merchants"]
        self.assertTrue(merchants and all(m["needs_review"] for m in merchants))

    def test_upload_within_limit_uses_one_unit(self):
        self._set_limit(5)
        client = logged_in_client()
        res = client.post("/api/upload", files={"files": ("oct.csv", STATEMENT.encode())}).json()
        self.assertFalse(res["ai_limited"])
        self.batch_mock.assert_called_once()
        self.assertEqual(client.get("/api/auth/me").json()["ai_usage"]["used"], 1)

    def test_monthly_insights_over_limit_use_rule_based_summary(self):
        self._set_limit(1)
        client = logged_in_client()
        client.post("/api/upload", files={"files": ("oct.csv", STATEMENT.encode())})  # uses the 1 unit
        with mock.patch("app.services.analytics.monthly_insights.requests.post", side_effect=AssertionError("Gemini called")):
            res = client.post("/api/month-insights/2026-10").json()
        self.assertTrue(res["ai_limited"])
        self.assertIn("executive_headline", res)


class StrategicAuditCacheTests(unittest.TestCase):
    def setUp(self):
        self.generate = mock.patch.object(main, "generate_strategic_audit", side_effect=lambda df, use_ai=True: {"ai": use_ai})
        self.generate_mock = self.generate.start()
        self.addCleanup(self.generate.stop)
        patcher = mock.patch(
            "app.services.categorizer.merchant_intelligence.call_gemini_batch_classifier", return_value={}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _client_with_statement(self, limit):
        for p in limits(limit):
            p.start()
            self.addCleanup(p.stop)
        client = logged_in_client()
        client.post("/api/upload", files={"files": ("oct.csv", STATEMENT.encode())})
        return client

    def test_audit_is_cached_until_statements_change(self):
        client = self._client_with_statement(limit=10)
        self.assertEqual(client.get("/api/subscriptions").json(), {"ai": True})
        client.get("/api/subscriptions")
        client.get("/api/strategic-audit")
        self.assertEqual(self.generate_mock.call_count, 1)  # page reloads reuse the cache

        client.post("/api/strategic-audit")  # "Re-analyze" forces a refresh
        self.assertEqual(self.generate_mock.call_count, 2)

        nov = STATEMENT.replace("/10/2026", "/11/2026")
        client.post("/api/upload", files={"files": ("nov.csv", nov.encode())})
        client.get("/api/subscriptions")
        self.assertEqual(self.generate_mock.call_count, 3)  # new statement invalidates the cache

    def test_audit_over_limit_is_rule_based_and_not_cached(self):
        client = self._client_with_statement(limit=1)  # the upload used the only unit
        first = client.get("/api/subscriptions").json()
        self.assertEqual(first, {"ai": False, "ai_limited": True})
        with mock.patch.object(config, "DAILY_AI_LIMIT", 10):
            self.assertEqual(client.get("/api/subscriptions").json(), {"ai": True})


if __name__ == "__main__":
    unittest.main()
