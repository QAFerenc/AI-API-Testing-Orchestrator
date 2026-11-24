import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

# Offline regression testing only.
os.environ["GOOGLE_API_KEY"] = "offline_regression_test_key"
