from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import AttackEventModel
from app.schemas.event import (
    EventTypeStatsResponse,
    SessionStatsResponse,
    SourceIpStatsResponse,
)

router = APIRouter(tags=["stats"])


@router.get("/stats/source-ip", response_model=list[SourceIpStatsResponse])
def stats_by_source_ip(db: Session = Depends(get_db)):
    results = (
        db.query(
            AttackEventModel.source_ip,
            func.count(AttackEventModel.id).label("total_events"),
        )
        .group_by(AttackEventModel.source_ip)
        .order_by(func.count(AttackEventModel.id).desc())
        .all()
    )

    return [
        {"source_ip": source_ip, "total_events": total_events}
        for source_ip, total_events in results
    ]


@router.get("/stats/event-types", response_model=list[EventTypeStatsResponse])
def stats_by_event_type(db: Session = Depends(get_db)):
    results = (
        db.query(
            AttackEventModel.event_type,
            func.count(AttackEventModel.id).label("total_events"),
        )
        .group_by(AttackEventModel.event_type)
        .order_by(func.count(AttackEventModel.id).desc())
        .all()
    )

    return [
        {"event_type": event_type, "total_events": total_events}
        for event_type, total_events in results
    ]


@router.get("/stats/recent-sessions", response_model=list[SessionStatsResponse])
def stats_recent_sessions(db: Session = Depends(get_db)):
    results = (
        db.query(
            AttackEventModel.session_id,
            AttackEventModel.source_ip,
            func.count(AttackEventModel.id).label("total_events"),
            func.min(AttackEventModel.timestamp).label("first_seen"),
            func.max(AttackEventModel.timestamp).label("last_seen"),
        )
        .group_by(AttackEventModel.session_id, AttackEventModel.source_ip)
        .order_by(func.max(AttackEventModel.timestamp).desc())
        .limit(50)
        .all()
    )

    return [
        {
            "session_id": session_id,
            "source_ip": source_ip,
            "total_events": total_events,
            "first_seen": first_seen,
            "last_seen": last_seen,
        }
        for session_id, source_ip, total_events, first_seen, last_seen in results
    ]