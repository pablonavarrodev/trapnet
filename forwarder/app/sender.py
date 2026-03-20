import requests

from app.config import COLLECTOR_API_URL, load_collector_api_key

COLLECTOR_API_KEY = load_collector_api_key()


def send_event(event: dict) -> None:
    response = requests.post(
        f"{COLLECTOR_API_URL}/events",
        json=event,
        headers={
            "X-API-Key": COLLECTOR_API_KEY,
        },
        timeout=5,
    )
    response.raise_for_status()