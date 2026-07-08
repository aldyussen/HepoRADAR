import datetime as dt

from app.models.cascade_event import CascadeEvent
from app.models.patient import Patient
from app.services.cascade_logic import CASCADE_STAGES, cascade_funnel, hcv_stage, reflex_flag


def test_hcv_stage_empty_or_none_is_indeterminate():
    assert hcv_stage([]) == "indeterminate"
    assert hcv_stage(None) == "indeterminate"


def test_hcv_stage_ignores_unrecognized_values():
    assert hcv_stage(["not_a_real_stage"]) == "indeterminate"


def test_hcv_stage_picks_furthest_stage_reached_regardless_of_order():
    assert hcv_stage(["screened"]) == "screened"
    assert hcv_stage(["screened", "anti_hcv_positive"]) == "anti_hcv_positive"
    assert hcv_stage(["screened", "anti_hcv_positive", "rna_tested", "treated", "svr"]) == "svr"
    assert hcv_stage(["svr", "screened", "rna_tested"]) == "svr"


def test_reflex_flag_true_for_positive_screen_without_rna():
    assert reflex_flag(["screened", "anti_hcv_positive"]) is True


def test_reflex_flag_false_when_rna_test_exists():
    assert reflex_flag(["screened", "anti_hcv_positive", "rna_tested"]) is False


def test_reflex_flag_false_when_treated_or_svr_exists_even_without_explicit_rna_event():
    assert reflex_flag(["screened", "anti_hcv_positive", "treated"]) is False
    assert reflex_flag(["screened", "anti_hcv_positive", "svr"]) is False


def test_reflex_flag_false_for_negative_screen():
    assert reflex_flag(["screened"]) is False


def test_reflex_flag_false_for_no_data():
    assert reflex_flag([]) is False
    assert reflex_flag(None) is False


def test_cascade_funnel_counts_sum_correctly_and_are_monotonic():
    cohort = [
        ["screened"],
        ["screened", "anti_hcv_positive"],
        ["screened", "anti_hcv_positive", "rna_tested"],
        ["screened", "anti_hcv_positive", "rna_tested", "treated"],
        ["screened", "anti_hcv_positive", "rna_tested", "treated", "svr"],
        [],  # indeterminate -- no cascade_event rows at all
    ]
    funnel = cascade_funnel(cohort)

    assert funnel["screened"] == 5
    assert funnel["anti_hcv_positive"] == 4
    assert funnel["rna_tested"] == 3
    assert funnel["treated"] == 2
    assert funnel["svr"] == 1

    counts = [funnel[stage] for stage in CASCADE_STAGES]
    assert counts == sorted(counts, reverse=True)


def _seed_patient_with_stages(db_session, mrn: str, stages: list[str]) -> Patient:
    patient = Patient(mrn=mrn, age=40, sex=1)
    db_session.add(patient)
    db_session.flush()
    for stage in stages:
        db_session.add(CascadeEvent(patient_id=patient.id, stage=stage, event_date=dt.date(2026, 1, 1)))
    db_session.commit()
    return patient


def test_hcv_cascade_endpoint_returns_funnel_and_reflex_list_for_coordinator(
    client, db_session, coordinator_headers
):
    _seed_patient_with_stages(db_session, "P1", ["screened", "anti_hcv_positive"])
    _seed_patient_with_stages(db_session, "P2", ["screened", "anti_hcv_positive", "rna_tested"])
    _seed_patient_with_stages(db_session, "P3", [])

    response = client.get("/cascade/hcv", headers=coordinator_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["funnel"]["screened"] == 2
    assert body["funnel"]["anti_hcv_positive"] == 2
    assert body["funnel"]["rna_tested"] == 1

    reflex_mrns = {p["mrn"] for p in body["reflex_flagged"]}
    assert reflex_mrns == {"P1"}


def test_hcv_cascade_endpoint_allows_admin(client, db_session, admin_headers):
    response = client.get("/cascade/hcv", headers=admin_headers)
    assert response.status_code == 200


def test_hcv_cascade_endpoint_forbidden_for_doctor(client, db_session, doctor_headers):
    response = client.get("/cascade/hcv", headers=doctor_headers)
    assert response.status_code == 403


def test_hcv_cascade_endpoint_forbidden_for_viewer(client, db_session, viewer_headers):
    response = client.get("/cascade/hcv", headers=viewer_headers)
    assert response.status_code == 403


def test_hcv_cascade_endpoint_requires_authentication(client, db_session):
    response = client.get("/cascade/hcv")
    assert response.status_code == 401
