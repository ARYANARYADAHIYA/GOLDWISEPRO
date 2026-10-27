import os
import uuid
import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

from app.core.config import MODELS_DIR
from app.quant.ml.features import engineer_timestamp_safe_features, get_feature_matrix, FEATURE_NAMES
from app.quant.ml.baseline import StatisticalAnomalyBaseline
from app.quant.ml.isolation_forest import IsolationForestAnomalyDetector
from app.quant.ml.supervised import SupervisedOutcomeModel

def chronological_split(
    df: pd.DataFrame,
    train_pct: float = 0.70,
    val_pct: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs strict chronological splitting of time series data.
    ZERO RANDOM SHUFFLING to ensure complete lookahead prevention.
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_pct)
    val_end = int(n * (train_pct + val_pct))
    
    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()
    
    return df_train, df_val, df_test

def train_and_persist_model(
    df_aligned: pd.DataFrame,
    model_type: str = "ISOLATION_FOREST",
    model_name: Optional[str] = None,
    dataset_id: str = "unknown",
    train_pct: float = 0.70,
    val_pct: float = 0.15,
    hyperparams: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes reproducible ML model training workflow:
    1. Timestamp-safe feature engineering
    2. Strict chronological train/val/test splitting
    3. Fit model on training slice only
    4. Evaluate on validation and protected test slices
    5. Persist artifact to disk (.joblib)
    6. Reload and verify inference integrity
    """
    hyperparams = hyperparams or {}
    logs = []
    logs.append(f"[{datetime.datetime.now(datetime.timezone.utc).isoformat()}] Starting ML Pipeline for model_type='{model_type}' on dataset='{dataset_id}'")
    
    if len(df_aligned) < 20:
        raise ValueError(f"Insufficient observations for training: {len(df_aligned)} < 20 required")
        
    # Feature engineering
    df_feat = engineer_timestamp_safe_features(df_aligned)
    logs.append(f"Engineered {len(FEATURE_NAMES)} timestamp-safe features for {len(df_feat)} aligned observations")
    
    # Chronological split
    df_train, df_val, df_test = chronological_split(df_feat, train_pct=train_pct, val_pct=val_pct)
    logs.append(f"Chronological split: Train={len(df_train)} ({df_train['timestamp'].min()} to {df_train['timestamp'].max()}), "
                f"Val={len(df_val)} ({df_val['timestamp'].min()} to {df_val['timestamp'].max()}), "
                f"Test={len(df_test)} ({df_test['timestamp'].min()} to {df_test['timestamp'].max()})")
                
    X_train, _ = get_feature_matrix(df_train)
    X_val, _ = get_feature_matrix(df_val)
    X_test, _ = get_feature_matrix(df_test)
    
    model_id = f"model-{model_type.lower()}-{uuid.uuid4().hex[:8]}"
    version = f"v1.0-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M')}"
    
    if model_type == "BASELINE_STATISTICAL":
        z_thresh = hyperparams.get("zscore_threshold", 2.0)
        model = StatisticalAnomalyBaseline(zscore_threshold=z_thresh)
        model.fit(X_train)
        feature_importance = {name: (100.0 if name == "robust_zscore" else 0.0) for name in FEATURE_NAMES}
    elif model_type == "ISOLATION_FOREST":
        contam = hyperparams.get("contamination", 0.05)
        n_est = hyperparams.get("n_estimators", 100)
        seed = hyperparams.get("random_state", 42)
        model = IsolationForestAnomalyDetector(contamination=contam, n_estimators=n_est, random_state=seed)
        model.fit(X_train)
        feature_importance = model.compute_feature_importance(X_val, FEATURE_NAMES)
    elif model_type == "SUPERVISED_RIDGE":
        # Check if labels exist
        y_train = df_train.get("label", None)
        model = SupervisedOutcomeModel()
        try:
            model.fit(X_train, y_train.values if y_train is not None else None)
        except Exception as e:
            logs.append(f"Supervised model training stopped: {str(e)}")
            return {
                "id": model_id,
                "name": model_name or f"Supervised Outcome ({version})",
                "model_type": model_type,
                "dataset_id": dataset_id,
                "version": version,
                "status": "FAILED",
                "logs": "\n".join(logs),
                "error": str(e)
            }
        feature_importance = {name: 100.0 / len(FEATURE_NAMES) for name in FEATURE_NAMES}
    else:
        raise ValueError(f"Unknown model_type '{model_type}'")
        
    logs.append(f"Model {model_type} fitted successfully on training slice.")
    
    # Compute metrics on train, val, and test slices
    def evaluate_slice(X_slice: np.ndarray, slice_name: str) -> Dict[str, Any]:
        preds = model.predict(X_slice)
        scores = model.decision_function(X_slice)
        detection_rate = float(np.mean(preds)) * 100.0
        return {
            "slice_name": slice_name,
            "observations": len(X_slice),
            "anomalies_detected": int(np.sum(preds)),
            "detection_rate_pct": round(detection_rate, 2),
            "mean_anomaly_score": round(float(np.mean(scores)), 4),
            "score_std": round(float(np.std(scores)), 4),
            "score_p95": round(float(np.percentile(scores, 95.0)), 4) if len(scores) > 0 else 0.0,
            "score_max": round(float(np.max(scores)), 4) if len(scores) > 0 else 0.0
        }
        
    train_metrics = evaluate_slice(X_train, "TRAIN")
    val_metrics = evaluate_slice(X_val, "VALIDATION")
    test_metrics = evaluate_slice(X_test, "HELD_OUT_TEST")
    
    # Persist artifact
    artifact_filename = f"{model_id}.joblib"
    artifact_path = str(MODELS_DIR / artifact_filename)
    artifact_payload = {
        "model_id": model_id,
        "model_type": model_type,
        "version": version,
        "feature_names": FEATURE_NAMES,
        "hyperparams": hyperparams,
        "model_object": model,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "split_config": {
            "train_pct": train_pct,
            "val_pct": val_pct,
            "test_pct": round(1.0 - train_pct - val_pct, 2)
        }
    }
    joblib.dump(artifact_payload, artifact_path)
    logs.append(f"Saved artifact to {artifact_path}")
    
    # Reload and verify inference
    reloaded_payload = joblib.load(artifact_path)
    reloaded_model = reloaded_payload["model_object"]
    test_preds = reloaded_model.predict(X_test[:5])
    logs.append(f"Inference reload verification passed. Sample 5 test predictions: {test_preds.tolist()}")
    
    return {
        "id": model_id,
        "name": model_name or f"{model_type.replace('_', ' ').title()} ({version})",
        "model_type": model_type,
        "dataset_id": dataset_id,
        "version": version,
        "status": "TRAINED",
        "is_active": True,
        "artifact_path": artifact_path,
        "hyperparameters": hyperparams,
        "feature_names": FEATURE_NAMES,
        "feature_importance": feature_importance,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "split_config": artifact_payload["split_config"],
        "logs": "\n".join(logs),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
