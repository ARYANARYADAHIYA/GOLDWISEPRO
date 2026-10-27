import io
import pytest
import datetime
import pandas as pd
from app.core.database import SessionLocal
from app.data.importer import parse_and_validate_file
from app.data.mcx_collector import is_market_holiday_or_weekend, attempt_mcx_automated_collection
from app.data.mcx_historical_data import generate_authentic_mcx_bhavcopy_csv, seed_real_mcx_historical_dataset
from app.quant.ml.forecast import GoldPriceForecaster
from app.quant.ml.retraining import execute_retraining_pipeline
from app.models.entities import DatasetModel, ObservationModel, MLModelRecord

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_mcx_holiday_and_weekend_detection():
    # Test Saturday / Sunday
    sat = datetime.date(2026, 5, 2)
    is_closed, reason = is_market_holiday_or_weekend(sat)
    assert is_closed is True
    assert "Saturday" in reason

    # Test Republic Day (Jan 26)
    rep_day = datetime.date(2026, 1, 26)
    is_closed, reason = is_market_holiday_or_weekend(rep_day)
    assert is_closed is True
    assert "Republic Day" in reason

    # Test ordinary weekday
    weekday = datetime.date(2026, 5, 6)
    is_closed, reason = is_market_holiday_or_weekend(weekday)
    assert is_closed is False

def test_mcx_bhavcopy_generation_and_parsing():
    csv_bytes = generate_authentic_mcx_bhavcopy_csv(start_date="2026-02-02", num_days=30)
    assert len(csv_bytes) > 1000

    parsed = parse_and_validate_file(csv_bytes, filename="mcx_test.csv", preferred_date_format="DD/MM/YYYY")
    assert parsed["is_valid"] is True
    assert parsed["row_count"] > 100
    assert "GOLD" in parsed["instruments"]
    assert "GOLDM" in parsed["instruments"]
    assert "GOLDGUINEA" in parsed["instruments"]
    assert "GOLDPETAL" in parsed["instruments"]
    assert "GOLDTEN" in parsed["instruments"]

    # Verify fields populated
    first_obs = parsed["observations"][0]
    assert first_obs["close_price"] > 0
    assert first_obs["previous_close"] > 0
    assert first_obs["turnover"] >= 0
    assert first_obs["normalized_price_pure_gram"] > 0

def test_price_forecaster_insufficient_data():
    forecaster = GoldPriceForecaster(min_observations=30)
    small_df = pd.DataFrame([
        {"timestamp": f"2026-05-{i:02d}", "normalized_a": 7500.0 + i}
        for i in range(1, 10)
    ])
    res = forecaster.train_and_evaluate(small_df)
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["is_fitted"] is False

def test_price_forecaster_chronological_evaluation():
    forecaster = GoldPriceForecaster(min_observations=30)
    # Generate 60 daily observations with slight trend
    records = []
    price = 7400.0
    for i in range(60):
        price *= (1.0 + (0.001 if i % 2 == 0 else -0.0008))
        records.append({
            "timestamp": f"2026-04-{i+1:03d}",
            "normalized_a": price,
            "price_a": price * 10,
            "percentage_spread": 0.05,
            "robust_zscore": 0.2
        })
    df = pd.DataFrame(records)
    res = forecaster.train_and_evaluate(df, train_pct=0.70, val_pct=0.15)
    assert res["status"] == "TRAINED"
    assert res["is_fitted"] is True
    assert "mae_price_inr_per_g" in res["metrics"]["candidate"]
    assert "directional_accuracy_pct" in res["metrics"]["candidate"]
    assert len(res["test_series"]) > 0

def test_retraining_pipeline_execution(db):
    res = execute_retraining_pipeline(db, force=True)
    assert res["status"] == "SUCCESS"
    assert res["isolation_forest"] is not None
    assert res["price_forecasting"] is not None

    # Check database persistence
    active_models = db.query(MLModelRecord).filter(MLModelRecord.is_active == True).all()
    assert len(active_models) >= 1
