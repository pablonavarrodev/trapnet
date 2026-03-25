from sqlalchemy.orm import Session

from app.models.event import AttackEventModel
from app.repositories.event_repository import list_events as repo_list_events
from app.schemas.event import AttackEvent


def create_event(db: Session, event: AttackEvent) -> AttackEventModel:
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
    return db_event


def get_filtered_events(db: Session, **filters):
    return repo_list_events(db, **filters)