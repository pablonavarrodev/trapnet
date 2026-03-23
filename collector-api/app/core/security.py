import secrets

from fastapi import HTTPException

from app.core.config import settings


def load_collector_api_key() -> str:
    try:
        with open(settings.COLLECTOR_API_KEY_FILE, "r", encoding="utf-8") as file:
            value = file.read().strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"[collector] secret file not found: {settings.COLLECTOR_API_KEY_FILE}"
        ) from exc

    if not value:
        raise RuntimeError("[collector] collector api key is empty")

    return value


COLLECTOR_API_KEY = load_collector_api_key()


def verify_api_key(x_api_key: str | None) -> None:
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="missing api key")

    if not secrets.compare_digest(x_api_key, COLLECTOR_API_KEY):
        raise HTTPException(status_code=401, detail="invalid api key")