from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import AttackEventModel

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    total_events = db.query(AttackEventModel).count()
    return {"status": "ok", "total_events": total_events}