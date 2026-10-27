import json
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import AuditEventModel

def log_audit_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: Optional[str],
    summary: str,
    details: Optional[Dict[str, Any]] = None
) -> AuditEventModel:
    """
    Appends an immutable audit event record to the database.
    """
    event = AuditEventModel(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        details_json=json.dumps(details or {}, default=str),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def list_audit_events(
    db: Session,
    limit: int = 50,
    event_type: Optional[str] = None
) -> list:
    query = db.query(AuditEventModel)
    if event_type:
        query = query.filter(AuditEventModel.event_type == event_type)
    events = query.order_by(AuditEventModel.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "summary": e.summary,
            "details": json.loads(e.details_json or "{}"),
            "timestamp": e.timestamp.isoformat()
        }
        for e in events
    ]
