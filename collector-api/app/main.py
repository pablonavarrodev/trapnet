from fastapi import FastAPI

from app.schemas.event import AttackEvent

app = FastAPI(title="trapnet collector")

EVENTS: list[AttackEvent] = []


@app.get("/health")
def health():
    return {"status": "ok", "total_events": len(EVENTS)}


@app.post("/events")
def create_event(event: AttackEvent):
    EVENTS.append(event)
    print(
        f"[collector] received source={event.event_source} type={event.event_type} ip={event.source_ip} session={event.session_id}"
    )
    return {"received": True, "total_events": len(EVENTS)}


@app.get("/events")
def list_events():
    return EVENTS