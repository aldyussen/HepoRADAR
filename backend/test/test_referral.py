import io

# age=45, ast=40, alt=35, plt=180 -> fib4 ~= 1.69 -> grey zone
CSV_CONTENT = """patient_id,age,sex,date,AST,ALT,Platelets,Bilirubin,Albumin
P1,45,M,2026-06-01,40,35,180,0.9,4.0
""".strip()


def _ingest_and_scan(client, headers, mrn: str = "P1") -> int:
    files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.replace("P1", mrn).encode()), "text/csv")}
    assert client.post("/ingest", files=files, headers=headers).status_code == 200
    assert client.post("/cohort/scan", headers=headers).status_code == 200

    from app.db.session import SessionLocal
    from app.models.patient import Patient

    db = SessionLocal()
    try:
        return db.query(Patient).filter(Patient.mrn == mrn).one().id
    finally:
        db.close()


def _assert_valid_referral_body(body: dict) -> None:
    assert body["patient_id"] is not None
    assert body["status"] in ("draft", "template_fallback")
    assert body["source"] in ("llm", "template")
    assert body["content"].strip() != ""
    assert "Patient Summary:" in body["content"]
    assert "Risk Scores:" in body["content"]
    assert "Key Drivers:" in body["content"]
    assert "Recommendation:" in body["content"]


def test_referral_llm_success_is_used_and_persisted(client, doctor_headers, monkeypatch):
    patient_id = _ingest_and_scan(client, doctor_headers, "P1")

    monkeypatch.setattr(
        "app.services.llm_client.generate_referral",
        lambda *a, **k: "Patient Summary:\nfoo\n\nRisk Scores:\nbar\n\nKey Drivers:\nbaz\n\nRecommendation:\nqux",
    )

    response = client.post(f"/patients/{patient_id}/referral", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "llm"
    assert body["status"] == "draft"
    assert "qux" in body["content"]
    _assert_valid_referral_body(body)

    from app.db.session import SessionLocal
    from app.models.referral import Referral

    db = SessionLocal()
    try:
        stored = db.query(Referral).filter(Referral.patient_id == patient_id).one()
        assert stored.source == "llm"
        assert stored.content == body["content"]
    finally:
        db.close()


def test_referral_falls_back_to_template_when_llm_raises(client, doctor_headers, monkeypatch):
    patient_id = _ingest_and_scan(client, doctor_headers, "P2")

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr("app.services.llm_client.generate_referral", _boom)

    response = client.post(f"/patients/{patient_id}/referral", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "template"
    assert body["status"] == "template_fallback"
    _assert_valid_referral_body(body)
    # scores + factors must actually be embedded in the fallback content
    assert "fib4" in body["content"]
    assert "zone" in body["content"]


def test_referral_template_fallback_alone_without_any_llm_mocking(client, doctor_headers, monkeypatch):
    """No gemini_api_key configured in tests -> llm_client raises naturally,
    so this exercises the template path with zero mocking of generate_referral.
    """
    from app.config import settings
    monkeypatch.setattr(settings, "gemini_api_key", None)
    
    patient_id = _ingest_and_scan(client, doctor_headers, "P3")

    response = client.post(f"/patients/{patient_id}/referral", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "template"
    assert body["status"] == "template_fallback"
    _assert_valid_referral_body(body)


def test_referral_endpoint_allows_admin(client, doctor_headers, admin_headers):
    patient_id = _ingest_and_scan(client, doctor_headers, "P4")

    response = client.post(f"/patients/{patient_id}/referral", headers=admin_headers)
    assert response.status_code == 200


def test_referral_endpoint_forbidden_for_viewer(client, doctor_headers, viewer_headers):
    patient_id = _ingest_and_scan(client, doctor_headers, "P5")

    response = client.post(f"/patients/{patient_id}/referral", headers=viewer_headers)
    assert response.status_code == 403


def test_referral_endpoint_forbidden_for_coordinator(client, doctor_headers, coordinator_headers):
    patient_id = _ingest_and_scan(client, doctor_headers, "P6")

    response = client.post(f"/patients/{patient_id}/referral", headers=coordinator_headers)
    assert response.status_code == 403


def test_referral_endpoint_requires_authentication(client, doctor_headers):
    patient_id = _ingest_and_scan(client, doctor_headers, "P7")

    response = client.post(f"/patients/{patient_id}/referral")
    assert response.status_code == 401


def test_referral_endpoint_404_for_unknown_patient(client, doctor_headers):
    response = client.post("/patients/999999/referral", headers=doctor_headers)
    assert response.status_code == 404


def test_referral_with_no_complete_labs_still_produces_valid_referral(client, doctor_headers):
    files = {"file": ("labs.csv", io.BytesIO(b"patient_id,age,sex,date,AST\nP9,50,M,2026-01-01,40\n"), "text/csv")}
    assert client.post("/ingest", files=files, headers=doctor_headers).status_code == 200

    from app.db.session import SessionLocal
    from app.models.patient import Patient

    db = SessionLocal()
    try:
        patient_id = db.query(Patient).filter(Patient.mrn == "P9").one().id
    finally:
        db.close()

    response = client.post(f"/patients/{patient_id}/referral", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()
    _assert_valid_referral_body(body)
