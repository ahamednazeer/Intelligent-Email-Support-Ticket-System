from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import init_db
from app.bootstrap import bootstrap_defaults
from app.deps import get_current_user, require_roles
from app.auth import create_access_token, verify_password
from app.pipeline import process_ticket
from app.schemas import (
    AgentCreate,
    AgentResponse,
    AgentStatusUpdate,
    AnalyticsSummary,
    AuthResponse,
    FeedbackCreate,
    FeedbackResponse,
    TicketAssignment,
    TicketResponseCreate,
    TicketResponseItem,
    IngestRequest,
    LoginRequest,
    PasswordResetRequest,
    UserStatusUpdate,
    AuditLogItem,
    TicketLabelUpdate,
    TicketResponse,
    TicketStatusUpdate,
    UserCreate,
    UserResponse,
)
from app.modules import analytics as analytics_module
from app.modules import closure_feedback as feedback_module
from app.modules import email_sender, email_ingest
from app.modules import learning as learning_module
from app.modules import ticket_management
from app.repositories import agents as agent_repo
from app.repositories import audit as audit_repo
from app.repositories import responses as response_repo
from app.repositories import tickets as ticket_repo
from app.repositories import users as user_repo

load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env", override=False)

app = FastAPI(title="Intelligent Email Support Ticket System")

AGENT_ROLES = {
    "BILLING",
    "TECHNICAL",
    "ACCOUNT",
    "COMPLAINT",
    "FEATURE_REQUEST",
    "GENERAL",
}
ALL_ROLES = {"ADMIN", "SUPERVISOR"} | AGENT_ROLES
DEPARTMENT_BY_ROLE = {
    "BILLING": "Billing",
    "TECHNICAL": "Engineering Support",
    "ACCOUNT": "Account",
    "COMPLAINT": "Customer Care",
    "FEATURE_REQUEST": "Product",
    "GENERAL": "General",
}

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    bootstrap_defaults()
    email_ingest.start_imap_poller()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest/email", response_model=TicketResponse)
def ingest_email(
    payload: IngestRequest,
    _: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> TicketResponse:
    return process_ticket(payload)


@app.post("/ingest/portal", response_model=TicketResponse)
def ingest_portal(
    payload: IngestRequest,
    _: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> TicketResponse:
    return process_ticket(payload)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user_row = user_repo.get_user_with_password(payload.username)
    if not user_row or not verify_password(payload.password, user_row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user_row["active"]:
        raise HTTPException(status_code=403, detail="User is inactive")

    user = user_repo.get_user_by_username(payload.username)
    token = create_access_token({"sub": user.username, "role": user.role, "uid": user.user_id})
    return AuthResponse(access_token=token, token_type="bearer", user=user)


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user


@app.get("/users", response_model=list[UserResponse])
def list_users(_: UserResponse = Depends(require_roles("ADMIN"))) -> list[UserResponse]:
    return user_repo.list_users()


@app.post("/users", response_model=UserResponse)
def create_user(
    payload: UserCreate,
    _: UserResponse = Depends(require_roles("ADMIN")),
) -> UserResponse:
    role = payload.role.upper()
    if role not in ALL_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Role must be ADMIN, SUPERVISOR, or a category role (BILLING, TECHNICAL, ACCOUNT, COMPLAINT, FEATURE_REQUEST, GENERAL)",
        )

    updated_payload = payload
    if role in AGENT_ROLES and not payload.agent_id:
        agent = agent_repo.create_agent(
            AgentCreate(
                name=payload.full_name or payload.username,
                email=payload.email,
                department=DEPARTMENT_BY_ROLE.get(role, "General"),
                skills=[role.lower()],
                tier="L1",
                active=True,
            )
        )
        updated_payload = payload.model_copy(update={"agent_id": agent.agent_id, "role": role})
    else:
        if payload.agent_id:
            agent = agent_repo.get_agent(payload.agent_id)
            if not agent:
                raise HTTPException(status_code=400, detail="Agent profile not found")
            if role in AGENT_ROLES and role.lower() not in agent.skills:
                raise HTTPException(status_code=400, detail="Agent profile missing required category skill")
        updated_payload = payload.model_copy(update={"role": role})

    return user_repo.create_user(updated_payload)


@app.post("/users/{user_id}/password")
def reset_password(
    user_id: str,
    payload: PasswordResetRequest,
    current_user: UserResponse = Depends(require_roles("ADMIN")),
) -> dict:
    updated = user_repo.update_password(user_id, payload.new_password)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="PASSWORD_RESET",
        target_type="USER",
        target_id=user_id,
        metadata={},
    )
    return {"status": "ok"}


@app.post("/users/{user_id}/active", response_model=UserResponse)
def update_user_active(
    user_id: str,
    payload: UserStatusUpdate,
    current_user: UserResponse = Depends(require_roles("ADMIN")),
) -> UserResponse:
    updated = user_repo.update_active(user_id, payload.active)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="USER_STATUS_UPDATE",
        target_type="USER",
        target_id=user_id,
        metadata={"active": payload.active},
    )
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    current_user: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> TicketResponse:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role in AGENT_ROLES and current_user.agent_id != ticket.assigned_agent_id:
        raise HTTPException(status_code=403, detail="Not authorized for this ticket")
    return ticket


