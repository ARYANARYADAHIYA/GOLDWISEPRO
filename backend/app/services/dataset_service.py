import json
import uuid
import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.entities import DatasetModel, ObservationModel, ContractSpecModel
from app.quant.contracts import OFFICIAL_MCX_SPECS
from app.quant.synthetic import generate_synthetic_mcx_dataset
from app.data.importer import parse_and_validate_csv
from app.data.integrity import audit_dataset_integrity
from app.services.audit_service import log_audit_event

def seed_contract_specs_if_empty(db: Session):
    existing_count = db.query(ContractSpecModel).count()
    if existing_count == 0:
        for sym, spec in OFFICIAL_MCX_SPECS.items():
            record = ContractSpecModel(
                symbol=spec.symbol,
                name=spec.name,
                trading_unit_grams=spec.trading_unit_grams,
                quotation_basis_grams=spec.quotation_basis_grams,
                purity_per_mille=spec.purity_per_mille,
                tick_size=spec.tick_size,
                lot_size_grams=spec.lot_size_grams,
                delivery_unit_grams=spec.delivery_unit_grams,
                effective_date=spec.effective_date,
                source_verification_status=spec.source_verification_status,
                notes=spec.notes,
                updated_at=datetime.datetime.utcnow()
            )
            db.add(record)
        db.commit()

def seed_synthetic_dataset_if_empty(db: Session) -> DatasetModel:
    seed_contract_specs_if_empty(db)
    existing_dataset = db.query(DatasetModel).filter(DatasetModel.source_type == "SYNTHETIC").first()
    if existing_dataset:
        return existing_dataset

    dataset_id = "ds-synthetic-mcx-gold-baseline"
    records = generate_synthetic_mcx_dataset(start_date="2026-04-01", num_days=140, random_seed=42)
    
    dates = [r["timestamp"] for r in records]
    symbols = sorted(list(set(r["symbol"] for r in records)))
    
    dataset = DatasetModel(
        id=dataset_id,
        name="Deterministic MCX Gold Benchmark (Synthetic Reference)",
        description="Deterministic synthetic MCX gold time series with 8 injected market, quotation, and expiry scenarios for reproducible research validation.",
        source_type="SYNTHETIC",
        file_hash="deterministic-seed-42-v1",
        row_count=len(records),
        start_date=min(dates),
        end_date=max(dates),
        instruments=",".join(symbols),
        is_active=True,
        validation_status="VALID",
        validation_report_json=json.dumps({"synthetic_seed": 42, "num_observations": len(records), "injected_scenarios_count": 8}),
        created_at=datetime.datetime.utcnow()
    )
    db.add(dataset)
    db.commit()

    # Batch insert observations
    obs_models = [
        ObservationModel(
            dataset_id=dataset_id,
            symbol=r["symbol"],
            expiry_date=r["expiry_date"],
            timestamp=r["timestamp"],
            open_price=r["open_price"],
            high_price=r["high_price"],
            low_price=r["low_price"],
            close_price=r["close_price"],
            volume=r["volume"],
            open_interest=r["open_interest"],
            quotation_basis=r["quotation_basis"],
            purity=r["purity"],
            normalized_price_pure_gram=r["normalized_price_pure_gram"],
            is_quarantined=r["is_quarantined"],
            quarantine_reason=r["quarantine_reason"]
        )
        for r in records
    ]
    db.bulk_save_objects(obs_models)
    db.commit()

    log_audit_event(
        db,
        event_type="DATASET_SEEDED",
        entity_type="DatasetModel",
        entity_id=dataset_id,
        summary=f"Seeded deterministic synthetic dataset with {len(records)} observations.",
        details={"seed": 42, "symbols": symbols}
    )
    return dataset

