from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv(
    "DB_PATH",
    str(Path(__file__).resolve().parents[2] / "backend" / "data" / "tickets.db"),
)


def _ensure_db_dir() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    _ensure_db_dir()
    schema = """
    CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        sender_email TEXT NOT NULL,
        subject TEXT,
        body TEXT NOT NULL,
        attachments_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        status TEXT NOT NULL,
        language TEXT,
        cleaned_text TEXT,
        entities_json TEXT,
        embedding_json TEXT,
        category TEXT,
        subcategory TEXT,
        intent_label TEXT,
        confidence_score REAL,
        needs_manual_review INTEGER DEFAULT 0,
        sentiment_score REAL,
        priority_level TEXT,
        urgency_score REAL,
        sla_deadline TEXT,
        assigned_agent_id TEXT,
        suggested_agent_id TEXT,
        review_required INTEGER DEFAULT 0,
        department TEXT,
        resolution_notes TEXT,
        label_category TEXT,
        label_subcategory TEXT,
        label_intent TEXT,
        label_updated_at TEXT,
        last_response_at TEXT,
        response_count INTEGER DEFAULT 0,
        resolved_at TEXT
    );

    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT,
        skills_json TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        workload INTEGER NOT NULL DEFAULT 0,
        tier TEXT
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL,
        rating INTEGER,
        comments TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(ticket_id) REFERENCES tickets(id)
    );

    CREATE TABLE IF NOT EXISTS ticket_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL,
        author_user_id TEXT NOT NULL,
        message TEXT NOT NULL,
        is_internal INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(ticket_id) REFERENCES tickets(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        metadata_json TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        agent_id TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ingested_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        message_id TEXT,
        uid TEXT,
        fingerprint TEXT,
        ticket_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
    CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority_level);
    CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
    CREATE INDEX IF NOT EXISTS idx_ticket_responses_ticket ON ticket_responses(ticket_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_type, target_id);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_ingested_messages_source_message ON ingested_messages(source, message_id);
    CREATE INDEX IF NOT EXISTS idx_ingested_messages_source_uid ON ingested_messages(source, uid);
    CREATE INDEX IF NOT EXISTS idx_ingested_messages_source_fingerprint ON ingested_messages(source, fingerprint);
    """
    with get_conn() as conn:
        conn.executescript(schema)

        def ensure_column(table: str, column: str, column_def: str) -> None:
            existing = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")

        ensure_column("tickets", "label_category", "TEXT")
        ensure_column("tickets", "label_subcategory", "TEXT")
        ensure_column("tickets", "label_intent", "TEXT")
        ensure_column("tickets", "label_updated_at", "TEXT")
        ensure_column("tickets", "suggested_agent_id", "TEXT")
        ensure_column("tickets", "review_required", "INTEGER DEFAULT 0")

        conn.commit()
