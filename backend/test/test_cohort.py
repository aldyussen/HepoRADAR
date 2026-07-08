import io

CSV_CONTENT = """patient_id,age,sex,date,AST,ALT,Platelets
P1,30,F,2026-06-01,20,20,250
P2,45,M,2026-06-01,40,35,180
P3,70,M,2020-01-01,120,30,60
P4,65,F,2026-06-01,100,40,70
""".strip()


def _ingest_sample(client):
    files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 200
    return response.json()


def test_ingest_report_counts_patients_and_labs(client):
    report = _ingest_sample(client)
    assert report["patients_ingested"] == 4
    assert report["labs_ingested"] == 12  # 4 patients x 3 analytes
    assert report["rows_rejected"] == 0


def test_scan_produces_zone_summary(client):
    _ingest_sample(client)
    response = client.post("/cohort/scan")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 4
    assert summary["low"] == 1
    assert summary["grey"] == 1
    assert summary["high"] == 2
    assert summary["lost_count"] == 1


def test_worklist_is_non_empty_and_smaller_than_full_cohort(client):
    _ingest_sample(client)
    client.post("/cohort/scan")

    response = client.get("/cohort/worklist")
    assert response.status_code == 200
    worklist = response.json()

    assert worklist["total"] > 0
    assert worklist["total"] < 4
    assert all(item["is_lost"] for item in worklist["items"])
    assert all(item["zone"] == "high" for item in worklist["items"])


def test_worklist_zone_filter(client):
    _ingest_sample(client)
    client.post("/cohort/scan")

    response = client.get("/cohort/worklist", params={"zone": "low"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_patient_card_returns_labs_and_scores(client):
    _ingest_sample(client)
    client.post("/cohort/scan")

    patients_response = client.get("/cohort/worklist")
    patient_id = patients_response.json()["items"][0]["patient_id"]

    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    card = response.json()
    assert len(card["labs"]) == 3
    assert len(card["scores"]) == 1
    assert card["scores"][0]["zone"] == "high"


def test_patient_card_404_for_unknown_patient(client):
    response = client.get("/patients/999999")
    assert response.status_code == 404


def test_scan_only_assigns_ml_risk_to_grey_zone_patients(client, monkeypatch, tmp_path):
    from ml.src.export import export_placeholder

    from app.services import ml_infer

    paths = export_placeholder(tmp_path / "artifacts")
    monkeypatch.setattr(ml_infer.settings, "model_path", str(paths["model"]))
    monkeypatch.setattr(ml_infer.settings, "feature_order_path", str(paths["feature_order"]))

    _ingest_sample(client)
    client.post("/cohort/scan")

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
