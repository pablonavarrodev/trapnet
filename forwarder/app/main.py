import hashlib
import json
import time
from pathlib import Path

from app.config import (
    COWRIE_LOG_PATH,
    FORWARDER_BACKFILL_ON_STARTUP,
    FORWARDER_MAX_ERROR_LENGTH,
    FORWARDER_RUN_MODE,
    FORWARDER_SEND_BATCH_SIZE,
    FORWARDER_START_POSITION,
    POLL_INTERVAL_SECONDS,
)
from app.parser import parse_cowrie_event
from app.sender import send_event
from app.store import (
    count_pending_events,
    enqueue_event,
    get_pending_events,
    init_storage,
    load_file_state,
    mark_failed,
    mark_sent,
    save_file_state,
)


processed = 0
ignored = 0
failed = 0
queued = 0
duplicates = 0


def build_event_uid(event: dict) -> str:
    canonical = json.dumps(
        event,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_line_to_event(line: str) -> dict | None:
    global ignored, failed

    try:
        raw_event = json.loads(line)
    except json.JSONDecodeError as exc:
        failed += 1
        print(f"[forwarder] invalid json line: {exc}")
        return None

    parsed_event = parse_cowrie_event(raw_event)

    if parsed_event is None:
        ignored += 1
        eventid = raw_event.get("eventid", "unknown")
        print(f"[forwarder] ignored event: {eventid} | ignored={ignored}")
        return None

    return parsed_event


def enqueue_line(line: str, source_label: str) -> None:
    global queued, duplicates

    parsed_event = parse_line_to_event(line)

    if parsed_event is None:
        return

    event_uid = build_event_uid(parsed_event)
    inserted = enqueue_event(event_uid, parsed_event)

    if inserted:
        queued += 1
        print(
            f"[forwarder] queued event from {source_label} "
            f"type={parsed_event['event_type']} "
            f"session={parsed_event['session_id']} "
            f"| queued={queued}"
        )
    else:
        duplicates += 1
        print(
            f"[forwarder] duplicate event skipped from {source_label} "
            f"event_uid={event_uid[:12]}... "
            f"| duplicates={duplicates}"
        )


def drain_queue_once() -> None:
    global processed, failed

    pending_items = get_pending_events(FORWARDER_SEND_BATCH_SIZE)

    if not pending_items:
        return

    for item in pending_items:
        success, error_message = send_event(item["payload"])

        if success:
            mark_sent(item["id"])
            processed += 1
            print(
                f"[forwarder] sent queued event "
                f"id={item['id']} "
                f"event_uid={item['event_uid'][:12]}... "
                f"| processed={processed}"
            )
            continue

        failed += 1
        safe_error = (error_message or "unknown error")[:FORWARDER_MAX_ERROR_LENGTH]
        mark_failed(item["id"], safe_error)
        print(
            f"[forwarder] failed to send queued event "
            f"id={item['id']} "
            f"attempts={item['attempts'] + 1} "
            f"error={safe_error} "
            f"| failed={failed}"
        )


def wait_for_log_file(filepath: str) -> Path:
    path = Path(filepath)

    while not path.exists():
        print(f"[forwarder] waiting for cowrie log file: {filepath}")
        time.sleep(POLL_INTERVAL_SECONDS)

    return path


def backfill_file(filepath: str) -> None:
    path = wait_for_log_file(filepath)
    print(f"[forwarder] starting backfill from beginning: {filepath}")

    with path.open("r", encoding="utf-8") as file:
        while True:
            line = file.readline()

            if not line:
                break

            enqueue_line(line, source_label="backfill")

        current_offset = file.tell()

    current_stat = path.stat()
    save_file_state(filepath, inode=current_stat.st_ino, offset=current_offset)

    print(
        f"[forwarder] backfill finished | pending={count_pending_events()} "
        f"offset={current_offset}"
    )


def drain_until_queue_empty() -> None:
    while True:
        pending = count_pending_events()

        if pending == 0:
            print("[forwarder] queue drained completely")
            return

        print(f"[forwarder] draining queue | pending={pending}")
        drain_queue_once()
        time.sleep(1)


def resolve_initial_offset(path: Path, filepath: str) -> tuple[int, int]:
    file_stat = path.stat()
    saved_state = load_file_state(filepath)

    if saved_state is not None:
        saved_inode = int(saved_state.get("inode", -1))
        saved_offset = int(saved_state.get("offset", 0))

        if saved_inode == file_stat.st_ino and saved_offset <= file_stat.st_size:
            print(
                f"[forwarder] resuming from saved offset={saved_offset} "
                f"inode={saved_inode}"
            )
            return saved_inode, saved_offset

        print(
            "[forwarder] saved state is stale "
            f"(saved_inode={saved_inode}, current_inode={file_stat.st_ino}, "
            f"saved_offset={saved_offset}, current_size={file_stat.st_size})"
        )

    if FORWARDER_START_POSITION == "beginning":
        print("[forwarder] no valid saved state, starting from beginning")
        return file_stat.st_ino, 0

    print("[forwarder] no valid saved state, starting from end")
    return file_stat.st_ino, file_stat.st_size


def tail_file_forever(filepath: str) -> None:
    path = wait_for_log_file(filepath)
    inode, offset = resolve_initial_offset(path, filepath)

    print(f"[forwarder] reading cowrie log file in live mode: {filepath}")

    with path.open("r", encoding="utf-8") as file:
        file.seek(offset)

        while True:
            line = file.readline()

            if line:
                offset = file.tell()
                enqueue_line(line, source_label="live")
                save_file_state(filepath, inode=inode, offset=offset)
                drain_queue_once()
                continue

            drain_queue_once()
            time.sleep(POLL_INTERVAL_SECONDS)

            if not path.exists():
                print("[forwarder] log file disappeared, waiting for it again...")
                path = wait_for_log_file(filepath)

            current_stat = path.stat()

            if current_stat.st_ino != inode or current_stat.st_size < offset:
                print(
                    "[forwarder] detected log rotation/truncation, reopening "
                    f"(old_inode={inode}, new_inode={current_stat.st_ino}, "
                    f"old_offset={offset}, new_size={current_stat.st_size})"
                )
                inode = current_stat.st_ino
                offset = 0
                save_file_state(filepath, inode=inode, offset=offset)
                file.close()
                file = path.open("r", encoding="utf-8")
                file.seek(0)


def main() -> None:
    print("[forwarder] starting cowrie forwarder...")
    init_storage()

    if FORWARDER_RUN_MODE == "backfill_once":
        backfill_file(COWRIE_LOG_PATH)
        drain_until_queue_empty()
        print("[forwarder] backfill mode completed successfully")
        return

    if FORWARDER_RUN_MODE != "live":
        raise RuntimeError(
            f"[forwarder] invalid FORWARDER_RUN_MODE={FORWARDER_RUN_MODE}"
        )

    if FORWARDER_BACKFILL_ON_STARTUP:
        backfill_file(COWRIE_LOG_PATH)

    tail_file_forever(COWRIE_LOG_PATH)


if __name__ == "__main__":
    main()