from __future__ import annotations

from app.db import get_conn
from app.schemas import FeedbackCreate, FeedbackResponse
from app.utils.time import utc_now_iso


def create_feedback(ticket_id: str, payload: FeedbackCreate) -> FeedbackResponse:
    now = utc_now_iso()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (ticket_id, rating, comments, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (ticket_id, payload.rating, payload.comments, now),
        )
        conn.commit()
        feedback_id = cursor.lastrowid

    return FeedbackResponse(
        feedback_id=feedback_id,
        ticket_id=ticket_id,
        rating=payload.rating,
        comments=payload.comments,
        created_at=now,
    )
