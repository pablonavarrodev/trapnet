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