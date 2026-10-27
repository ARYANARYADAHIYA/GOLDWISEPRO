import os
import pytest
import numpy as np
import pandas as pd
import joblib

from app.quant.synthetic import generate_synthetic_mcx_dataset
from app.quant.scanner import run_relative_value_scan
from app.quant.ml.features import engineer_timestamp_safe_features, FEATURE_NAMES
from app.quant.ml.pipeline import train_and_persist_model, chronological_split
from app.quant.ml.supervised import SupervisedOutcomeModel
from app.quant.ml.drift import calculate_psi, evaluate_model_drift

def test_chronological_split_no_shuffle():
    records = generate_synthetic_mcx_dataset(num_days=100)
    df = pd.DataFrame(records)[["timestamp"]].drop_duplicates().sort_values("timestamp").reset_index(drop=True)
    df["percentage_spread"] = np.random.randn(len(df))
    df["robust_zscore"] = np.random.randn(len(df))
    df["volume_a"] = 1000.0
    df["volume_b"] = 1000.0

    df_train, df_val, df_test = chronological_split(df, train_pct=0.70, val_pct=0.15)
    
    # Verify temporal order
    assert df_train["timestamp"].max() < df_val["timestamp"].min()
    assert df_val["timestamp"].max() < df_test["timestamp"].min()
    assert len(df_train) + len(df_val) + len(df_test) == len(df)

def test_isolation_forest_pipeline_training_and_reload():
    records = generate_synthetic_mcx_dataset(num_days=100)
    df_obs = pd.DataFrame(records)
    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    df_aligned = pd.DataFrame(scan_res["candidates"])

    res = train_and_persist_model(
        df_aligned=df_aligned,
        model_type="ISOLATION_FOREST",
        dataset_id="test-ds",
        hyperparams={"contamination": 0.05, "n_estimators": 50, "random_state": 42}
    )

    assert res["status"] == "TRAINED"
    assert os.path.exists(res["artifact_path"])
    assert res["test_metrics"]["observations"] > 0

    # Reload artifact and verify inference
    payload = joblib.load(res["artifact_path"])
    model = payload["model_object"]
    sample_X = np.zeros((2, len(FEATURE_NAMES)))
    preds = model.predict(sample_X)
    assert len(preds) == 2
    assert set(preds).issubset({0, 1})

def test_supervised_model_rejects_insufficient_labels():
    model = SupervisedOutcomeModel(min_required_samples=30)
    X = np.zeros((10, 5))
    y = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) # Only 1 class, under 30 samples

    with pytest.raises(ValueError) as excinfo:
        model.fit(X, y)
    assert "Supervised model validation halted" in str(excinfo.value)

def test_psi_and_drift_calculation():
    np.random.seed(42)
    # Baseline normal distribution
    baseline = np.random.normal(0, 1, 500)
    # Similar distribution -> low PSI
    shifted_minor = np.random.normal(0.05, 1, 500)
    psi_stable = calculate_psi(baseline, shifted_minor)
    assert psi_stable < 0.10

    # Highly shifted distribution -> high PSI
    shifted_major = np.random.normal(2.5, 1.5, 500)
    psi_drift = calculate_psi(baseline, shifted_major)
    assert psi_drift > 0.25
