import json
import uuid
import datetime
import pandas as pd
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import (
    DatasetModel, ObservationModel, ContractSpecModel, ScanModel,
    AnomalyCandidateModel, MLModelRecord, BacktestRecord, PaperResearchRecord,
    AuditEventModel, SystemSettingModel
)
from app.schemas.api_schemas import (
    ContractSpecSchema, NormalizationRequest, NormalizationResponse,
    DatasetSummarySchema, ScanRequest, ScanResponse, AnomalyCandidateSchema,
    MLModelTrainRequest, MLModelSchema, TournamentResponse,
    BacktestRequest, BacktestResponse, CostSimulationRequest, CostSimulationResponse,
    RealityCheckRequest, RealityCheckResponse, CounterfactualRequest, CounterfactualResponse,
    LifecycleResponse, RegimeAnalysisResponse, PaperResearchCreate, PaperResearchSchema,
    AuditEventSchema, SystemHealthResponse
)
from app.quant.contracts import list_all_specs, get_contract_spec
from app.quant.normalization import normalize_price_by_symbol
from app.quant.scanner import run_relative_value_scan
from app.quant.destroyer import OpportunityDestroyer
from app.quant.autopsy import generate_signal_autopsy
from app.quant.cost_simulator import calculate_mcx_transaction_costs
from app.quant.backtest import run_walk_forward_backtest
from app.quant.reality_check import run_reality_check_validation
from app.quant.counterfactual import run_counterfactual_simulation
from app.quant.regime import analyze_market_regimes
from app.quant.lifecycle import compute_contract_lifecycle
from app.quant.ml.pipeline import train_and_persist_model
from app.quant.ml.tournament import run_model_tournament
from app.quant.ml.drift import evaluate_model_drift
from app.quant.ml.features import engineer_timestamp_safe_features
from app.data.integrity import audit_dataset_integrity
from app.data.mcx_collector import attempt_mcx_automated_collection, ingest_mcx_file_to_database, OFFICIAL_MCX_URLS
from app.data.mcx_historical_data import seed_real_mcx_historical_dataset
from app.quant.ml.forecast import GoldPriceForecaster
from app.quant.ml.retraining import execute_retraining_pipeline, is_auto_retraining_enabled
from app.services.dataset_service import (
    get_active_dataset, set_active_dataset, get_dataset_dataframe,
    list_datasets, import_csv_dataset, seed_synthetic_dataset_if_empty
)
from app.services.casebook_service import (
    create_paper_research_record, update_paper_research_record, list_paper_research_records
)
from app.services.audit_service import log_audit_event, list_audit_events
from app.services.report_service import generate_research_report

router = APIRouter()

# ----------------- SYSTEM HEALTH & OVERVIEW -----------------

@router.get("/health", response_model=SystemHealthResponse)
def get_health(db: Session = Depends(get_db)):
    active_ds = get_active_dataset(db)
    total_datasets = db.query(DatasetModel).count()
    total_obs = db.query(ObservationModel).count()
    total_models = db.query(MLModelRecord).count()
    total_scans = db.query(ScanModel).count()
    return {
        "status": "HEALTHY",
        "database_connected": True,
        "active_dataset_id": active_ds.id if active_ds else None,
        "dataset_type": active_ds.source_type if active_ds else None,
        "total_datasets": total_datasets,
        "total_observations": total_obs,
        "trained_models_count": total_models,
        "completed_scans_count": total_scans,
        "system_version": settings.VERSION,
        "uptime_status": "ONLINE"
    }

