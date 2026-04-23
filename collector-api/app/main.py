import logging
import time

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.routes import events, health, stats
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.event import AttackEventModel  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [collector] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

app.include_router(health.router)
app.include_router(events.router)
app.include_router(stats.router)


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

            logger.info("database connection established")
            return
        except OperationalError as exc:
            logger.warning(
                "database not ready yet (attempt %s/%s): %s",
                attempt,
                max_retries,
                exc,
            )
            time.sleep(retry_delay)

    raise RuntimeError("[collector] could not connect to database after several retries")