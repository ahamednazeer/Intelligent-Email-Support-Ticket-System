from __future__ import annotations

from app.repositories import analytics as analytics_repo
from app.schemas import AnalyticsSummary


def get_summary() -> AnalyticsSummary:
    return analytics_repo.get_summary()
