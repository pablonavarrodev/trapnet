import os

COLLECTOR_API_URL = os.getenv("COLLECTOR_API_URL", "http://collector-api:8000")
COWRIE_LOG_PATH = os.getenv(
    "COWRIE_LOG_PATH",
    "/cowrie/var/log/cowrie/cowrie.json"
)
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "1"))