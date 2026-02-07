from __future__ import annotations

from app.modules import (
    input_module,
    preprocessing,
    classification as classification_module,
    priority as priority_module,
    routing as routing_module,
)
from app.repositories import tickets as ticket_repo
from app.schemas import IngestRequest, TicketResponse


def process_ticket(request: IngestRequest) -> TicketResponse:
    structured = input_module.ingest(request)
    preprocess = preprocessing.preprocess(structured)
    classification = classification_module.classify(preprocess)
    priority = priority_module.predict_priority(
        preprocess=preprocess,
        classification=classification,
        customer_tier=request.customer_tier,
    )
    routing = routing_module.route(classification=classification, priority=priority)
    return ticket_repo.create_ticket(
        structured=structured,
        preprocess=preprocess,
        classification=classification,
        priority=priority,
        routing=routing,
    )
