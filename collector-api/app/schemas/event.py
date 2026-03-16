from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AttackEvent(BaseModel):
    event_type: str
    source_ip: str
    timestamp: datetime
    session_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    success: bool = False