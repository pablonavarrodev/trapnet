from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import AttackEventModel

router = APIRouter(tags=["stats"])


@router.get("/stats/source-ip")
def stats_by_source_ip(db: Session = Depends(get_db)):
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