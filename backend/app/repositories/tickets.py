from __future__ import annotations

import json
from typing import Optional
from datetime import datetime, timedelta, timezone
import hashlib

from app.db import get_conn
from app.schemas import (
    ClassificationResult,
    PreprocessResult,
    PriorityResult,
    RoutingResult,
    StructuredTicket,
    TicketResponse,
)
from app.utils.time import utc_now_iso


def create_ticket(
    structured: StructuredTicket,
    preprocess: PreprocessResult,
    classification: ClassificationResult,
    priority: PriorityResult,
    routing: RoutingResult,
) -> TicketResponse:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tickets (
                id, sender_email, subject, body, attachments_json, created_at, updated_at, status,
                language, cleaned_text, entities_json, embedding_json, category, subcategory,
                intent_label, confidence_score, needs_manual_review, sentiment_score,
                priority_level, urgency_score, sla_deadline, assigned_agent_id, suggested_agent_id, review_required, department
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                structured.ticket_id,
                structured.sender,
                structured.subject,
                structured.body,
                json.dumps([a.model_dump() for a in structured.attachments]),
                structured.created_at,
                now,
                routing.updated_status,
                preprocess.language,
                preprocess.cleaned_text,
                json.dumps(preprocess.entities),
                json.dumps(preprocess.embedding),
                classification.ticket_category,
                classification.subcategory,
                classification.intent_label,
                classification.confidence_score,
                1 if classification.needs_manual_review else 0,
                priority.sentiment_score,
                priority.priority_level,
                priority.urgency_score,
                priority.sla_deadline,
                routing.assigned_agent_id,
                routing.suggested_agent_id,
                1 if routing.review_required else 0,
                routing.department,
            ),
        )
        conn.commit()

    return TicketResponse(
        ticket_id=structured.ticket_id,
        sender_email=structured.sender,
        subject=structured.subject,
        body=structured.body,
        status=routing.updated_status,
        category=classification.ticket_category,
        subcategory=classification.subcategory,
        intent_label=classification.intent_label,
        confidence_score=classification.confidence_score,
        needs_manual_review=classification.needs_manual_review,
        priority_level=priority.priority_level,
        urgency_score=priority.urgency_score,
        sla_deadline=priority.sla_deadline,
        assigned_agent_id=routing.assigned_agent_id,
        department=routing.department,
        suggested_agent_id=routing.suggested_agent_id,
        review_required=routing.review_required,
        resolution_notes=None,
        label_category=None,
        label_subcategory=None,
        label_intent=None,
        label_updated_at=None,
        created_at=structured.created_at,
        updated_at=now,
        resolved_at=None,
    )


def _row_to_ticket(row) -> TicketResponse:
    return TicketResponse(
        ticket_id=row["id"],
        sender_email=row["sender_email"],
        subject=row["subject"],
        body=row["body"],
        status=row["status"],
        category=row["category"],
        subcategory=row["subcategory"],
        intent_label=row["intent_label"],
        confidence_score=row["confidence_score"],
        needs_manual_review=bool(row["needs_manual_review"]),
        priority_level=row["priority_level"],
        urgency_score=row["urgency_score"],
        sla_deadline=row["sla_deadline"],
        assigned_agent_id=row["assigned_agent_id"],
        department=row["department"],
        suggested_agent_id=row["suggested_agent_id"],
        review_required=bool(row["review_required"]),
        resolution_notes=row["resolution_notes"],
        label_category=row["label_category"],
        label_subcategory=row["label_subcategory"],
        label_intent=row["label_intent"],
        label_updated_at=row["label_updated_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolved_at=row["resolved_at"],
    )


def get_ticket(ticket_id: str) -> Optional[TicketResponse]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        return None
    return _row_to_ticket(row)


def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_agent_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TicketResponse]:
    query = "SELECT * FROM tickets"
    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if priority:
        conditions.append("priority_level = ?")
        params.append(priority)
    if assigned_agent_id:
        conditions.append("assigned_agent_id = ?")
        params.append(assigned_agent_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_ticket(row) for row in rows]


