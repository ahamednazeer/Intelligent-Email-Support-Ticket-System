from __future__ import annotations

from app.repositories import feedback as feedback_repo
from app.schemas import FeedbackCreate, FeedbackResponse


def record_feedback(ticket_id: str, payload: FeedbackCreate) -> FeedbackResponse:
    return feedback_repo.create_feedback(ticket_id, payload)
