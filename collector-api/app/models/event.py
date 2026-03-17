from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db import Base


class AttackEventModel(Base):
    __tablename__ = "attack_events"

    id = Column(Integer, primary_key=True, index=True)
    event_source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    source_ip = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    session_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    command = Column(Text, nullable=True)
    duration = Column(String, nullable=True)
    raw_event = Column(JSONB, nullable=True)