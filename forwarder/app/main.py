import hashlib
import json
import logging
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [forwarder] %(message)s",
)
logger = logging.getLogger(__name__)

processed = 0
ignored = 0
failed = 0
queued = 0
duplicates = 0

SUMMARY_EVERY_SECONDS = 60
_last_summary_at = 0.0


def log_periodic_summary(force: bool = False) -> None:
    global _last_summary_at

    now = time.time()

    if not force and (now - _last_summary_at) < SUMMARY_EVERY_SECONDS:
        return

    _last_summary_at = now
    pending = count_pending_events()

    logger.info(
        "summary processed=%s queued=%s ignored=%s duplicates=%s failed=%s pending=%s",
        processed,
        queued,
        ignored,
        duplicates,
        failed,
        pending,
    )


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
        logger.warning("invalid json line: %s", exc)
        return None

    parsed_event = parse_cowrie_event(raw_event)

    if parsed_event is None:
        ignored += 1
        return None

    return parsed_event


def enqueue_line(line: str, source_label: str) -> None:
    global queued, duplicates

    parsed_event = parse_line_to_event(line)

    if parsed_event is None:
        log_periodic_summary()
        return

    event_uid = build_event_uid(parsed_event)
    inserted = enqueue_event(event_uid, parsed_event)

    if inserted:
        queued += 1
    else:
        duplicates += 1

    log_periodic_summary()


def drain_queue_once() -> None:
    global processed, failed

    pending_items = get_pending_events(FORWARDER_SEND_BATCH_SIZE)

    if not pending_items:
        return

    batch_sent = 0
    batch_failed = 0

    for item in pending_items:
        success, error_message = send_event(item["payload"])

        if success:
            mark_sent(item["id"])
            processed += 1
            batch_sent += 1
            continue

        failed += 1
        batch_failed += 1
        safe_error = (error_message or "unknown error")[:FORWARDER_MAX_ERROR_LENGTH]
        mark_failed(item["id"], safe_error)

    if batch_failed > 0:
        logger.warning(
            "queue batch processed with failures sent=%s failed=%s pending=%s",
            batch_sent,
            batch_failed,
            count_pending_events(),
        )
    elif batch_sent > 0:
        logger.info(
            "queue batch sent=%s pending=%s",
            batch_sent,
            count_pending_events(),
        )

    log_periodic_summary()


def wait_for_log_file(filepath: str) -> Path:
    path = Path(filepath)

    while not path.exists():
        logger.info("waiting for cowrie log file: %s", filepath)
        time.sleep(POLL_INTERVAL_SECONDS)

    return path


def backfill_file(filepath: str) -> None:
    path = wait_for_log_file(filepath)
    logger.info("starting backfill from beginning: %s", filepath)

    with path.open("r", encoding="utf-8") as file:
        while True:
            line = file.readline()

            if not line:
                break

            enqueue_line(line, source_label="backfill")

        current_offset = file.tell()

    current_stat = path.stat()
    save_file_state(filepath, inode=current_stat.st_ino, offset=current_offset)

    logger.info(
        "backfill finished pending=%s offset=%s",
        count_pending_events(),
        current_offset,
    )
    log_periodic_summary(force=True)


def drain_until_queue_empty() -> None:
    while True:
        pending = count_pending_events()

        if pending == 0:
            logger.info("queue drained completely")
            return

        logger.info("draining queue pending=%s", pending)
        drain_queue_once()
        time.sleep(1)


def resolve_initial_offset(path: Path, filepath: str) -> tuple[int, int]:
    file_stat = path.stat()
    saved_state = load_file_state(filepath)

    if saved_state is not None:
        saved_inode = int(saved_state.get("inode", -1))
        saved_offset = int(saved_state.get("offset", 0))

        if saved_inode == file_stat.st_ino and saved_offset <= file_stat.st_size:
            logger.info(
                "resuming from saved offset=%s inode=%s",
                saved_offset,
                saved_inode,
            )
            return saved_inode, saved_offset

        logger.warning(
            "saved state is stale saved_inode=%s current_inode=%s saved_offset=%s current_size=%s",
            saved_inode,
            file_stat.st_ino,
            saved_offset,
            file_stat.st_size,
        )

    if FORWARDER_START_POSITION == "beginning":
        logger.info("no valid saved state, starting from beginning")
        return file_stat.st_ino, 0

    logger.info("no valid saved state, starting from end")
    return file_stat.st_ino, file_stat.st_size


def tail_file_forever(filepath: str) -> None:
    path = wait_for_log_file(filepath)
    inode, offset = resolve_initial_offset(path, filepath)

    logger.info("reading cowrie log file in live mode: %s", filepath)

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
            log_periodic_summary()
            time.sleep(POLL_INTERVAL_SECONDS)

            if not path.exists():
                logger.warning("log file disappeared, waiting for it again...")
                path = wait_for_log_file(filepath)

            current_stat = path.stat()

            if current_stat.st_ino != inode or current_stat.st_size < offset:
                logger.warning(
                    "detected log rotation/truncation, reopening old_inode=%s new_inode=%s old_offset=%s new_size=%s",
                    inode,
                    current_stat.st_ino,
                    offset,
                    current_stat.st_size,
                )
                inode = current_stat.st_ino
                offset = 0
                save_file_state(filepath, inode=inode, offset=offset)
                file.close()
                file = path.open("r", encoding="utf-8")
                file.seek(0)


def main() -> None:
    logger.info("starting cowrie forwarder run_mode=%s", FORWARDER_RUN_MODE)
    init_storage()

    if FORWARDER_RUN_MODE == "backfill_once":
        backfill_file(COWRIE_LOG_PATH)
        drain_until_queue_empty()
        logger.info("backfill mode completed successfully")
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