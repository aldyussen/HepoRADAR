import datetime as dt

from app.config import settings
from app.services.ranking import is_lost, rank_worklist


def test_low_zone_is_never_lost():
    assert is_lost("low", dt.date(2025, 1, 1), dt.date(2026, 7, 8)) is False


def test_grey_zone_is_never_lost_without_ml_risk():
    assert is_lost("grey", dt.date(2025, 1, 1), dt.date(2026, 7, 8)) is False


def test_high_zone_stale_lab_is_lost():
    last_lab = dt.date(2025, 1, 1)
    reference = last_lab + dt.timedelta(days=31 * (settings.lost_no_repeat_months + 1))
    assert is_lost("high", last_lab, reference) is True


def test_high_zone_recent_lab_is_not_lost():
    last_lab = dt.date(2026, 6, 1)
    reference = dt.date(2026, 7, 8)
    assert is_lost("high", last_lab, reference) is False


def test_high_zone_with_followup_after_last_lab_is_not_lost():
    last_lab = dt.date(2024, 1, 1)
    reference = dt.date(2026, 7, 8)
    followups = [dt.date(2024, 6, 1)]
    assert is_lost("high", last_lab, reference, followup_dates=followups) is False


def test_grey_zone_with_high_ml_risk_can_be_lost():
    last_lab = dt.date(2024, 1, 1)
    reference = dt.date(2026, 7, 8)
    assert is_lost("grey", last_lab, reference, ml_risk=0.9) is True


def test_no_last_lab_date_is_never_lost():
    assert is_lost("high", None, dt.date(2026, 7, 8)) is False


def test_rank_worklist_sorts_by_risk_desc():
    patients = [
        {"patient_id": 1, "risk": 1.5, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
        {"patient_id": 2, "risk": 3.5, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
        {"patient_id": 3, "risk": 2.5, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
    ]
    ranked = rank_worklist(patients)
    assert [p["patient_id"] for p in ranked] == [2, 3, 1]


def test_rank_worklist_breaks_ties_by_recency_then_completeness():
    patients = [
        {"patient_id": 1, "risk": 3.0, "last_lab_date": dt.date(2026, 3, 1), "completeness": 1.0},
        {"patient_id": 2, "risk": 3.0, "last_lab_date": dt.date(2026, 1, 1), "completeness": 0.5},
        {"patient_id": 3, "risk": 3.0, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
    ]
    ranked = rank_worklist(patients)
    # most overdue (earliest last_lab_date) first; among ties, more complete data first
    assert [p["patient_id"] for p in ranked] == [3, 2, 1]


def test_rank_worklist_handles_missing_risk():
    patients = [
        {"patient_id": 1, "risk": None, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
        {"patient_id": 2, "risk": 1.0, "last_lab_date": dt.date(2026, 1, 1), "completeness": 1.0},
    ]
    ranked = rank_worklist(patients)
    assert [p["patient_id"] for p in ranked] == [2, 1]
