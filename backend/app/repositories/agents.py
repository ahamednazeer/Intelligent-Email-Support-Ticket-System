from __future__ import annotations

import json
from typing import Optional
from uuid import uuid4

from app.db import get_conn
from app.schemas import AgentCreate, AgentResponse


def create_agent(payload: AgentCreate) -> AgentResponse:
    agent_id = payload.agent_id or str(uuid4())
    skills_json = json.dumps(payload.skills)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO agents (id, name, email, department, skills_json, active, workload, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                payload.name,
                payload.email,
                payload.department,
                skills_json,
                1 if payload.active else 0,
                0,
                payload.tier,
            ),
        )
        conn.commit()

    return AgentResponse(
        agent_id=agent_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        skills=payload.skills,
        tier=payload.tier,
        active=payload.active,
        workload=0,
    )


def list_agents(active_only: bool = False) -> list[AgentResponse]:
    query = "SELECT * FROM agents"
    params = []
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY workload ASC"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    results: list[AgentResponse] = []
    for row in rows:
        skills = json.loads(row["skills_json"]) if row["skills_json"] else []
        results.append(
            AgentResponse(
                agent_id=row["id"],
                name=row["name"],
                email=row["email"],
                department=row["department"],
                skills=skills,
                tier=row["tier"],
                active=bool(row["active"]),
                workload=row["workload"],
            )
        )
    return results


def get_agent(agent_id: str) -> Optional[AgentResponse]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        return None
    skills = json.loads(row["skills_json"]) if row["skills_json"] else []
    return AgentResponse(
        agent_id=row["id"],
        name=row["name"],
        email=row["email"],
        department=row["department"],
        skills=skills,
        tier=row["tier"],
        active=bool(row["active"]),
        workload=row["workload"],
    )


def find_best_agent(required_skill: Optional[str]) -> Optional[AgentResponse]:
    agents = list_agents(active_only=True)
    if not agents:
        return None

    if required_skill:
        skilled = [a for a in agents if required_skill in a.skills]
        if skilled:
            return skilled[0]
        return None

    return agents[0]


def update_workload(agent_id: str, delta: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE agents SET workload = MAX(0, workload + ?) WHERE id = ?",
            (delta, agent_id),
        )
        conn.commit()


def update_active(agent_id: str, active: bool) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE agents SET active = ? WHERE id = ?",
            (1 if active else 0, agent_id),
        )
        conn.commit()
    return cursor.rowcount > 0


def delete_agent(agent_id: str) -> bool:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()
    return cursor.rowcount > 0
