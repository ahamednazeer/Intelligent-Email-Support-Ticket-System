from __future__ import annotations

import os

from app.repositories import agents as agent_repo
from app.schemas import ClassificationResult, PriorityResult, RoutingResult

_DEPARTMENT_BY_CATEGORY = {
    "technical": "Engineering Support",
    "billing": "Billing",
    "account": "Account",
    "complaint": "Customer Care",
    "feature_request": "Product",
    "general": "General",
}


def route(
    classification: ClassificationResult,
    priority: PriorityResult,
) -> RoutingResult:
    department = _DEPARTMENT_BY_CATEGORY.get(classification.ticket_category, "General")
    assigned_agent_id = None
    updated_status = "QUEUED"
    review_required = os.getenv("ASSIGNMENT_REQUIRES_REVIEW", "true").lower() in {"1", "true", "yes"}

    if priority.priority_level == "CRITICAL":
        return RoutingResult(
            assigned_agent_id=None,
            department="Escalations",
            updated_status="ESCALATED",
            suggested_agent_id=None,
            review_required=False,
        )

    best_agent = agent_repo.find_best_agent(classification.ticket_category)
    if best_agent:
        if review_required:
            return RoutingResult(
                assigned_agent_id=None,
                department=department,
                updated_status="REVIEW_PENDING",
                suggested_agent_id=best_agent.agent_id,
                review_required=True,
            )
        assigned_agent_id = best_agent.agent_id
        updated_status = "ASSIGNED"
        agent_repo.update_workload(best_agent.agent_id, 1)

    return RoutingResult(
        assigned_agent_id=assigned_agent_id,
        department=department,
        updated_status=updated_status,
        suggested_agent_id=None,
        review_required=False,
    )
