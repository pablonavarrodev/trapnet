from fastapi import FastAPI
from sqlalchemy import text

from app.db import Base, engine, SessionLocal
from app.models.event import AttackEventModel
from app.schemas.event import AttackEvent

app = FastAPI(title="trapnet collector")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("[collector] database connection established")
    finally:
        db.close()


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        total_events = db.query(AttackEventModel).count()
        return {"status": "ok", "total_events": total_events}
    finally:
        db.close()


@app.post("/events")
def create_event(event: AttackEvent):
    db = SessionLocal()
    try:
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
            f"[collector] stored source={event.event_source} type={event.event_type} ip={event.source_ip} session={event.session_id}"
        )

        return {"received": True, "event_id": db_event.id}
    finally:
        db.close()


@app.get("/events")
def list_events():
    db = SessionLocal()
    try:
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
    finally:
        db.close()