import os
import sys

# Ensure root and backend are in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["IS_VERCEL"] = "1"

from backend.app.main import app

__all__ = ["app"]
