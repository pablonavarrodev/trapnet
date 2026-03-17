import json
import time
from pathlib import Path

from app.config import COWRIE_LOG_PATH, POLL_INTERVAL_SECONDS
from app.parser import parse_cowrie_event
from app.sender import send_event

processed = 0
ignored = 0
failed = 0


def process_line(line: str) -> None:
    global processed, ignored, failed

    try:
        raw_event = json.loads(line)
    except json.JSONDecodeError as exc:
        failed += 1
        print(f"[forwarder] invalid json line: {exc}")
        return

    parsed_event = parse_cowrie_event(raw_event)

    if parsed_event is None:
        ignored += 1
        eventid = raw_event.get("eventid", "unknown")
        print(f"[forwarder] ignored event: {eventid} | ignored={ignored}")
        return

    try:
        send_event(parsed_event)
        processed += 1
        print(
            f"[forwarder] sent event type={parsed_event['event_type']} session={parsed_event['session_id']} | processed={processed}"
        )
    except Exception as exc:
        failed += 1
        print(f"[forwarder] failed to send event: {exc} | failed={failed}")


def tail_file_forever(filepath: str) -> None:
    path = Path(filepath)

    while not path.exists():
        print(f"[forwarder] waiting for cowrie log file: {filepath}")
        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"[forwarder] reading cowrie log file: {filepath}")

    with path.open("r", encoding="utf-8") as file:
        file.seek(0, 2)

        while True:
            line = file.readline()

            if not line:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            process_line(line)


def main() -> None:
    print("[forwarder] starting cowrie forwarder...")
    tail_file_forever(COWRIE_LOG_PATH)


if __name__ == "__main__":
    main()