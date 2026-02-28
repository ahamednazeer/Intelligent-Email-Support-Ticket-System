from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None


class IngestRequest(BaseModel):
    sender_email: str = Field(..., description="Customer email address")
    subject: Optional[str] = None
    body: str
    attachments: List[Attachment] = Field(default_factory=list)
    customer_tier: Optional[str] = Field(default=None, description="VIP/Enterprise/Standard")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = Field(
        ...,
        description="ADMIN, SUPERVISOR, or category role (BILLING, TECHNICAL, ACCOUNT, COMPLAINT, FEATURE_REQUEST, GENERAL, GOVERNMENT)",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    agent_id: Optional[str] = None
    active: bool = True


class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    agent_id: Optional[str] = None
    active: bool
    created_at: str


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


class UserStatusUpdate(BaseModel):
    active: bool


class AuditLogItem(BaseModel):
    log_id: int
    action: str
    target_type: str
    target_id: str
    actor_username: str
    actor_role: str
    metadata: Dict[str, Any]
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class StructuredTicket(BaseModel):
    ticket_id: str
    sender: str
    subject: Optional[str]
    body: str
    attachments: List[Attachment]
    created_at: str
    status: str


class PreprocessResult(BaseModel):
    cleaned_text: str
    entities: Dict[str, List[str]]
    embedding: List[int]
    language: str
    tokens: List[str]


class ClassificationResult(BaseModel):
    ticket_category: str
    subcategory: Optional[str]
    intent_label: str
    confidence_score: float
    needs_manual_review: bool


class PriorityResult(BaseModel):
    priority_level: str
    urgency_score: float
    sla_deadline: str
    sentiment_score: float


class RoutingResult(BaseModel):
    assigned_agent_id: Optional[str]
    department: Optional[str]
    updated_status: str
    suggested_agent_id: Optional[str] = None
    review_required: bool = False


class TicketResponse(BaseModel):
    ticket_id: str
    sender_email: str
    subject: Optional[str]
    body: str
    status: str
    category: Optional[str]
    subcategory: Optional[str]
    intent_label: Optional[str]
    confidence_score: Optional[float]
    needs_manual_review: bool = False
    priority_level: Optional[str]
    urgency_score: Optional[float]
    sla_deadline: Optional[str]
    assigned_agent_id: Optional[str]
    department: Optional[str]
    suggested_agent_id: Optional[str] = None
    review_required: bool = False
    resolution_notes: Optional[str] = None
    label_category: Optional[str] = None
    label_subcategory: Optional[str] = None
    label_intent: Optional[str] = None
    label_updated_at: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None


class AgentCreate(BaseModel):
    agent_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    tier: Optional[str] = None
    active: bool = True


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    email: Optional[str]
    department: Optional[str]
    skills: List[str]
    tier: Optional[str]
    active: bool
    workload: int


class AgentStatusUpdate(BaseModel):
    active: bool


class TicketStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


class FeedbackCreate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    ticket_id: str
    rating: Optional[int]
    comments: Optional[str]
    created_at: str


class TicketResponseCreate(BaseModel):
    message: str
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    is_internal: bool = False


class TicketResponseItem(BaseModel):
    response_id: int
    ticket_id: str
    author_username: str
    author_role: str
    message: str
    is_internal: bool
    created_at: str


class TicketAssignment(BaseModel):
    agent_id: Optional[str] = None


class TicketLabelUpdate(BaseModel):
    label_category: str
    label_subcategory: Optional[str] = None
    label_intent: Optional[str] = None


class AnalyticsSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    avg_resolution_time_hours: Optional[float]
    tickets_by_category: Dict[str, int]
    tickets_by_priority: Dict[str, int]