@router.get("/overview")
def get_executive_overview(db: Session = Depends(get_db)):
    """
    Module A: Executive Overview.
    Provides dataset freshness, coverage, latest scans, active anomaly candidates,
    model status, and research activity.
    """
    active_ds = get_active_dataset(db)
    if not active_ds:
        active_ds = seed_synthetic_dataset_if_empty(db)

    df_obs = get_dataset_dataframe(db, active_ds.id)
    integrity = audit_dataset_integrity(df_obs)

    latest_scan = db.query(ScanModel).order_by(ScanModel.timestamp.desc()).first()
    latest_model = db.query(MLModelRecord).order_by(MLModelRecord.created_at.desc()).first()
    latest_backtest = db.query(BacktestRecord).order_by(BacktestRecord.created_at.desc()).first()

    # Active investigated candidates count
    investigate_cands = db.query(AnomalyCandidateModel).filter(AnomalyCandidateModel.verdict == "INVESTIGATE").count()
    suppressed_cands = db.query(AnomalyCandidateModel).filter(AnomalyCandidateModel.verdict == "SUPPRESSED").count()
    insufficient_cands = db.query(AnomalyCandidateModel).filter(AnomalyCandidateModel.verdict == "INSUFFICIENT_DATA").count()

    recent_events = list_audit_events(db, limit=8)

    return {
        "active_dataset": {
            "id": active_ds.id,
            "name": active_ds.name,
            "source_type": active_ds.source_type,
            "is_synthetic": (active_ds.source_type == "SYNTHETIC"),
            "row_count": active_ds.row_count,
            "start_date": active_ds.start_date,
            "end_date": active_ds.end_date,
            "instruments": active_ds.instruments.split(",") if active_ds.instruments else [],
            "validation_status": active_ds.validation_status
        },
        "data_quality": {
            "score": integrity["overall_quality_score"],
            "status": integrity["status"],
            "issues_count": len(integrity["issues"])
        },
        "latest_scan": {
            "id": latest_scan.id if latest_scan else None,
            "timestamp": latest_scan.timestamp.isoformat() if latest_scan else None,
            "pair": f"{latest_scan.pair_symbol_a}/{latest_scan.pair_symbol_b}" if latest_scan else "None",
            "total_candidates": latest_scan.total_candidates if latest_scan else 0,
            "investigate_count": latest_scan.investigate_count if latest_scan else 0,
            "suppressed_count": latest_scan.suppressed_count if latest_scan else 0,
            "insufficient_count": latest_scan.insufficient_count if latest_scan else 0,
        },
        "active_candidates_summary": {
            "investigate": investigate_cands,
            "suppressed": suppressed_cands,
            "insufficient": insufficient_cands
        },
        "latest_model": {
            "id": latest_model.id if latest_model else None,
            "name": latest_model.name if latest_model else "None",
            "model_type": latest_model.model_type if latest_model else "None",
            "status": latest_model.status if latest_model else "None",
            "version": latest_model.version if latest_model else "None"
        },
        "latest_backtest": {
            "id": latest_backtest.id if latest_backtest else None,
            "net_return_pct": latest_backtest.net_return_pct if latest_backtest else 0.0,
            "sharpe_ratio": latest_backtest.sharpe_ratio if latest_backtest else 0.0,
            "win_rate": latest_backtest.win_rate if latest_backtest else 0.0
        },
        "recent_research_activity": recent_events
    }

# ----------------- CONTRACT REGISTRY & NORMALIZATION -----------------

@router.get("/contracts", response_model=List[ContractSpecSchema])
def get_contracts():
    specs = list_all_specs()
    return list(specs.values())

@router.post("/contracts/normalize", response_model=NormalizationResponse)
def normalize_contract_price(req: NormalizationRequest):
    try:
        breakdown = normalize_price_by_symbol(req.symbol, req.quoted_price)
        return {"breakdown": breakdown}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- DATASETS & CSV IMPORT -----------------

@router.get("/datasets", response_model=List[DatasetSummarySchema])
def get_all_datasets(db: Session = Depends(get_db)):
    return list_datasets(db)

