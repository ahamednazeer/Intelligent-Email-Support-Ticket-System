from __future__ import annotations

import json
from typing import Any

from app.db import get_conn
from app.schemas import AuditLogItem
from app.utils.time import utc_now_iso


def log_action(
    actor_user_id: str,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> AuditLogItem:
    now = utc_now_iso()
    metadata_json = json.dumps(metadata or {})
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (actor_user_id, action, target_type, target_id, metadata_json, now),
        )
        log_id = cursor.lastrowid
        conn.commit()

        row = conn.execute(
            """
            SELECT a.id, a.action, a.target_type, a.target_id, a.metadata_json, a.created_at,
                   u.username, u.role
            FROM audit_logs a
            JOIN users u ON u.id = a.actor_user_id
            WHERE a.id = ?
            """,
            (log_id,),
        ).fetchone()

    return AuditLogItem(
        log_id=row["id"],
        action=row["action"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        actor_username=row["username"],
        actor_role=row["role"],
        metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
        created_at=row["created_at"],
    )


def list_logs(limit: int = 100, offset: int = 0) -> list[AuditLogItem]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.action, a.target_type, a.target_id, a.metadata_json, a.created_at,
                   u.username, u.role
            FROM audit_logs a
            JOIN users u ON u.id = a.actor_user_id
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [
        AuditLogItem(
            log_id=row["id"],
            action=row["action"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            actor_username=row["username"],
            actor_role=row["role"],
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            created_at=row["created_at"],
        )
        for row in rows
    ]