def update_ticket_status(ticket_id: str, status: str, resolution_notes: Optional[str]) -> Optional[TicketResponse]:
    now = utc_now_iso()
    resolved_at = now if status.upper() == "RESOLVED" else None
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET status = ?, updated_at = ?, resolution_notes = COALESCE(?, resolution_notes),
                last_response_at = ?, response_count = response_count + 1,
                resolved_at = COALESCE(?, resolved_at)
            WHERE id = ?
            """,
            (status, now, resolution_notes, now, resolved_at, ticket_id),
        )
        conn.commit()

    return get_ticket(ticket_id)


def update_ticket_assignment(
    ticket_id: str,
    assigned_agent_id: Optional[str],
    department: Optional[str],
    status: Optional[str],
) -> Optional[TicketResponse]:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET assigned_agent_id = ?, department = COALESCE(?, department),
                status = COALESCE(?, status), updated_at = ?,
                review_required = 0, suggested_agent_id = NULL
            WHERE id = ?
            """,
            (assigned_agent_id, department, status, now, ticket_id),
        )
        conn.commit()
    return get_ticket(ticket_id)


def count_open_tickets_for_agent(agent_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT COUNT(1) AS total
            FROM tickets
            WHERE assigned_agent_id = ? AND status != 'RESOLVED'
            """,
            (agent_id,),
        ).fetchone()
    return int(row["total"]) if row else 0


def update_ticket_label(
    ticket_id: str,
    label_category: Optional[str],
    label_subcategory: Optional[str],
    label_intent: Optional[str],
) -> Optional[TicketResponse]:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET label_category = ?, label_subcategory = ?, label_intent = ?, label_updated_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (label_category, label_subcategory, label_intent, now, now, ticket_id),
        )
        conn.commit()
    return get_ticket(ticket_id)


def update_ticket_analysis(
    ticket_id: str,
    preprocess: PreprocessResult,
    classification: ClassificationResult,
    department: Optional[str],
) -> Optional[TicketResponse]:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET cleaned_text = ?, entities_json = ?, embedding_json = ?, language = ?,
                category = ?, subcategory = ?, intent_label = ?, confidence_score = ?,
                needs_manual_review = ?, department = COALESCE(?, department), updated_at = ?
            WHERE id = ?
            """,
            (
                preprocess.cleaned_text,
                json.dumps(preprocess.entities),
                json.dumps(preprocess.embedding),
                preprocess.language,
                classification.ticket_category,
                classification.subcategory,
                classification.intent_label,
                classification.confidence_score,
                1 if classification.needs_manual_review else 0,
                department,
                now,
                ticket_id,
            ),
        )
        conn.commit()
    return get_ticket(ticket_id)


def dedupe_tickets(window_hours: int = 24, dry_run: bool = False) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, sender_email, subject, body, created_at
            FROM tickets
            WHERE created_at >= ?
            ORDER BY created_at ASC
            """,
            (cutoff,),
        ).fetchall()

    groups: dict[str, list] = {}
    for row in rows:
        sender = (row["sender_email"] or "").lower()
        subject = (row["subject"] or "").strip().lower()
        body = (row["body"] or "").strip()
        fingerprint = hashlib.sha256(f"{sender}\n{subject}\n{body}".encode("utf-8", errors="ignore")).hexdigest()
        groups.setdefault(fingerprint, []).append(row)

    duplicate_ids: list[str] = []
    for items in groups.values():
        if len(items) > 1:
            items_sorted = sorted(items, key=lambda r: r["created_at"])
            duplicate_ids.extend([row["id"] for row in items_sorted[1:]])

    if dry_run or not duplicate_ids:
        return {
            "window_hours": window_hours,
            "scanned": len(rows),
            "duplicates_found": len(duplicate_ids),
            "deleted": 0,
            "dry_run": dry_run,
        }

    placeholders = ",".join("?" for _ in duplicate_ids)
    with get_conn() as conn:
        conn.execute(
            f"DELETE FROM ticket_responses WHERE ticket_id IN ({placeholders})",
            duplicate_ids,
        )
        conn.execute(
            f"DELETE FROM feedback WHERE ticket_id IN ({placeholders})",
            duplicate_ids,
        )
        conn.execute(
            f"DELETE FROM audit_logs WHERE target_type = 'TICKET' AND target_id IN ({placeholders})",
            duplicate_ids,
        )
        conn.execute(
            f"DELETE FROM ingested_messages WHERE ticket_id IN ({placeholders})",
            duplicate_ids,
        )
        conn.execute(
            f"DELETE FROM tickets WHERE id IN ({placeholders})",
            duplicate_ids,
        )
        conn.commit()

    return {
        "window_hours": window_hours,
        "scanned": len(rows),
        "duplicates_found": len(duplicate_ids),
        "deleted": len(duplicate_ids),
        "dry_run": dry_run,
    }


def list_labeled_samples(limit: int = 5000) -> list[tuple[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT COALESCE(cleaned_text, body) AS text, label_category
            FROM tickets
            WHERE label_category IS NOT NULL AND label_category != ''
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [(row["text"], row["label_category"]) for row in rows]
