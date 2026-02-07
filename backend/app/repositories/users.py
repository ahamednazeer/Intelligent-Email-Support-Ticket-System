from __future__ import annotations

from typing import Optional
from uuid import uuid4

from app.auth import hash_password
from app.db import get_conn
from app.schemas import UserCreate, UserResponse
from app.utils.time import utc_now_iso


def _row_to_user(row) -> UserResponse:
    return UserResponse(
        user_id=row["id"],
        username=row["username"],
        role=row["role"],
        full_name=row["full_name"],
        email=row["email"],
        agent_id=row["agent_id"],
        active=bool(row["active"]),
        created_at=row["created_at"],
    )


def create_user(payload: UserCreate) -> UserResponse:
    user_id = str(uuid4())
    password_hash = hash_password(payload.password)
    created_at = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, role, full_name, email, agent_id, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload.username,
                password_hash,
                payload.role,
                payload.full_name,
                payload.email,
                payload.agent_id,
                1 if payload.active else 0,
                created_at,
            ),
        )
        conn.commit()

    return UserResponse(
        user_id=user_id,
        username=payload.username,
        role=payload.role,
        full_name=payload.full_name,
        email=payload.email,
        agent_id=payload.agent_id,
        active=payload.active,
        created_at=created_at,
    )


def list_users() -> list[UserResponse]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [_row_to_user(row) for row in rows]


def get_user_by_username(username: str) -> Optional[UserResponse]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        return None
    return _row_to_user(row)


def get_user_by_id(user_id: str) -> Optional[UserResponse]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    return _row_to_user(row)


def get_user_with_password(username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return row


def update_password(user_id: str, new_password: str) -> bool:
    new_hash = hash_password(new_password)
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )
        conn.commit()
    return cursor.rowcount > 0


def update_active(user_id: str, active: bool) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE users SET active = ? WHERE id = ?",
            (1 if active else 0, user_id),
        )
        conn.commit()
    return cursor.rowcount > 0


def get_user_by_agent_id(agent_id: str) -> Optional[UserResponse]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE agent_id = ?", (agent_id,)).fetchone()
    if not row:
        return None
    return _row_to_user(row)


def count_users_by_agent_id(agent_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(1) AS total FROM users WHERE agent_id = ?", (agent_id,)).fetchone()
    return int(row["total"]) if row else 0


def list_users_by_agent_id(agent_id: str) -> list[UserResponse]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users WHERE agent_id = ?", (agent_id,)).fetchall()
    return [_row_to_user(row) for row in rows]


def delete_users_by_agent_id(agent_id: str) -> int:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM users WHERE agent_id = ?", (agent_id,))
        conn.commit()
    return cursor.rowcount


def delete_user(user_id: str) -> bool:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return cursor.rowcount > 0
