import io

from ml.src.export import export_placeholder

# age=45, ast=40, alt=35, plt=180 -> fib4 ~= 1.69 -> grey zone
CSV_CONTENT = """patient_id,age,sex,date,AST,ALT,Platelets,Bilirubin,Albumin
P1,45,M,2026-06-01,40,35,180,0.9,4.0
""".strip()


def _ingest_and_scan(client, headers):
    files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
    assert client.post("/ingest", files=files, headers=headers).status_code == 200
    assert client.post("/cohort/scan", headers=headers).status_code == 200

    from app.db.session import SessionLocal
    from app.models.patient import Patient

    db = SessionLocal()
    try:
        return db.query(Patient).filter(Patient.mrn == "P1").one().id
    finally:
        db.close()


def test_explain_without_explainer_returns_rule_based_reason(client, doctor_headers):
    patient_id = _ingest_and_scan(client, doctor_headers)

    response = client.get(f"/patients/{patient_id}/explain", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["base_value"] is None
    assert isinstance(body["factors"], list)


def test_explain_with_explainer_returns_shap_factors(client, doctor_headers, monkeypatch, tmp_path):
    from app.services import ml_infer

    paths = export_placeholder(tmp_path / "artifacts")
    monkeypatch.setattr(ml_infer.settings, "model_path", str(paths["model"]))
    monkeypatch.setattr(ml_infer.settings, "feature_order_path", str(paths["feature_order"]))
    monkeypatch.setattr(ml_infer.settings, "shap_explainer_path", str(paths["explainer"]))

    patient_id = _ingest_and_scan(client, doctor_headers)

    response = client.get(f"/patients/{patient_id}/explain", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["base_value"] == 0.3
    assert len(body["factors"]) <= 3


def test_explain_404_for_unknown_patient(client, doctor_headers):
    response = client.get("/patients/999999/explain", headers=doctor_headers)
    assert response.status_code == 404


def test_explain_empty_payload_when_no_complete_labs(client, doctor_headers):
    files = {"file": ("labs.csv", io.BytesIO(b"patient_id,age,sex,date,AST\nP9,50,M,2026-01-01,40\n"), "text/csv")}
    assert client.post("/ingest", files=files, headers=doctor_headers).status_code == 200

    from app.db.session import SessionLocal
    from app.models.patient import Patient

    db = SessionLocal()
    try:
        patient_id = db.query(Patient).filter(Patient.mrn == "P9").one().id
    finally:
        db.close()

    response = client.get(f"/patients/{patient_id}/explain", headers=doctor_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["factors"] == []
    assert body["prediction"] is None
