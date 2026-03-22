import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import FORWARDER_DB_PATH


def _ensure_db_parent_exists() -> None:
    db_path = Path(FORWARDER_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_db_parent_exists()

    connection = sqlite3.connect(FORWARDER_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    return connection


def init_storage() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS queued_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_uid TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_attempt_at TEXT,
                sent_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_queued_events_status_id
            ON queued_events(status, id);

            CREATE TABLE IF NOT EXISTS state_store (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()


def enqueue_event(event_uid: str, payload: dict[str, Any]) -> bool:
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO queued_events (
                event_uid,
                payload_json,
                status
            )
            VALUES (?, ?, 'pending')
            """,
            (event_uid, payload_json),
        )
        connection.commit()
        return cursor.rowcount == 1


def get_pending_events(limit: int) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, event_uid, payload_json, attempts
            FROM queued_events
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    result: list[dict[str, Any]] = []

    for row in rows:
        result.append(
            {
                "id": row["id"],
                "event_uid": row["event_uid"],
                "payload": json.loads(row["payload_json"]),
                "attempts": row["attempts"],
            }
        )

    return result


def mark_sent(queue_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE queued_events
            SET status = 'sent',
                sent_at = CURRENT_TIMESTAMP,
                last_error = NULL
            WHERE id = ?
            """,
            (queue_id,),
        )
        connection.commit()


def mark_failed(queue_id: int, error_message: str) -> None:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE queued_events
            SET attempts = attempts + 1,
                last_error = ?,
                last_attempt_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (error_message, queue_id),
        )
        connection.commit()


def count_pending_events() -> int:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM queued_events
            WHERE status = 'pending'
            """
        ).fetchone()

    return int(row["total"])


def set_state(state_key: str, value: dict[str, Any]) -> None:
    state_value = json.dumps(value, ensure_ascii=False, sort_keys=True)

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO state_store (state_key, state_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(state_key) DO UPDATE SET
                state_value = excluded.state_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (state_key, state_value),
        )
        connection.commit()


def get_state(state_key: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT state_value
            FROM state_store
            WHERE state_key = ?
            """,
            (state_key,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["state_value"])


def build_file_state_key(filepath: str) -> str:
    return f"log_state::{filepath}"


def save_file_state(filepath: str, inode: int, offset: int) -> None:
    set_state(
        build_file_state_key(filepath),
        {
            "inode": inode,
            "offset": offset,
        },
    )


def load_file_state(filepath: str) -> dict[str, Any] | None:
    return get_state(build_file_state_key(filepath))