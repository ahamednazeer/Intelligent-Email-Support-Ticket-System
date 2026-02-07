from __future__ import annotations

from typing import Optional

from app.db import get_conn
from app.utils.time import utc_now_iso


def is_duplicate(
    source: str,
    message_id: Optional[str],
    uid: Optional[str],
    fingerprint: Optional[str],
) -> bool:
    conditions = []
    params: list[str] = [source]
    if message_id:
        conditions.append("message_id = ?")
        params.append(message_id)
    if uid:
        conditions.append("uid = ?")
        params.append(uid)
    if fingerprint:
        conditions.append("fingerprint = ?")
        params.append(fingerprint)

    if not conditions:
        return False

    query = "SELECT 1 FROM ingested_messages WHERE source = ? AND (" + " OR ".join(conditions) + ") LIMIT 1"
    with get_conn() as conn:
        row = conn.execute(query, params).fetchone()
    return row is not None


def record_message(
    source: str,
    message_id: Optional[str],
    uid: Optional[str],
    fingerprint: Optional[str],
    ticket_id: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ingested_messages (source, message_id, uid, fingerprint, ticket_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (source, message_id, uid, fingerprint, ticket_id, utc_now_iso()),
        )
        conn.commit()
