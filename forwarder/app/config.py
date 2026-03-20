import os
from pathlib import Path

COLLECTOR_API_URL = os.getenv("COLLECTOR_API_URL", "http://collector-api:8000")
COWRIE_LOG_PATH = os.getenv(
    "COWRIE_LOG_PATH",
    "/cowrie/var/log/cowrie/cowrie.json"
)
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "1"))

COLLECTOR_API_KEY_FILE = os.getenv(
    "COLLECTOR_API_KEY_FILE",
    "/run/secrets/collector_api_key"
)


def load_collector_api_key() -> str:
    path = Path(COLLECTOR_API_KEY_FILE)

    if not path.exists():
        raise RuntimeError(
            f"[forwarder] secret file not found: {COLLECTOR_API_KEY_FILE}"
        )

    value = path.read_text(encoding="utf-8").strip()

    if not value:
        raise RuntimeError("[forwarder] collector api key is empty")

    return value