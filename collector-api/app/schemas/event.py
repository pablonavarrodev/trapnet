from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AttackEvent(BaseModel):
    event_source: str = "cowrie"
    event_type: str
    source_ip: str
    timestamp: datetime
    session_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    success: bool = False
    command: Optional[str] = None
    duration: Optional[str] = None
    raw_event: Optional[dict[str, Any]] = None


class AttackEventResponse(BaseModel):
    id: int
    event_source: str
    event_type: str
    source_ip: str
    timestamp: datetime
    session_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    success: bool
    command: Optional[str] = None
    duration: Optional[str] = None
    raw_event: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class EventIngestResponse(BaseModel):
    received: bool
    event_id: int


class SourceIpStatsResponse(BaseModel):
    source_ip: str
    total_events: int