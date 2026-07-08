import io

CSV_CONTENT = """patient_id,age,sex,date,AST,ALT,Platelets
P1,36,F,2026-06-01,20,20,250
P2,45,M,2026-06-01,40,35,180
P3,70,M,2020-01-01,120,30,60
P4,65,F,2026-06-01,100,40,70
""".strip()


def _ingest_sample(client, headers):
    files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
    response = client.post("/ingest", files=files, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_ingest_report_counts_patients_and_labs(client, doctor_headers):
    report = _ingest_sample(client, doctor_headers)
    assert report["patients_ingested"] == 4
    assert report["labs_ingested"] == 12  # 4 patients x 3 analytes
    assert report["rows_rejected"] == 0


def test_scan_produces_zone_summary(client, doctor_headers):
    _ingest_sample(client, doctor_headers)
    response = client.post("/cohort/scan", headers=doctor_headers)
    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 4
    assert summary["low"] == 1
    assert summary["grey"] == 1
    assert summary["high"] == 2
    assert summary["lost_count"] == 1


def test_worklist_is_non_empty_and_smaller_than_full_cohort(client, doctor_headers):
    _ingest_sample(client, doctor_headers)
    client.post("/cohort/scan", headers=doctor_headers)

    response = client.get("/cohort/worklist", headers=doctor_headers)
    assert response.status_code == 200
    worklist = response.json()

    assert worklist["total"] > 0
    assert worklist["total"] < 4
    assert all(item["is_lost"] for item in worklist["items"])
    assert all(item["zone"] == "high" for item in worklist["items"])


def test_worklist_zone_filter(client, doctor_headers):
    _ingest_sample(client, doctor_headers)
    client.post("/cohort/scan", headers=doctor_headers)

    response = client.get("/cohort/worklist", params={"zone": "low"}, headers=doctor_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_patient_card_returns_labs_and_scores(client, doctor_headers):
    _ingest_sample(client, doctor_headers)
    client.post("/cohort/scan", headers=doctor_headers)

    patients_response = client.get("/cohort/worklist", headers=doctor_headers)
    patient_id = patients_response.json()["items"][0]["patient_id"]

    response = client.get(f"/patients/{patient_id}", headers=doctor_headers)
    assert response.status_code == 200
    card = response.json()
    assert len(card["labs"]) == 3
    assert len(card["scores"]) == 1
    assert card["scores"][0]["zone"] == "high"


def test_patient_card_404_for_unknown_patient(client, doctor_headers):
    response = client.get("/patients/999999", headers=doctor_headers)
    assert response.status_code == 404


def test_scan_only_assigns_ml_risk_to_grey_zone_patients(client, doctor_headers, monkeypatch, tmp_path):
    from ml.src.export import export_placeholder

    from app.services import ml_infer

    paths = export_placeholder(tmp_path / "artifacts")
    monkeypatch.setattr(ml_infer.settings, "model_path", str(paths["model"]))
    monkeypatch.setattr(ml_infer.settings, "feature_order_path", str(paths["feature_order"]))

    _ingest_sample(client, doctor_headers)
    client.post("/cohort/scan", headers=doctor_headers)

    from app.db.session import SessionLocal
    from app.models.score import Score

    db = SessionLocal()
    try:
        scores = db.query(Score).all()
    finally:
        db.close()

    assert any(s.zone == "grey" for s in scores)
    for score in scores:
        if score.zone == "grey":
            assert score.ml_risk is not None
        else:
            assert score.ml_risk is None
