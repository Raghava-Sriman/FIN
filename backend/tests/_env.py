"""
Test environment: import this before `main` so all storage (auth.db, accounts,
demo template) goes to a temporary directory instead of vault_storage/.
"""

import atexit
import os
import shutil
import tempfile

if "FINSIGHT_TEST_VAULT_ROOT" not in os.environ:
    root = tempfile.mkdtemp(prefix="finsight_test_vault_")
    os.environ["FINSIGHT_TEST_VAULT_ROOT"] = root
    os.environ["FINSIGHT_VAULT_ROOT"] = root
    os.environ["FINSIGHT_SKIP_DEMO_WARMUP"] = "1"
    atexit.register(shutil.rmtree, root, ignore_errors=True)

VAULT_ROOT = os.environ["FINSIGHT_VAULT_ROOT"]
