"""
Production configuration: docs disabled, proxy secret required and enforced, health check,
and refusal to start with unsafe settings. Settings are read at import time, so each case
runs in a fresh Python process with its own environment.
Run from backend/: python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET = "s" * 48

CHECK_SCRIPT = textwrap.dedent(
    """
    import json, sys
    from fastapi.testclient import TestClient
    import main
    from app.services.auth.rate_limit import client_ip
    from starlette.requests import Request

    client = TestClient(main.app, base_url="https://testserver")
    secret = {"x-finsight-proxy-secret": sys.argv[1]}
    out = {}
    for path in ("/docs", "/redoc", "/openapi.json", "/api/samples", "/api/healthz", "/api/overview"):
        out[path] = {
            "no_secret": client.get(path).status_code,
            "wrong_secret": client.get(path, headers={"x-finsight-proxy-secret": "wrong"}).status_code,
            "with_secret": client.get(path, headers=secret).status_code,
        }
    req = Request({"type": "http", "headers": [(b"x-finsight-client-ip", b"203.0.113.7"), (b"x-forwarded-for", b"10.0.0.1")], "client": ("10.9.9.9", 1)})
    out["client_ip"] = client_ip(req)
    print(json.dumps(out))
    """
)


def run_backend(env_overrides, *args):
    data_dir = tempfile.mkdtemp(prefix="finsight_prod_test_")
    env = {k: v for k, v in os.environ.items() if not k.startswith("FINSIGHT_")}
    env.update({"FINSIGHT_DATA_DIR": data_dir, "FINSIGHT_SKIP_DEMO_WARMUP": "1"})
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", CHECK_SCRIPT, *args],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )


class ProductionConfigTests(unittest.TestCase):
    def test_production_without_secret_refuses_to_start(self):
        res = run_backend({"FINSIGHT_ENV": "production"}, "x")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("FINSIGHT_PROXY_SECRET", res.stderr)

    def test_production_with_short_secret_refuses_to_start(self):
        res = run_backend({"FINSIGHT_ENV": "production", "FINSIGHT_PROXY_SECRET": "too-short"}, "x")
        self.assertNotEqual(res.returncode, 0)

    def test_production_rejects_insecure_cookies(self):
        res = run_backend({"FINSIGHT_ENV": "production", "FINSIGHT_PROXY_SECRET": SECRET, "FINSIGHT_INSECURE_COOKIES": "1"}, SECRET)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("FINSIGHT_INSECURE_COOKIES", res.stderr)

    def test_production_behaviour(self):
        res = run_backend({"FINSIGHT_ENV": "production", "FINSIGHT_PROXY_SECRET": SECRET}, SECRET)
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout.strip().splitlines()[-1])

        for docs_path in ("/docs", "/redoc", "/openapi.json"):
            with self.subTest(path=docs_path):
                self.assertEqual(out[docs_path]["no_secret"], 403)
                self.assertEqual(out[docs_path]["with_secret"], 404)  # disabled in production

        # Everything except the health check requires the proxy secret
        self.assertEqual(out["/api/samples"], {"no_secret": 403, "wrong_secret": 403, "with_secret": 200})
        self.assertEqual(out["/api/overview"]["no_secret"], 403)
        self.assertEqual(out["/api/overview"]["with_secret"], 401)  # still needs a login
        self.assertEqual(out["/api/healthz"], {"no_secret": 200, "wrong_secret": 200, "with_secret": 200})

        # Rate limits use the visitor address reported by the proxy
        self.assertEqual(out["client_ip"], "203.0.113.7")

    def test_development_defaults(self):
        res = run_backend({}, "unused")
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout.strip().splitlines()[-1])
        self.assertEqual(out["/docs"]["no_secret"], 200)
        self.assertEqual(out["/api/samples"]["no_secret"], 200)  # no proxy secret configured locally
        self.assertEqual(out["client_ip"], "10.0.0.1")  # last X-Forwarded-For entry from next dev


if __name__ == "__main__":
    unittest.main()
