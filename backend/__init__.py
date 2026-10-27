import sys
from pathlib import Path

# Ensure backend directory is in sys.path when backend is imported as a package
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
