import sys
import os
from pathlib import Path

# Allow tests to import backend modules as top-level modules.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Some modules expect backend-relative files (e.g. systemprompt.txt) from CWD.
os.chdir(BACKEND_DIR)
