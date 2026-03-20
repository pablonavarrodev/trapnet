import os
import secrets
import time

from fastapi import FastAPI, Header, HTTPException
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError

from app.db import Base, SessionLocal, engine
from app.models.event import AttackEventModel
from app.schemas.event import AttackEvent

app = FastAPI(title="trapnet collector")


def load_collector_api_key() -> str:
    secret_path = os.getenv(
        "COLLECTOR_API_KEY_FILE",
        "/run/secrets/collector_api_key"
    )

    try:
        with open(secret_path, "r", encoding="utf-8") as file:
            value = file.read().strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"[collector] secret file not found: {secret_path}"
        ) from exc

    if not value:
        raise RuntimeError("[collector] collector api key is empty")

    return value


COLLECTOR_API_KEY = load_collector_api_key()


def verify_api_key(x_api_key: str | None) -> None:
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="missing api key")

    if not secrets.compare_digest(x_api_key, COLLECTOR_API_KEY):
        raise HTTPException(status_code=401, detail="invalid api key")


@app.on_event("startup")
def on_startup():
    max_retries = 15
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)

            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()

            print("[collector] database connection established")
            return

        except OperationalError as exc:
            print(
                f"[collector] database not ready yet "
                f"(attempt {attempt}/{max_retries}): {exc}"
            )
            time.sleep(retry_delay)

    raise RuntimeError("[collector] could not connect to database after several retries")


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        total_events = db.query(AttackEventModel).count()
        return {"status": "ok", "total_events": total_events}
    finally:
        db.close()


@app.post("/events")
def create_event(event: AttackEvent, x_api_key: str | None = Header(default=None)):
    verify_api_key(x_api_key)

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
            f"[collector] stored source={event.event_source} "
            f"type={event.event_type} ip={event.source_ip} "
            f"session={event.session_id}"
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


@app.get("/sessions/{session_id}")
def get_session_events(session_id: str):
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.get("/stats/source-ip")
def stats_by_source_ip():
    db = SessionLocal()
    try:
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
            {
                "source_ip": source_ip,
                "total_events": total_events,
            }
            for source_ip, total_events in results
        ]
    finally:
        db.close()