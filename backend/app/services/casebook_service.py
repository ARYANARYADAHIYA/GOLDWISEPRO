import json
import uuid
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import PaperResearchRecord
from app.services.audit_service import log_audit_event

def create_paper_research_record(
    db: Session,
    data: Dict[str, Any]
) -> PaperResearchRecord:
    record_id = f"case-{uuid.uuid4().hex[:8]}"
    record = PaperResearchRecord(
        id=record_id,
        candidate_id=data.get("candidate_id"),
        symbol_pair=data["symbol_pair"],
        observation_date=data["observation_date"],
        initial_verdict=data["initial_verdict"],
        initial_score=data.get("initial_score"),
        spread_bps=data["spread_bps"],
        rationale=data["rationale"],
        expected_horizon_days=data.get("expected_horizon_days", 5),
        entry_price_spread=data["entry_price_spread"],
        exit_observed_spread=None,
        cost_assumptions_json=json.dumps(data.get("cost_assumptions", {})),
        status="PROSPECTIVE",
        notes=data.get("notes", ""),
        tags=data.get("tags", "relative_value"),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_audit_event(
        db,
        event_type="CASEBOOK_CREATED",
        entity_type="PaperResearchRecord",
        entity_id=record_id,
        summary=f"Created prospective research casebook entry for {record.symbol_pair} on {record.observation_date}",
        details={"rationale": record.rationale, "spread_bps": record.spread_bps}
    )
    return record

def update_paper_research_record(
    db: Session,
    record_id: str,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    exit_observed_spread: Optional[float] = None
) -> Optional[PaperResearchRecord]:
    record = db.query(PaperResearchRecord).filter(PaperResearchRecord.id == record_id).first()
    if not record:
        return None

    if status:
        record.status = status
    if notes is not None:
        record.notes = notes
    if exit_observed_spread is not None:
        record.exit_observed_spread = exit_observed_spread
    record.updated_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(record)

    log_audit_event(
        db,
        event_type="CASEBOOK_UPDATED",
        entity_type="PaperResearchRecord",
        entity_id=record_id,
        summary=f"Updated research case {record_id} to status '{record.status}'",
        details={"status": record.status, "exit_observed_spread": exit_observed_spread}
    )
    return record

def list_paper_research_records(
    db: Session,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = db.query(PaperResearchRecord)
    if status:
        query = query.filter(PaperResearchRecord.status == status)
    records = query.order_by(PaperResearchRecord.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "candidate_id": r.candidate_id,
            "symbol_pair": r.symbol_pair,
            "observation_date": r.observation_date,
            "initial_verdict": r.initial_verdict,
            "initial_score": r.initial_score,
            "spread_bps": r.spread_bps,
            "rationale": r.rationale,
            "expected_horizon_days": r.expected_horizon_days,
            "entry_price_spread": r.entry_price_spread,
            "exit_observed_spread": r.exit_observed_spread,
            "cost_assumptions": json.loads(r.cost_assumptions_json or "{}"),
            "status": r.status,
            "notes": r.notes,
            "tags": r.tags,
            "updated_at": r.updated_at.isoformat(),
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]
