from __future__ import annotations

from app.repositories import agents as agent_repo
from app.repositories import tickets as ticket_repo
from app.schemas import TicketResponse


def update_status(ticket_id: str, status: str, resolution_notes: str | None) -> TicketResponse | None:
    current = ticket_repo.get_ticket(ticket_id)
    updated = ticket_repo.update_ticket_status(ticket_id, status, resolution_notes)
    if not current or not updated:
        return updated

    if status.upper() == "RESOLVED" and current.assigned_agent_id:
        agent_repo.update_workload(current.assigned_agent_id, -1)

    return updated
