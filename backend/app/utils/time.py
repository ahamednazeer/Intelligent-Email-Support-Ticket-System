from __future__ import annotations

from datetime import datetime, timezone, timedelta


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_hours_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
