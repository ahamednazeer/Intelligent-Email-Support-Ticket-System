from __future__ import annotations

from app.db import get_conn
from app.schemas import AnalyticsSummary


def get_summary() -> AnalyticsSummary:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
        open_count = conn.execute(
            "SELECT COUNT(*) AS c FROM tickets WHERE status != 'RESOLVED'"
        ).fetchone()["c"]
        resolved = conn.execute(
            "SELECT COUNT(*) AS c FROM tickets WHERE status = 'RESOLVED'"
        ).fetchone()["c"]
        avg_row = conn.execute(
            """
            SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24.0) AS avg_hours
            FROM tickets
            WHERE resolved_at IS NOT NULL
            """
        ).fetchone()
        avg_hours = avg_row["avg_hours"] if avg_row else None

        category_rows = conn.execute(
            "SELECT category, COUNT(*) AS c FROM tickets GROUP BY category"
        ).fetchall()
        priority_rows = conn.execute(
            "SELECT priority_level, COUNT(*) AS c FROM tickets GROUP BY priority_level"
        ).fetchall()

    tickets_by_category = {row["category"] or "unknown": row["c"] for row in category_rows}
    tickets_by_priority = {
        row["priority_level"] or "unknown": row["c"] for row in priority_rows
    }

    return AnalyticsSummary(
        total_tickets=total,
        open_tickets=open_count,
        resolved_tickets=resolved,
        avg_resolution_time_hours=round(avg_hours, 2) if avg_hours is not None else None,
        tickets_by_category=tickets_by_category,
        tickets_by_priority=tickets_by_priority,
    )
