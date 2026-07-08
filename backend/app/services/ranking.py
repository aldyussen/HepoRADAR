"""Lost-patient tagging and worklist ranking.

Operational definition of "lost" (Part 0.1 of the plan): the org's data has
no `referred?` / diagnosis / hepatology-visit / fibroscan columns, so we use
the stated fallback — high risk AND the most recent risky lab is more than
`settings.lost_no_repeat_months` old with no repeat test since.

`followup_dates` is accepted for forward-compatibility: if real follow-up
event columns show up later, pass them and a follow-up after the last risky
lab clears the flag regardless of how much time has passed.
"""

import datetime as dt
from typing import Iterable

from app.config import settings


def _month_diff(later: dt.date, earlier: dt.date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def is_lost(
    zone: str | None,
    last_risky_lab_date: dt.date | None,
    reference_date: dt.date,
    ml_risk: float | None = None,
    followup_dates: Iterable[dt.date] | None = None,
) -> bool:
    is_risky = zone == "high" or (ml_risk is not None and ml_risk >= settings.ml_risk_threshold)
    if not is_risky or last_risky_lab_date is None:
        return False

    if followup_dates and any(d > last_risky_lab_date for d in followup_dates):
        return False

    return _month_diff(reference_date, last_risky_lab_date) > settings.lost_no_repeat_months


def rank_worklist(patients: list[dict]) -> list[dict]:
    """Sort by risk desc, then recency (most overdue first), then data completeness desc.

    Each dict may have: risk (float|None), last_lab_date (date|None), completeness (float|None, 0-1).
    """

    def sort_key(p: dict):
        risk = p.get("risk")
        risk_rank = -risk if risk is not None else float("inf")

        last_lab_date = p.get("last_lab_date")
        recency_rank = last_lab_date if last_lab_date is not None else dt.date.max

        completeness = p.get("completeness") or 0.0
        completeness_rank = -completeness

        return (risk_rank, recency_rank, completeness_rank)

    return sorted(patients, key=sort_key)
