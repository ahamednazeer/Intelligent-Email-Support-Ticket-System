from __future__ import annotations

import os

from app.repositories import agents as agent_repo
from app.repositories import users as user_repo
from app.schemas import AgentCreate, UserCreate


def ensure_default_agents() -> None:
    existing = agent_repo.list_agents(active_only=False)
    if existing:
        return

    agent_repo.create_agent(
        AgentCreate(
            agent_id="agent-001",
            name="Avery Cole",
            email="agent1@support.local",
            department="Engineering Support",
            skills=["technical"],
            tier="L2",
            active=True,
        )
    )


def ensure_default_users() -> None:
    existing = user_repo.list_users()
    if existing:
        return

    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    agent_username = os.getenv("DEFAULT_AGENT_USERNAME", "agent1")
    agent_password = os.getenv("DEFAULT_AGENT_PASSWORD", "agent123")

    user_repo.create_user(
        UserCreate(
            username=admin_username,
            password=admin_password,
            role="ADMIN",
            full_name="System Administrator",
            email="admin@support.local",
            active=True,
        )
    )

    user_repo.create_user(
        UserCreate(
            username=agent_username,
            password=agent_password,
            role="TECHNICAL",
            full_name="Avery Cole",
            email="agent1@support.local",
            agent_id="agent-001",
            active=True,
        )
    )


def bootstrap_defaults() -> None:
    ensure_default_agents()
    ensure_default_users()