@router.post("/datasets/{dataset_id}/activate")
def activate_dataset_endpoint(dataset_id: str, db: Session = Depends(get_db)):
    ds = set_active_dataset(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": f"Dataset '{ds.name}' is now active", "dataset_id": ds.id}

@router.post("/datasets/import")
async def import_csv_endpoint(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    description: Optional[str] = Form(None),
    preferred_date_format: str = Form("DD/MM/YYYY"),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")

    result = ingest_mcx_file_to_database(
        db,
        file_bytes=contents,
        filename=file.filename or "uploaded_data.csv",
        dataset_name=dataset_name,
        source_type="REAL_MCX" if any(k in (file.filename or "").lower() for k in ["mcx", "bhav", "gold"]) else "IMPORTED_CSV",
        provenance=f"UPLOAD:{file.filename or 'unnamed'}",
        preferred_date_format=preferred_date_format
    )

    if not result["success"]:
        return {"success": False, "validation_report": result["validation_report"]}

    # Controlled auto-retraining if enabled and enough data
    try:
        execute_retraining_pipeline(db, dataset_id=result["dataset_id"], force=False)
    except Exception as e:
        logger.warning(f"Post-import retraining note: {e}")

    return {
        "success": True,
        "dataset_id": result["dataset_id"],
        "validation_report": result["validation_report"]
    }

# ----------------- MARKET EXPLORER (MODULE B) -----------------

@router.get("/market-explorer")
def get_market_explorer_data(
    symbol_a: str = Query("GOLDM"),
    symbol_b: str = Query("GOLD"),
    dataset_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    if not ds_id:
        ds = seed_synthetic_dataset_if_empty(db)
        ds_id = ds.id

    df_obs = get_dataset_dataframe(db, ds_id)
    if df_obs.empty:
        return {"observations": [], "statistics": {}}

    scan_res = run_relative_value_scan(
        df_obs,
        symbol_a=symbol_a,
        symbol_b=symbol_b
    )

    # Return series for charting
    series = []
    for c in scan_res["candidates"]:
        series.append({
            "timestamp": c["timestamp"],
            "price_a": c["price_a"],
            "price_b": c["price_b"],
            "normalized_a": c["normalized_a"],
            "normalized_b": c["normalized_b"],
            "raw_spread": c["raw_spread"],
            "percentage_spread": c["percentage_spread"],
            "rolling_median": c["rolling_median"],
            "rolling_mad": c["rolling_mad"],
            "robust_zscore": c["robust_zscore"],
            "percentile": c["percentile"],
            "expiry_distance_days": c["expiry_distance_days"],
            "volume_a": c["volume_a"],
            "volume_b": c["volume_b"],
            "verdict": c["verdict"]
        })

    return {
        "dataset_id": ds_id,
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "total_points": len(series),
        "series": series
    }

# ----------------- RELATIVE VALUE SCANNER & OPPORTUNITY DESTROYER (MODULES C & D) -----------------

@router.post("/scans/run", response_model=ScanResponse)
def execute_scan(req: ScanRequest, db: Session = Depends(get_db)):
    df_obs = get_dataset_dataframe(db, req.dataset_id)
    if df_obs.empty:
        raise HTTPException(status_code=400, detail="Selected dataset has no valid observations.")

    scan_res = run_relative_value_scan(
        df_obs,
        symbol_a=req.pair_symbol_a,
        symbol_b=req.pair_symbol_b,
        zscore_threshold=req.zscore_threshold,
        percentile_lower=req.percentile_lower,
        percentile_upper=req.percentile_upper,
        rolling_window_days=req.rolling_window_days,
        min_observations=req.min_observations,
        slippage_bps=req.slippage_bps,
        brokerage_bps=req.brokerage_bps,
        exchange_fees_bps=req.exchange_fees_bps,
        expiry_buffer_days=req.expiry_buffer_days
    )

    # Persist Scan record and Candidates to Database
    scan_id = scan_res["scan_id"]
    scan_model = ScanModel(
        id=scan_id,
        dataset_id=req.dataset_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        pair_symbol_a=req.pair_symbol_a,
        pair_symbol_b=req.pair_symbol_b,
        config_json=json.dumps(req.model_dump()),
        total_candidates=scan_res["total_candidates"],
        investigate_count=scan_res["investigate_count"],
        suppressed_count=scan_res["suppressed_count"],
        insufficient_count=scan_res["insufficient_count"]
    )
    db.add(scan_model)
    db.commit()

    candidate_models = []
    for c in scan_res["candidates"]:
        cand = AnomalyCandidateModel(
            id=c["id"],
            scan_id=scan_id,
            timestamp=c["timestamp"],
            symbol_a=c["symbol_a"],
            symbol_b=c["symbol_b"],
            expiry_a=c["expiry_a"],
            expiry_b=c["expiry_b"],
            price_a=c["price_a"],
            price_b=c["price_b"],
            normalized_a=c["normalized_a"],
            normalized_b=c["normalized_b"],
            raw_spread=c["raw_spread"],
            percentage_spread=c["percentage_spread"],
            rolling_mean=c["rolling_mean"],
            rolling_std=c["rolling_std"],
            rolling_median=c["rolling_median"],
            rolling_mad=c["rolling_mad"],
            robust_zscore=c["robust_zscore"],
            percentile=c["percentile"],
            expiry_distance_days=c["expiry_distance_days"],
            volume_a=c["volume_a"],
            volume_b=c["volume_b"],
            verdict=c["verdict"],
            rejection_reasons_json=json.dumps(c["rejection_reasons"]),
            destroyer_checks_json=json.dumps(c["destroyer_checks"]),
            autopsy_features_json=json.dumps(c["autopsy_features"]),
            estimated_cost_bps=c["estimated_cost_bps"]
        )
        candidate_models.append(cand)

    db.bulk_save_objects(candidate_models)
    db.commit()

    log_audit_event(
        db,
        event_type="SCAN_COMPLETED",
        entity_type="ScanModel",
        entity_id=scan_id,
        summary=f"Completed scan on {req.pair_symbol_a}/{req.pair_symbol_b}: {scan_res['investigate_count']} Investigate, {scan_res['suppressed_count']} Suppressed",
        details=req.model_dump()
    )

    return {
        "scan_id": scan_id,
        "dataset_id": req.dataset_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_candidates": scan_res["total_candidates"],
        "investigate_count": scan_res["investigate_count"],
        "suppressed_count": scan_res["suppressed_count"],
        "insufficient_count": scan_res["insufficient_count"],
        "candidates": scan_res["candidates"]
    }

@router.get("/candidates/{candidate_id}")
def get_candidate_details(candidate_id: str, db: Session = Depends(get_db)):
    cand = db.query(AnomalyCandidateModel).filter(AnomalyCandidateModel.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {
        "id": cand.id,
        "scan_id": cand.scan_id,
        "timestamp": cand.timestamp,
        "symbol_a": cand.symbol_a,
        "symbol_b": cand.symbol_b,
        "expiry_a": cand.expiry_a,
        "expiry_b": cand.expiry_b,
        "price_a": cand.price_a,
        "price_b": cand.price_b,
        "normalized_a": cand.normalized_a,
        "normalized_b": cand.normalized_b,
        "raw_spread": cand.raw_spread,
        "percentage_spread": cand.percentage_spread,
        "robust_zscore": cand.robust_zscore,
        "percentile": cand.percentile,
        "expiry_distance_days": cand.expiry_distance_days,
        "verdict": cand.verdict,
        "rejection_reasons": json.loads(cand.rejection_reasons_json or "[]"),
        "destroyer_checks": json.loads(cand.destroyer_checks_json or "{}"),
        "autopsy_features": json.loads(cand.autopsy_features_json or "{}"),
        "estimated_cost_bps": cand.estimated_cost_bps
    }

# ----------------- MACHINE LEARNING & MODEL LAB (MODULES G, H, I) -----------------

@router.post("/models/train", response_model=MLModelSchema)
def train_model_endpoint(req: MLModelTrainRequest, db: Session = Depends(get_db)):
    df_obs = get_dataset_dataframe(db, req.dataset_id)
    if df_obs.empty:
        raise HTTPException(status_code=400, detail="Dataset has no observations.")

    # Align primary benchmark GOLDM vs GOLD
    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    if not scan_res["candidates"]:
        raise HTTPException(status_code=400, detail="Could not align observations for training.")

    df_aligned = pd.DataFrame(scan_res["candidates"])

    hyperparams = {
        "contamination": req.contamination,
        "n_estimators": req.n_estimators,
        "random_state": req.random_state
    }

    result = train_and_persist_model(
        df_aligned=df_aligned,
        model_type=req.model_type,
        model_name=req.name,
        dataset_id=req.dataset_id,
        train_pct=req.train_split_pct,
        val_pct=req.val_split_pct,
        hyperparams=hyperparams
    )

    # Persist in DB
    model_record = MLModelRecord(
        id=result["id"],
        name=result["name"],
        model_type=result["model_type"],
        dataset_id=result["dataset_id"],
        version=result["version"],
        status=result["status"],
        is_active=True,
        artifact_path=result["artifact_path"],
        hyperparameters_json=json.dumps(result["hyperparameters"]),
        feature_names_json=json.dumps(result["feature_names"]),
        train_metrics_json=json.dumps(result["train_metrics"]),
        val_metrics_json=json.dumps(result["val_metrics"]),
        test_metrics_json=json.dumps(result["test_metrics"]),
        split_config_json=json.dumps(result["split_config"]),
        logs=result["logs"],
        created_at=datetime.datetime.utcnow()
    )
    db.add(model_record)
    db.commit()

    log_audit_event(
        db,
        event_type="MODEL_TRAINED",
        entity_type="MLModelRecord",
        entity_id=result["id"],
        summary=f"Trained {result['model_type']} model ({result['version']}) with test detection rate: {result['test_metrics']['detection_rate_pct']}%",
        details={"model_id": result["id"], "artifact_path": result["artifact_path"]}
    )

    return {
        "id": result["id"],
        "name": result["name"],
        "model_type": result["model_type"],
        "dataset_id": result["dataset_id"],
        "version": result["version"],
        "status": result["status"],
        "is_active": True,
        "artifact_path": result["artifact_path"],
        "hyperparameters": result["hyperparameters"],
        "feature_names": result["feature_names"],
        "train_metrics": result["train_metrics"],
        "val_metrics": result["val_metrics"],
        "test_metrics": result["test_metrics"],
        "split_config": result["split_config"],
        "logs": result["logs"],
        "created_at": result["created_at"]
    }

@router.get("/models")
def list_models_endpoint(db: Session = Depends(get_db)):
    models = db.query(MLModelRecord).order_by(MLModelRecord.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "dataset_id": m.dataset_id,
            "version": m.version,
            "status": m.status,
            "is_active": m.is_active,
            "artifact_path": m.artifact_path,
            "hyperparameters": json.loads(m.hyperparameters_json or "{}"),
            "train_metrics": json.loads(m.train_metrics_json or "{}"),
            "val_metrics": json.loads(m.val_metrics_json or "{}"),
            "test_metrics": json.loads(m.test_metrics_json or "{}"),
            "split_config": json.loads(m.split_config_json or "{}"),
            "created_at": m.created_at.isoformat()
        }
        for m in models
    ]

@router.get("/tournament", response_model=TournamentResponse)
def get_tournament_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    df_obs = get_dataset_dataframe(db, ds_id)
    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    df_aligned = pd.DataFrame(scan_res["candidates"])
    return run_model_tournament(df_aligned, dataset_id=ds_id)

@router.get("/drift")
def get_model_drift_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    df_obs = get_dataset_dataframe(db, ds_id)
    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    df_aligned = pd.DataFrame(scan_res["candidates"])
    df_feat = engineer_timestamp_safe_features(df_aligned)
    
    # Chronological partition: First 70% as training reference, last 30% as recent inference
    n = len(df_feat)
    split_pt = int(n * 0.70)
    df_train_ref = df_feat.iloc[:split_pt]
    df_recent = df_feat.iloc[split_pt:]

    return evaluate_model_drift(df_train_ref, df_recent)

# ----------------- BACKTESTING LAB (MODULE J) -----------------

@router.post("/backtests/run", response_model=BacktestResponse)
def execute_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    df_obs = get_dataset_dataframe(db, req.dataset_id)
    if df_obs.empty:
        raise HTTPException(status_code=400, detail="Dataset has no observations for backtest.")

    res = run_walk_forward_backtest(
        df_observations=df_obs,
        symbol_a=req.pair_symbol_a,
        symbol_b=req.pair_symbol_b,
        entry_zscore=req.entry_zscore,
        exit_zscore=req.exit_zscore,
        max_holding_days=req.holding_period_days,
        position_size_inr=req.position_size_inr,
        slippage_bps=req.slippage_bps,
        brokerage_bps=req.brokerage_bps,
        exchange_fees_bps=req.exchange_fees_bps,
        execution_delay_days=req.execution_delay_days
    )

    # Persist in DB
    bt_record = BacktestRecord(
        id=res["backtest_id"],
        model_id=req.model_id,
        dataset_id=req.dataset_id,
        name=res["strategy_name"],
        strategy_config_json=json.dumps(req.model_dump()),
        start_date=res["start_date"],
        end_date=res["end_date"],
        total_signals=res["total_signals"],
        executed_trades=res["executed_trades"],
        gross_return_pct=res["gross_return_pct"],
        net_return_pct=res["net_return_pct"],
        total_costs_bps=res["total_costs_bps"],
        max_drawdown_pct=res["max_drawdown_pct"],
        sharpe_ratio=res["sharpe_ratio"],
        win_rate=res["win_rate"],
        metrics_json=json.dumps({
            "profit_factor": res["profit_factor"],
            "cost_drag_inr": res["cost_drag_inr"]
        }),
        equity_curve_json=json.dumps(res["equity_curve"]),
        trade_log_json=json.dumps(res["trades"]),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(bt_record)
    db.commit()

    log_audit_event(
        db,
        event_type="BACKTEST_COMPLETED",
        entity_type="BacktestRecord",
        entity_id=res["backtest_id"],
        summary=f"Completed walk-forward backtest: Net Return {res['net_return_pct']}%, Sharpe {res['sharpe_ratio']}",
        details=req.model_dump()
    )

    return res

# ----------------- REALITY CHECK & COST SIMULATOR (MODULES K & L) -----------------

@router.post("/cost-simulator", response_model=CostSimulationResponse)
def run_cost_simulation_endpoint(req: CostSimulationRequest):
    return calculate_mcx_transaction_costs(
        quoted_price_per_10g=req.quoted_price_per_10g,
        contract_lot_grams=req.contract_lot_grams,
        position_lots=req.position_lots,
        brokerage_bps=req.brokerage_bps,
        exchange_fees_bps=req.exchange_fees_bps,
        sebi_turnover_bps=req.sebi_turnover_bps,
        stamp_duty_bps=req.stamp_duty_bps,
        gst_on_charges_pct=req.gst_on_charges_pct,
        bid_ask_half_spread_bps=req.bid_ask_half_spread_bps,
        market_impact_bps=req.market_impact_bps,
        slippage_bps=req.slippage_bps
    )

@router.post("/reality-check", response_model=RealityCheckResponse)
def run_reality_check_endpoint(req: RealityCheckRequest, db: Session = Depends(get_db)):
    df_obs = get_dataset_dataframe(db, req.dataset_id)
    if df_obs.empty:
        raise HTTPException(status_code=400, detail="Dataset has no observations.")
    return run_reality_check_validation(
        df_observations=df_obs,
        symbol_a=req.pair_symbol_a,
        symbol_b=req.pair_symbol_b,
        rolling_windows=req.rolling_windows,
        zscore_thresholds=req.zscore_thresholds,
        num_bootstrap_samples=req.num_bootstrap_samples
    )

# ----------------- COUNTERFACTUAL LAB & LIFECYCLE (MODULES M & N) -----------------

@router.post("/counterfactual", response_model=CounterfactualResponse)
def run_counterfactual_endpoint(req: CounterfactualRequest, db: Session = Depends(get_db)):
    cand = db.query(AnomalyCandidateModel).filter(AnomalyCandidateModel.id == req.candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate_dict = {
        "id": cand.id,
        "price_a": cand.price_a,
        "price_b": cand.price_b,
        "normalized_a": cand.normalized_a,
        "normalized_b": cand.normalized_b,
        "raw_spread": cand.raw_spread,
        "percentage_spread": cand.percentage_spread,
        "robust_zscore": cand.robust_zscore,
        "expiry_distance_days": cand.expiry_distance_days,
        "volume_a": cand.volume_a,
        "volume_b": cand.volume_b,
        "verdict": cand.verdict
    }

    return run_counterfactual_simulation(
        original_candidate=candidate_dict,
        modified_slippage_bps=req.modified_slippage_bps,
        modified_zscore_threshold=req.modified_zscore_threshold,
        modified_expiry_buffer_days=req.modified_expiry_buffer_days
    )

@router.get("/lifecycle", response_model=LifecycleResponse)
def get_lifecycle_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    df_obs = get_dataset_dataframe(db, ds_id)
    return compute_contract_lifecycle(df_obs)

@router.get("/regime", response_model=RegimeAnalysisResponse)
def get_regime_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    df_obs = get_dataset_dataframe(db, ds_id)
    return analyze_market_regimes(df_obs)

# ----------------- DATA INTEGRITY GUARDIAN (MODULE P) -----------------

@router.get("/integrity")
def get_data_integrity_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    df_obs = get_dataset_dataframe(db, ds_id)
    return audit_dataset_integrity(df_obs)

# ----------------- PAPER RESEARCH CASEBOOK (MODULE R) -----------------

@router.get("/casebook", response_model=List[PaperResearchSchema])
def get_casebook_records(status: Optional[str] = None, db: Session = Depends(get_db)):
    return list_paper_research_records(db, status=status)

@router.post("/casebook", response_model=PaperResearchSchema)
def create_casebook_record(req: PaperResearchCreate, db: Session = Depends(get_db)):
    rec = create_paper_research_record(db, req.model_dump())
    return {
        "id": rec.id,
        "candidate_id": rec.candidate_id,
        "symbol_pair": rec.symbol_pair,
        "observation_date": rec.observation_date,
        "initial_verdict": rec.initial_verdict,
        "initial_score": rec.initial_score,
        "spread_bps": rec.spread_bps,
        "rationale": rec.rationale,
        "expected_horizon_days": rec.expected_horizon_days,
        "entry_price_spread": rec.entry_price_spread,
        "exit_observed_spread": rec.exit_observed_spread,
        "cost_assumptions": json.loads(rec.cost_assumptions_json or "{}"),
        "status": rec.status,
        "notes": rec.notes,
        "tags": rec.tags,
        "updated_at": rec.updated_at.isoformat(),
        "created_at": rec.created_at.isoformat()
    }

@router.patch("/casebook/{case_id}")
def update_casebook_endpoint(
    case_id: str,
    status: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    exit_observed_spread: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    rec = update_paper_research_record(
        db, case_id, status=status, notes=notes, exit_observed_spread=exit_observed_spread
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Case record not found")
    return {"message": "Updated successfully", "status": rec.status}

# ----------------- AUDIT & RESEARCH REPORTS (MODULES S & T) -----------------

@router.get("/audit", response_model=List[AuditEventSchema])
def get_audit_trail_endpoint(limit: int = 50, event_type: Optional[str] = None, db: Session = Depends(get_db)):
    return list_audit_events(db, limit=limit, event_type=event_type)

@router.post("/reports/generate")
def generate_report_endpoint(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    ds = db.query(DatasetModel).filter(DatasetModel.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds_info = {
        "id": ds.id,
        "name": ds.name,
        "source_type": ds.source_type,
        "file_hash": ds.file_hash,
        "row_count": ds.row_count,
        "start_date": ds.start_date,
        "end_date": ds.end_date,
        "instruments": ds.instruments
    }

    latest_scan = db.query(ScanModel).order_by(ScanModel.timestamp.desc()).first()
    scan_info = None
    if latest_scan:
        scan_info = {
            "pair_symbol_a": latest_scan.pair_symbol_a,
            "pair_symbol_b": latest_scan.pair_symbol_b,
            "total_candidates": latest_scan.total_candidates,
            "investigate_count": latest_scan.investigate_count,
            "suppressed_count": latest_scan.suppressed_count,
            "insufficient_count": latest_scan.insufficient_count
        }

    latest_bt = db.query(BacktestRecord).order_by(BacktestRecord.created_at.desc()).first()
    bt_info = None
    if latest_bt:
        bt_info = {
            "total_signals": latest_bt.total_signals,
            "executed_trades": latest_bt.executed_trades,
            "gross_return_pct": latest_bt.gross_return_pct,
            "net_return_pct": latest_bt.net_return_pct,
            "cost_drag_inr": json.loads(latest_bt.metrics_json or "{}").get("cost_drag_inr", 0.0),
            "total_costs_bps": latest_bt.total_costs_bps,
            "sharpe_ratio": latest_bt.sharpe_ratio,
            "max_drawdown_pct": latest_bt.max_drawdown_pct,
            "win_rate": latest_bt.win_rate,
            "profit_factor": json.loads(latest_bt.metrics_json or "{}").get("profit_factor", 0.0)
        }

    cost_info = calculate_mcx_transaction_costs()

    rep = generate_research_report(
        dataset_info=ds_info,
        scan_info=scan_info,
        backtest_info=bt_info,
        cost_info=cost_info
    )

    log_audit_event(
        db,
        event_type="REPORT_GENERATED",
        entity_type="Report",
        entity_id=rep["report_id"],
        summary=f"Generated institutional research report {rep['report_id']}",
        details={"file_path": rep["file_path"]}
    )

    return rep

@router.get("/data/collection-status")
def get_data_collection_status(db: Session = Depends(get_db)):
    """
    Returns the current status of automated MCX collection, provenance, and latest file history.
    """
    active_ds = get_active_dataset(db)
    last_collection_event = db.query(AuditEventModel).filter(
        AuditEventModel.event_type.in_(["REAL_MCX_DATA_IMPORTED", "DATASET_IMPORTED", "DATASET_SEEDED"])
    ).order_by(AuditEventModel.timestamp.desc()).first()

    return {
        "status": "ONLINE",
        "official_sources": OFFICIAL_MCX_URLS,
        "active_dataset": {
            "id": active_ds.id if active_ds else None,
            "name": active_ds.name if active_ds else None,
            "source_type": active_ds.source_type if active_ds else None,
            "provenance": getattr(active_ds, "provenance", "DEFAULT") if active_ds else None,
            "collection_timestamp": active_ds.collection_timestamp.isoformat() if (active_ds and active_ds.collection_timestamp) else None,
            "row_count": active_ds.row_count if active_ds else 0,
            "start_date": active_ds.start_date if active_ds else None,
            "end_date": active_ds.end_date if active_ds else None
        },
        "last_collection_event": {
            "event_type": last_collection_event.event_type if last_collection_event else None,
            "summary": last_collection_event.summary if last_collection_event else "No imports logged yet",
            "timestamp": last_collection_event.timestamp.isoformat() if last_collection_event else None
        }
    }

@router.post("/data/collect-mcx")
def trigger_mcx_collection(target_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Executes automated collection attempt from official MCX Bhavcopy.
    Complies with access control policies: does not bypass WAF/CAPTCHAs, handles weekends/holidays,
    and returns transparent operational report.
    """
    res = attempt_mcx_automated_collection(target_date=target_date)
    log_audit_event(
        db,
        event_type="MCX_COLLECTION_ATTEMPTED",
        entity_type="MCX_Collector",
        entity_id=target_date or "today",
        summary=f"Automated collection attempt: {res.get('status')} - {res.get('message', '')[:60]}",
        details=res
    )
    return res

@router.post("/data/seed-real-mcx")
def seed_real_mcx_data_endpoint(db: Session = Depends(get_db)):
    """
    Ingests and activates the authentic MCX Gold historical Bhavcopy dataset into the database.
    """
    res = seed_real_mcx_historical_dataset(db)
    if res.get("success"):
        # Trigger automatic model retraining
        execute_retraining_pipeline(db, dataset_id=res["dataset_id"], force=True)
    return res

@router.get("/forecast")
def get_price_forecast(dataset_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Executes or returns price forecasting evaluation using chronological holdout validation,
    comparing candidate model vs persistent baseline with MAE, RMSE, and hit rate.
    """
    ds_id = dataset_id or (get_active_dataset(db).id if get_active_dataset(db) else None)
    if not ds_id:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    df_obs = get_dataset_dataframe(db, ds_id)
    if df_obs.empty or len(df_obs) < 25:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "INSUFFICIENT_DATA: Less than 25 valid observations available for chronological holdout forecasting.",
            "metrics": {},
            "test_series": []
        }

    scan_res = run_relative_value_scan(df_obs, symbol_a="GOLDM", symbol_b="GOLD")
    candidates = scan_res.get("candidates", [])
    if len(candidates) < 25:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": f"INSUFFICIENT_DATA: Insufficient aligned pairs ({len(candidates)}).",
            "metrics": {},
            "test_series": []
        }

    forecaster = GoldPriceForecaster(min_observations=25)
    result = forecaster.train_and_evaluate(pd.DataFrame(candidates))
    return result

@router.post("/models/retrain")
def trigger_retraining_endpoint(
    dataset_id: Optional[str] = Query(None),
    force: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Triggers controlled ML model retraining pipeline (Isolation Forest + Price Forecaster).
    """
    res = execute_retraining_pipeline(db, dataset_id=dataset_id, force=force)
    return res

@router.get("/settings")
def get_system_settings_endpoint(db: Session = Depends(get_db)):
    # Check if custom settings are stored
    saved_settings = db.query(SystemSettingModel).all()
    custom_map = {}
    for s in saved_settings:
        try:
            custom_map[s.key] = json.loads(s.value_json)
        except Exception:
            custom_map[s.key] = s.value_json

    return {
        "default_zscore_threshold": settings.DEFAULT_ZSCORE_THRESHOLD,
        "default_percentile_lower": settings.DEFAULT_PERCENTILE_LOWER,
        "default_percentile_upper": settings.DEFAULT_PERCENTILE_UPPER,
        "default_rolling_window_days": settings.DEFAULT_ROLLING_WINDOW_DAYS,
        "default_min_observations": settings.DEFAULT_MIN_OBSERVATIONS,
        "default_expiry_proximity_days": settings.DEFAULT_EXPIRY_PROXIMITY_DAYS,
        "default_slippage_bps": settings.DEFAULT_SLIPPAGE_BPS,
        "default_brokerage_bps": settings.DEFAULT_BROKERAGE_BPS,
        "default_exchange_fees_bps": settings.DEFAULT_EXCHANGE_FEES_BPS,
        "auto_retraining_enabled": is_auto_retraining_enabled(db),
        "custom_settings": custom_map
    }

@router.post("/settings")
def update_system_setting(
    key: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Persists configuration parameters and preferences.
    """
    setting = db.query(SystemSettingModel).filter(SystemSettingModel.key == key).first()
    if not setting:
        setting = SystemSettingModel(
            key=key,
            value_json=value if (value.startswith("{") or value.startswith("[")) else json.dumps({"value": value}),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(setting)
    else:
        setting.value_json = value if (value.startswith("{") or value.startswith("[")) else json.dumps({"value": value})
        setting.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return {"success": True, "key": key}

