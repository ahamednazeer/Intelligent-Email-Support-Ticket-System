from __future__ import annotations

from app.db import get_conn
from app.schemas import TicketResponseItem
from app.utils.time import utc_now_iso


def create_response(
    ticket_id: str,
    author_user_id: str,
    message: str,
    is_internal: bool,
) -> TicketResponseItem:
    now = utc_now_iso()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ticket_responses (ticket_id, author_user_id, message, is_internal, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, author_user_id, message, 1 if is_internal else 0, now),
        )
        response_id = cursor.lastrowid
        conn.commit()

        row = conn.execute(
            """
            SELECT r.id, r.ticket_id, r.message, r.is_internal, r.created_at,
                   u.username, u.role
            FROM ticket_responses r
            JOIN users u ON u.id = r.author_user_id
            WHERE r.id = ?
            """,
            (response_id,),
        ).fetchone()

    return TicketResponseItem(
        response_id=row["id"],
        ticket_id=row["ticket_id"],
        author_username=row["username"],
        author_role=row["role"],
        message=row["message"],
        is_internal=bool(row["is_internal"]),
        created_at=row["created_at"],
    )


def list_responses(ticket_id: str) -> list[TicketResponseItem]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.ticket_id, r.message, r.is_internal, r.created_at,
                   u.username, u.role
            FROM ticket_responses r
            JOIN users u ON u.id = r.author_user_id
            WHERE r.ticket_id = ?
            ORDER BY r.created_at ASC
            """,
            (ticket_id,),
        ).fetchall()

    return [
        TicketResponseItem(
            response_id=row["id"],
            ticket_id=row["ticket_id"],
            author_username=row["username"],
            author_role=row["role"],
            message=row["message"],
            is_internal=bool(row["is_internal"]),
            created_at=row["created_at"],
        )
        for row in rows
    ]
