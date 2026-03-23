from collections.abc import Generator

from fastapi import Header
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    verify_api_key(x_api_key)