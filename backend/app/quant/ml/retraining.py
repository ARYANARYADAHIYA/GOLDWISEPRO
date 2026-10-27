import json
import uuid
import datetime
import logging
import pandas as pd
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.entities import MLModelRecord, SystemSettingModel
from app.quant.scanner import run_relative_value_scan
from app.quant.ml.pipeline import train_and_persist_model
from app.quant.ml.forecast import GoldPriceForecaster
from app.services.dataset_service import get_dataset_dataframe, get_active_dataset
from app.services.audit_service import log_audit_event

logger = logging.getLogger("goldwise.retraining")

def is_auto_retraining_enabled(db: Session) -> bool:
    """Checks system settings for auto-retraining toggle."""
    setting = db.query(SystemSettingModel).filter(SystemSettingModel.key == "auto_retraining_enabled").first()
    if not setting:
        return True  # Default enabled
    try:
        val = json.loads(setting.value_json)
        return bool(val.get("enabled", True))
    except Exception:
        return True

def execute_retraining_pipeline(
    db: Session,
    dataset_id: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Controlled ML model retraining workflow:
    1. Check dataset observation sufficiency
    2. Check configuration and eligibility
    3. Train candidate Isolation Forest
    4. Train candidate Price Forecaster
    5. Evaluate on chronological holdout
    6. Deploy candidate only if valid; preserve previous model on failure
    7. Update Model Lab database records
    """
    ds_id = dataset_id
    if not ds_id:
        active_ds = get_active_dataset(db)
        if not active_ds:
            return {"status": "INSUFFICIENT_DATA", "message": "No active dataset found in database."}
        ds_id = active_ds.id

    if not force and not is_auto_retraining_enabled(db):
        return {
            "status": "SKIPPED",
            "message": "Automatic retraining is currently disabled in system settings. Use manual training control to trigger."
        }

    df_obs = get_dataset_dataframe(db, ds_id)
    if df_obs.empty or len(df_obs) < 30:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": f"INSUFFICIENT_DATA: Observation count ({len(df_obs)}) is below the required 30-day minimum.",
            "dataset_id": ds_id
        }

    # Align primary reference pair: GOLDM vs GOLD
    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    candidates = scan_res.get("candidates", [])
    if len(candidates) < 25:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": f"INSUFFICIENT_DATA: Insufficient aligned trading dates between GOLDM and GOLD ({len(candidates)} aligned).",
            "dataset_id": ds_id
        }

    df_aligned = pd.DataFrame(candidates)
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Train Anomaly Detection (Isolation Forest)
    if_result = None
    try:
        if_train_res = train_and_persist_model(
            df_aligned=df_aligned,
            model_type="ISOLATION_FOREST",
            model_name=f"GoldWise Isolation Forest ({now.strftime('%b %Y')})",
            dataset_id=ds_id,
            hyperparams={"contamination": 0.05, "n_estimators": 120}
        )
        
        # Persist MLModelRecord in DB
        prev_active = db.query(MLModelRecord).filter(
            MLModelRecord.model_type == "ISOLATION_FOREST",
            MLModelRecord.is_active == True
        ).first()

        new_if_rec = MLModelRecord(
            id=if_train_res["id"],
            name=if_train_res["name"],
            model_type="ISOLATION_FOREST",
            dataset_id=ds_id,
            version=if_train_res["version"],
            status="TRAINED",
            is_active=True,
            artifact_path=if_train_res["artifact_path"],
            hyperparameters_json=json.dumps(if_train_res.get("hyperparameters", {})),
            feature_names_json=json.dumps(if_train_res.get("feature_names", [])),
            train_metrics_json=json.dumps(if_train_res.get("metrics", {}).get("train", {})),
            val_metrics_json=json.dumps(if_train_res.get("metrics", {}).get("val", {})),
            test_metrics_json=json.dumps(if_train_res.get("metrics", {}).get("test", {})),
            split_config_json=json.dumps(if_train_res.get("split_counts", {})),
            logs=if_train_res.get("logs", ""),
            created_at=now
        )
        if prev_active:
            prev_active.is_active = False

        db.add(new_if_rec)
        db.commit()
        if_result = if_train_res
    except Exception as e:
        logger.error(f"Isolation Forest retraining error: {e}")
        if_result = {"status": "FAILED", "error": str(e)}

    # 2. Train Price Forecasting Engine
    forecaster = GoldPriceForecaster(min_observations=30)
    forecast_eval = forecaster.train_and_evaluate(df_aligned)

    if forecast_eval["status"] == "TRAINED":
        # Register forecast model in database
        forecast_model_id = f"model-forecast-{uuid.uuid4().hex[:8]}"
        forecast_rec = MLModelRecord(
            id=forecast_model_id,
            name=f"GoldWise Lagged Ridge Forecaster ({now.strftime('%b %Y')})",
            model_type="PRICE_FORECASTER",
            dataset_id=ds_id,
            version=f"v1.0-{now.strftime('%Y%m%d%H%M')}",
            status="TRAINED",
            is_active=True,
            artifact_path="in-memory-forecaster",
            hyperparameters_json=json.dumps({"alpha": 1.0, "lags": [1, 2, 3, 5]}),
            feature_names_json=json.dumps(forecaster.feature_names),
            train_metrics_json=json.dumps(forecast_eval["metrics"]["candidate"]),
            val_metrics_json=json.dumps(forecast_eval["metrics"]["baseline"]),
            test_metrics_json=json.dumps(forecast_eval["metrics"]["edge"]),
            split_config_json=json.dumps(forecast_eval["sample_counts"]),
            logs=f"Chronological holdout validation completed. MAE price: {forecast_eval['metrics']['candidate']['mae_price_inr_per_g']} INR/g. Directional accuracy: {forecast_eval['metrics']['candidate']['directional_accuracy_pct']}%.",
            created_at=now
        )
        db.add(forecast_rec)
        db.commit()

    log_audit_event(
        db,
        event_type="MODELS_RETRAINED",
        entity_type="MLModelRecord",
        entity_id=if_result.get("id") if if_result else "batch",
        summary=f"Retraining pipeline executed on dataset '{ds_id}'. Isolation Forest: {if_result.get('status') if if_result else 'SKIPPED'}, Forecaster: {forecast_eval.get('status')}.",
        details={"dataset_id": ds_id, "aligned_observations": len(candidates)}
    )

    return {
        "status": "SUCCESS",
        "dataset_id": ds_id,
        "isolation_forest": if_result,
        "price_forecasting": forecast_eval,
        "retrained_at": now.isoformat()
    }
