import os
from pathlib import Path
from pydantic import BaseModel

IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("IS_VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
if IS_VERCEL:
    DATA_DIR = Path("/tmp/data_storage")
    ARTIFACTS_DIR = Path("/tmp/artifacts")
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data_storage"
    ARTIFACTS_DIR = BASE_DIR / "artifacts"

MODELS_DIR = ARTIFACTS_DIR / "models"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "GOLDWISE PRO"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR / 'goldwise.db'}")
    ALLOWED_ORIGINS: list[str] = [
        "*"
    ]
    # Default quantitative thresholds
    DEFAULT_ZSCORE_THRESHOLD: float = 2.0
    DEFAULT_PERCENTILE_LOWER: float = 2.5
    DEFAULT_PERCENTILE_UPPER: float = 97.5
    DEFAULT_ROLLING_WINDOW_DAYS: int = 20
    DEFAULT_MIN_OBSERVATIONS: int = 15
    DEFAULT_EXPIRY_PROXIMITY_DAYS: int = 3
    DEFAULT_SLIPPAGE_BPS: float = 3.0
    DEFAULT_BROKERAGE_BPS: float = 1.5
    DEFAULT_EXCHANGE_FEES_BPS: float = 1.0

settings = Settings()
