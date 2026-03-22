import os
from pathlib import Path


def get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


COLLECTOR_API_URL = os.getenv("COLLECTOR_API_URL", "http://collector-api:8000")

COWRIE_LOG_PATH = os.getenv(
    "COWRIE_LOG_PATH",
    "/cowrie/var/log/cowrie/cowrie.json",
)

POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "1"))

COLLECTOR_API_KEY_FILE = os.getenv(
    "COLLECTOR_API_KEY_FILE",
    "/run/secrets/collector_api_key",
)

FORWARDER_DB_PATH = os.getenv(
    "FORWARDER_DB_PATH",
    "/data/forwarder.db",
)

FORWARDER_RUN_MODE = os.getenv(
    "FORWARDER_RUN_MODE",
    "live",
).strip().lower()

FORWARDER_START_POSITION = os.getenv(
    "FORWARDER_START_POSITION",
    "end",
).strip().lower()

FORWARDER_BACKFILL_ON_STARTUP = get_bool_env(
    "FORWARDER_BACKFILL_ON_STARTUP",
    False,
)

FORWARDER_SEND_BATCH_SIZE = int(
    os.getenv("FORWARDER_SEND_BATCH_SIZE", "50")
)

FORWARDER_MAX_ERROR_LENGTH = int(
    os.getenv("FORWARDER_MAX_ERROR_LENGTH", "500")
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