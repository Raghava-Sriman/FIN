"""
Test environment: import this before `main` so all storage (auth.db, accounts,
demo template) goes to a temporary FINSIGHT_DATA_DIR instead of vault_storage/.
"""

import atexit
import os
import shutil
import tempfile

if "FINSIGHT_TEST_DATA_DIR" not in os.environ:
    root = tempfile.mkdtemp(prefix="finsight_test_data_")
    os.environ["FINSIGHT_TEST_DATA_DIR"] = root
    os.environ["FINSIGHT_DATA_DIR"] = root
    os.environ["FINSIGHT_SKIP_DEMO_WARMUP"] = "1"
    atexit.register(shutil.rmtree, root, ignore_errors=True)

DATA_DIR = os.environ["FINSIGHT_DATA_DIR"]
