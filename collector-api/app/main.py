from fastapi import FastAPI
from app.schemas.event import AttackEvent

app = FastAPI(title="trapr collector")

EVENTS: list[AttackEvent] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/events")
def create_event(event: AttackEvent):
    EVENTS.append(event)
    return {"received": True, "total_events": len(EVENTS)}


@app.get("/events")
def list_events():
    return EVENTS