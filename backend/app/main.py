import sys
from pathlib import Path

# Ensure backend directory and project root are in sys.path so 'from app...' works
# regardless of whether uvicorn is launched from the workspace root or inside backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models.entities import *
from app.services.dataset_service import seed_synthetic_dataset_if_empty
from app.api.routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("goldwise")

from app.core.migrations import run_db_migrations

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        run_db_migrations()
    except Exception as e:
        logger.warning(f"Schema migration note: {e}")
    db = SessionLocal()
    try:
        seed_synthetic_dataset_if_empty(db)
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    finally:
        db.close()

# Proactively initialize database tables and seed
try:
    init_db()
except Exception as e:
    logger.warning(f"Initial schema setup deferred: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan startup: checking database schema...")
    init_db()
    yield
    logger.info("Shutting down GOLDWISE PRO quantitative backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Institutional Commodity Relative-Value Research and Anomaly Investigation Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router with /api prefix (primary standard)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount API router without prefix as a fallback for serverless environments
# where the /api path segment may be pre-stripped by the edge router
app.include_router(api_router, include_in_schema=False)

@app.get("/", include_in_schema=False)
@app.get("/api", include_in_schema=False)
def root():
    return {
        "app": "GOLDWISE PRO",
        "status": "ONLINE",
        "docs_url": "/api/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/docs", include_in_schema=False)
def docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
