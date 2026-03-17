import requests

from app.config import COLLECTOR_API_URL


def send_event(event: dict) -> None:
    response = requests.post(
        f"{COLLECTOR_API_URL}/events",
        json=event,
        timeout=5,
    )
    response.raise_for_status()