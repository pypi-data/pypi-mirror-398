import sys
from pathlib import Path

VENDORED_PATH = Path(__file__).parent / "vendored"
if str(VENDORED_PATH) not in sys.path:
    sys.path.insert(0, str(VENDORED_PATH))