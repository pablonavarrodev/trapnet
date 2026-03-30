from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_api_key
from app.schemas.event import (
    AttackEvent,
    AttackEventResponse,
    EventIngestResponse,
)
from app.services.event_service import create_event as create_event_service
from app.services.event_service import get_filtered_events

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventIngestResponse,
    dependencies=[Depends(require_api_key)],
)
def create_event(event: AttackEvent, db: Session = Depends(get_db)):
    db_event = create_event_service(db, event)

    print(
        f"[collector] stored source={event.event_source} "
        f"type={event.event_type} ip={event.source_ip} "
        f"session={event.session_id}"
    )

    return {"received": True, "event_id": db_event.id}


@router.get("/events", response_model=list[AttackEventResponse])
def list_events(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    source_ip: str | None = None,
    session_id: str | None = None,
    event_type: str | None = None,
    command_contains: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    exclude_internal: bool = Query(default=False),  # 👈 AÑADIDO
    db: Session = Depends(get_db),
):
    return get_filtered_events(
        db,
        limit=limit,
        offset=offset,
        source_ip=source_ip,
        session_id=session_id,
        event_type=event_type,
        command_contains=command_contains,
        from_ts=from_ts,
        to_ts=to_ts,
        exclude_internal=exclude_internal,  # 👈 AÑADIDO
    )


@router.get("/events/recent", response_model=list[AttackEventResponse])
def recent_events(
    limit: int = Query(default=50, ge=1, le=200),
    exclude_internal: bool = Query(default=False),  # 👈 AÑADIDO
    db: Session = Depends(get_db),
):
    return get_filtered_events(
        db,
        limit=limit,
        offset=0,
        exclude_internal=exclude_internal,  # 👈 AÑADIDO
    )


@router.get("/sessions/{session_id}", response_model=list[AttackEventResponse])
def get_session_events(
    session_id: str,
    exclude_internal: bool = Query(default=False),  # 👈 OPCIONAL pero útil
    db: Session = Depends(get_db),
):
    return get_filtered_events(
        db,
        limit=1000,
        offset=0,
        session_id=session_id,
        exclude_internal=exclude_internal,  # 👈 AÑADIDO
    )