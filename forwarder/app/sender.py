import requests

from app.config import COLLECTOR_API_URL, load_collector_api_key

COLLECTOR_API_KEY = load_collector_api_key()
HTTP_SESSION = requests.Session()


def send_event(event: dict) -> tuple[bool, str | None]:
    try:
        response = HTTP_SESSION.post(
            f"{COLLECTOR_API_URL}/events",
            json=event,
            headers={
                "X-API-Key": COLLECTOR_API_KEY,
            },
            timeout=5,
        )
        response.raise_for_status()
        return True, None

    except requests.RequestException as exc:
        return False, str(exc)