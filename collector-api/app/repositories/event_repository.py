from datetime import datetime

from sqlalchemy.orm import Session

from app.models.event import AttackEventModel


def list_events(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    source_ip: str | None = None,
    session_id: str | None = None,
    event_type: str | None = None,
    command_contains: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    exclude_internal: bool = False,
):
    query = db.query(AttackEventModel)

    if source_ip:
        query = query.filter(AttackEventModel.source_ip == source_ip)

    if session_id:
        query = query.filter(AttackEventModel.session_id == session_id)

    if event_type:
        query = query.filter(AttackEventModel.event_type == event_type)

    if command_contains:
        query = query.filter(AttackEventModel.command.ilike(f"%{command_contains}%"))

    if from_ts:
        query = query.filter(AttackEventModel.timestamp >= from_ts)

    if to_ts:
        query = query.filter(AttackEventModel.timestamp <= to_ts)

    if exclude_internal:
        query = query.filter(AttackEventModel.source_ip != "127.0.0.1")

    return (
        query.order_by(AttackEventModel.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )