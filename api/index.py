import os
import sys

# Ensure project root and backend directory are in sys.path so backend module can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set IS_VERCEL to force /tmp paths and appropriate serverless configuration
os.environ["IS_VERCEL"] = "1"

from backend.app.main import app

# Export the FastAPI app for Vercel Serverless
# Vercel's Python runtime will detect and invoke 'app'
__all__ = ["app"]