def import_csv_dataset(
    db: Session,
    file_bytes: bytes,
    dataset_name: str,
    description: Optional[str] = None,
    preferred_date_format: str = "DD/MM/YYYY"
) -> Dict[str, Any]:
    validation_res = parse_and_validate_csv(file_bytes, preferred_date_format=preferred_date_format)
    if not validation_res["is_valid"]:
        return {
            "success": False,
            "validation_report": validation_res,
            "dataset_id": None
        }

    dataset_id = f"ds-csv-{uuid.uuid4().hex[:8]}"
    obs_list = validation_res["observations"]

    # Deactivate other datasets if active
    db.query(DatasetModel).update({DatasetModel.is_active: False})

    dataset = DatasetModel(
        id=dataset_id,
        name=dataset_name,
        description=description or "User imported genuine MCX Bhavcopy CSV dataset.",
        source_type="IMPORTED_CSV",
        file_hash=validation_res["file_hash"],
        row_count=len(obs_list),
        start_date=validation_res["start_date"],
        end_date=validation_res["end_date"],
        instruments=validation_res["instruments"],
        is_active=True,
        validation_status="VALID",
        validation_report_json=json.dumps({
            "duplicate_count": validation_res["duplicate_count"],
            "ambiguous_date_count": validation_res["ambiguous_date_count"],
            "warnings": validation_res["warnings"],
            "errors": validation_res["errors"]
        }),
        created_at=datetime.datetime.utcnow()
    )
    db.add(dataset)
    db.commit()

    obs_models = [
        ObservationModel(
            dataset_id=dataset_id,
            symbol=o["symbol"],
            expiry_date=o["expiry_date"],
            timestamp=o["timestamp"],
            open_price=o["open_price"],
            high_price=o["high_price"],
            low_price=o["low_price"],
            close_price=o["close_price"],
            previous_close=o.get("previous_close"),
            volume=o.get("volume", 0.0),
            turnover=o.get("turnover", 0.0),
            open_interest=o.get("open_interest", 0.0),
            quotation_basis=o["quotation_basis"],
            purity=o["purity"],
            normalized_price_pure_gram=o["normalized_price_pure_gram"],
            is_quarantined=o["is_quarantined"],
            quarantine_reason=o["quarantine_reason"]
        )
        for o in obs_list
    ]
    db.bulk_save_objects(obs_models)
    db.commit()

    log_audit_event(
        db,
        event_type="DATASET_IMPORTED",
        entity_type="DatasetModel",
        entity_id=dataset_id,
        summary=f"Imported CSV dataset '{dataset_name}' with {len(obs_list)} valid observations.",
        details={"file_hash": validation_res["file_hash"], "row_count": len(obs_list)}
    )

    return {
        "success": True,
        "dataset_id": dataset_id,
        "validation_report": validation_res
    }

def get_active_dataset(db: Session) -> Optional[DatasetModel]:
    ds = db.query(DatasetModel).filter(DatasetModel.is_active == True).first()
    if not ds:
        ds = db.query(DatasetModel).first()
    return ds

def set_active_dataset(db: Session, dataset_id: str) -> Optional[DatasetModel]:
    db.query(DatasetModel).update({DatasetModel.is_active: False})
    ds = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if ds:
        ds.is_active = True
        db.commit()
        db.refresh(ds)
        log_audit_event(
            db,
            event_type="DATASET_ACTIVATED",
            entity_type="DatasetModel",
            entity_id=dataset_id,
            summary=f"Switched active dataset to '{ds.name}'",
            details={"dataset_id": dataset_id, "source_type": ds.source_type}
        )
    return ds

def get_dataset_dataframe(db: Session, dataset_id: str) -> pd.DataFrame:
    observations = db.query(ObservationModel).filter(
        ObservationModel.dataset_id == dataset_id,
        ObservationModel.is_quarantined == False
    ).order_by(ObservationModel.timestamp.asc()).all()

    if not observations:
        return pd.DataFrame()

    data = [
        {
            "id": o.id,
            "dataset_id": o.dataset_id,
            "symbol": o.symbol,
            "expiry_date": o.expiry_date,
            "timestamp": o.timestamp,
            "open_price": o.open_price,
            "high_price": o.high_price,
            "low_price": o.low_price,
            "close_price": o.close_price,
            "volume": o.volume,
            "open_interest": o.open_interest,
            "quotation_basis": o.quotation_basis,
            "purity": o.purity,
            "normalized": o.normalized_price_pure_gram,
            "normalized_price_pure_gram": o.normalized_price_pure_gram
        }
        for o in observations
    ]
    return pd.DataFrame(data)

def list_datasets(db: Session) -> List[Dict[str, Any]]:
    datasets = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "source_type": d.source_type,
            "file_hash": d.file_hash,
            "row_count": d.row_count,
            "start_date": d.start_date,
            "end_date": d.end_date,
            "instruments": d.instruments,
            "is_active": d.is_active,
            "validation_status": d.validation_status,
            "created_at": d.created_at.isoformat()
        }
        for d in datasets
    ]
