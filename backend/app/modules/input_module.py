from __future__ import annotations

from uuid import uuid4

from app.schemas import IngestRequest, StructuredTicket
from app.utils.time import utc_now_iso


def ingest(request: IngestRequest) -> StructuredTicket:
    return StructuredTicket(
        ticket_id=str(uuid4()),
        sender=request.sender_email,
        subject=request.subject,
        body=request.body,
        attachments=request.attachments,
        created_at=utc_now_iso(),
        status="NEW",
    )
