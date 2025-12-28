import sys
from pathlib import Path

# Ensure tests import the local SDK (sdk/python/src) rather than an installed package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


