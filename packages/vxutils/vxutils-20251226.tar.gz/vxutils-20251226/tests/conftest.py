import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

if "vxutils" in sys.modules:
    del sys.modules["vxutils"]