@app.get("/tickets", response_model=list[TicketResponse])
def list_tickets(
    current_user: UserResponse = Depends(require_roles(*ALL_ROLES)),
    status: str | None = None,
    priority: str | None = None,
    assigned_agent_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[TicketResponse]:
    if current_user.role in AGENT_ROLES:
        if not current_user.agent_id:
            raise HTTPException(status_code=403, detail="Agent account is not linked to an agent profile")
        assigned_agent_id = current_user.agent_id
    return ticket_repo.list_tickets(
        status=status,
        priority=priority,
        assigned_agent_id=assigned_agent_id,
        limit=limit,
        offset=offset,
    )


@app.post("/tickets/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    current_user: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> TicketResponse:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role in AGENT_ROLES and current_user.agent_id != ticket.assigned_agent_id:
        raise HTTPException(status_code=403, detail="Not authorized for this ticket")

    updated = ticket_management.update_status(
        ticket_id=ticket_id, status=payload.status, resolution_notes=payload.resolution_notes
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated


@app.post("/agents", response_model=AgentResponse)
def create_agent(
    payload: AgentCreate,
    _: UserResponse = Depends(require_roles("ADMIN")),
) -> AgentResponse:
    allowed_skills = {"billing", "technical", "account", "complaint", "feature_request", "general"}
    invalid = [skill for skill in payload.skills if skill not in allowed_skills]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid skill(s): {', '.join(invalid)}")
    return agent_repo.create_agent(payload)


@app.get("/agents", response_model=list[AgentResponse])
def list_agents(
    active_only: bool = False,
    _: UserResponse = Depends(require_roles("ADMIN", "SUPERVISOR")),
) -> list[AgentResponse]:
    return agent_repo.list_agents(active_only=active_only)


@app.delete("/agents/{agent_id}")
def delete_agent(
    agent_id: str,
    current_user: UserResponse = Depends(require_roles("ADMIN")),
) -> dict:
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    open_tickets = ticket_repo.count_open_tickets_for_agent(agent_id)
    if open_tickets:
        raise HTTPException(status_code=400, detail="Agent has open tickets assigned; reassign them first")

    updated = agent_repo.update_active(agent_id, False)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")

    linked_users = user_repo.list_users_by_agent_id(agent_id)
    if linked_users:
        for user in linked_users:
            user_repo.update_active(user.user_id, False)
            audit_repo.log_action(
                actor_user_id=current_user.user_id,
                action="USER_STATUS_UPDATE",
                target_type="USER",
                target_id=user.user_id,
                metadata={"active": False, "agent_id": agent_id},
            )

    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="AGENT_STATUS_UPDATE",
        target_type="AGENT",
        target_id=agent_id,
        metadata={"name": agent.name, "email": agent.email, "active": False},
    )
    return {"status": "deactivated", "agent_id": agent_id}


@app.post("/agents/{agent_id}/active")
def set_agent_active(
    agent_id: str,
    payload: AgentStatusUpdate,
    current_user: UserResponse = Depends(require_roles("ADMIN")),
) -> dict:
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not payload.active:
        open_tickets = ticket_repo.count_open_tickets_for_agent(agent_id)
        if open_tickets:
            raise HTTPException(status_code=400, detail="Agent has open tickets assigned; reassign them first")

    updated = agent_repo.update_active(agent_id, payload.active)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")

    linked_users = user_repo.list_users_by_agent_id(agent_id)
    if linked_users:
        for user in linked_users:
            user_repo.update_active(user.user_id, payload.active)
            audit_repo.log_action(
                actor_user_id=current_user.user_id,
                action="USER_STATUS_UPDATE",
                target_type="USER",
                target_id=user.user_id,
                metadata={"active": payload.active, "agent_id": agent_id},
            )

    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="AGENT_STATUS_UPDATE",
        target_type="AGENT",
        target_id=agent_id,
        metadata={"name": agent.name, "email": agent.email, "active": payload.active},
    )
    return {"status": "updated", "agent_id": agent_id, "active": payload.active}


@app.post("/tickets/{ticket_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    ticket_id: str,
    payload: FeedbackCreate,
    _: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> FeedbackResponse:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return feedback_module.record_feedback(ticket_id, payload)


@app.get("/tickets/{ticket_id}/responses", response_model=list[TicketResponseItem])
def list_ticket_responses(
    ticket_id: str,
    current_user: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> list[TicketResponseItem]:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role in AGENT_ROLES and current_user.agent_id != ticket.assigned_agent_id:
        raise HTTPException(status_code=403, detail="Not authorized for this ticket")
    return response_repo.list_responses(ticket_id)


@app.post("/tickets/{ticket_id}/responses", response_model=TicketResponseItem)
def create_ticket_response(
    ticket_id: str,
    payload: TicketResponseCreate,
    current_user: UserResponse = Depends(require_roles(*ALL_ROLES)),
) -> TicketResponseItem:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role in AGENT_ROLES and current_user.agent_id != ticket.assigned_agent_id:
        raise HTTPException(status_code=403, detail="Not authorized for this ticket")

    response = response_repo.create_response(
        ticket_id=ticket_id,
        author_user_id=current_user.user_id,
        message=payload.message,
        is_internal=payload.is_internal,
    )

    if not payload.is_internal:
        subject = ticket.subject or f"Support Ticket {ticket.ticket_id[:8]}"
        email_sender.send_email(
            to_address=ticket.sender_email,
            subject=f"Re: {subject}",
            body=payload.message,
        )

    next_status = payload.status or ticket.status
    ticket_management.update_status(
        ticket_id=ticket_id,
        status=next_status,
        resolution_notes=payload.resolution_notes,
    )

    return response


@app.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(_: UserResponse = Depends(require_roles("ADMIN"))) -> AnalyticsSummary:
    return analytics_module.get_summary()


@app.post("/tickets/{ticket_id}/label", response_model=TicketResponse)
def label_ticket(
    ticket_id: str,
    payload: TicketLabelUpdate,
    current_user: UserResponse = Depends(require_roles("ADMIN", "SUPERVISOR")),
) -> TicketResponse:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    allowed_categories = {"billing", "technical", "account", "complaint", "feature_request", "general"}
    if payload.label_category not in allowed_categories:
        raise HTTPException(status_code=400, detail="Invalid label category")

    updated = ticket_repo.update_ticket_label(
        ticket_id=ticket_id,
        label_category=payload.label_category,
        label_subcategory=payload.label_subcategory,
        label_intent=payload.label_intent,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")

    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="TICKET_LABEL_UPDATE",
        target_type="TICKET",
        target_id=ticket_id,
        metadata={
            "label_category": payload.label_category,
            "label_subcategory": payload.label_subcategory,
            "label_intent": payload.label_intent,
        },
    )

    return updated


@app.post("/tickets/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: str,
    payload: TicketAssignment,
    current_user: UserResponse = Depends(require_roles("ADMIN", "SUPERVISOR")),
) -> TicketResponse:
    ticket = ticket_repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    target_agent = None
    if payload.agent_id:
        target_agent = agent_repo.get_agent(payload.agent_id)
        if not target_agent:
            raise HTTPException(status_code=400, detail="Agent not found")
        if not target_agent.active:
            raise HTTPException(status_code=400, detail="Agent is inactive")
        category = ticket.label_category or ticket.category
        if category and category in {"billing", "technical", "account", "complaint", "feature_request", "general"}:
            if category not in target_agent.skills:
                raise HTTPException(status_code=400, detail="Agent does not match ticket category")

    previous_agent_id = ticket.assigned_agent_id
    if ticket.assigned_agent_id and ticket.assigned_agent_id != payload.agent_id:
        agent_repo.update_workload(ticket.assigned_agent_id, -1)
    if payload.agent_id and ticket.assigned_agent_id != payload.agent_id:
        agent_repo.update_workload(payload.agent_id, 1)

    next_status = None
    if ticket.status != "RESOLVED":
        next_status = "ASSIGNED" if payload.agent_id else "QUEUED"

    updated = ticket_repo.update_ticket_assignment(
        ticket_id=ticket_id,
        assigned_agent_id=payload.agent_id,
        department=target_agent.department if target_agent else None,
        status=next_status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="TICKET_ASSIGNMENT",
        target_type="TICKET",
        target_id=ticket_id,
        metadata={"previous_agent_id": previous_agent_id, "new_agent_id": payload.agent_id},
    )
    return updated


@app.get("/audit/logs", response_model=list[AuditLogItem])
def list_audit_logs(
    _: UserResponse = Depends(require_roles("ADMIN")),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AuditLogItem]:
    return audit_repo.list_logs(limit=limit, offset=offset)


@app.post("/retrain")
def retrain(reason: str | None = None, _: UserResponse = Depends(require_roles("ADMIN"))) -> dict:
    return learning_module.queue_retrain(reason)


@app.post("/maintenance/dedupe")
def dedupe_tickets(
    hours: int = Query(24, ge=1, le=168),
    dry_run: bool = False,
    current_user: UserResponse = Depends(require_roles("ADMIN")),
) -> dict:
    result = ticket_repo.dedupe_tickets(window_hours=hours, dry_run=dry_run)
    audit_repo.log_action(
        actor_user_id=current_user.user_id,
        action="TICKET_DEDUPE",
        target_type="SYSTEM",
        target_id="tickets",
        metadata=result,
    )
    return result


@app.post("/maintenance/imap/poll")
def manual_imap_poll(
    _: UserResponse = Depends(require_roles("ADMIN", "SUPERVISOR")),
) -> dict:
    ingested = email_ingest.poll_once()
    return {"status": "ok", "ingested": ingested}
