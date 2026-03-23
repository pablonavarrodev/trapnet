from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_api_key
from app.models.event import AttackEventModel
from app.schemas.event import AttackEvent

router = APIRouter(tags=["events"])


@router.post("/events", dependencies=[Depends(require_api_key)])
def create_event(event: AttackEvent, db: Session = Depends(get_db)):
    db_event = AttackEventModel(
        event_source=event.event_source,
        event_type=event.event_type,
        source_ip=event.source_ip,
        timestamp=event.timestamp,
        session_id=event.session_id,
        username=event.username,
        password=event.password,
        success=event.success,
        command=event.command,
        duration=event.duration,
        raw_event=event.raw_event,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    print(
        f"[collector] stored source={event.event_source} "
        f"type={event.event_type} ip={event.source_ip} "
        f"session={event.session_id}"
    )

    return {"received": True, "event_id": db_event.id}


@router.get("/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(AttackEventModel).order_by(AttackEventModel.id.asc()).all()

    return [
        {
            "id": event.id,
            "event_source": event.event_source,
            "event_type": event.event_type,
            "source_ip": event.source_ip,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "username": event.username,
            "password": event.password,
            "success": event.success,
            "command": event.command,
            "duration": event.duration,
            "raw_event": event.raw_event,
        }
        for event in events
    ]


@router.get("/sessions/{session_id}")
def get_session_events(session_id: str, db: Session = Depends(get_db)):
    events = (
        db.query(AttackEventModel)
        .filter(AttackEventModel.session_id == session_id)
        .order_by(AttackEventModel.id.asc())
        .all()
    )

    return [
        {
            "id": event.id,
            "event_source": event.event_source,
            "event_type": event.event_type,
            "source_ip": event.source_ip,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "username": event.username,
            "password": event.password,
            "success": event.success,
            "command": event.command,
            "duration": event.duration,
            "raw_event": event.raw_event,
        }
        for event in events
    ]