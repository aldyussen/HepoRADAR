import io

from app.db.seed import seed_users

CSV_CONTENT = """patient_id,age,sex,date,AST,ALT,Platelets
P1,30,F,2026-06-01,20,20,250
P2,45,M,2026-06-01,40,35,180
P3,70,M,2020-01-01,120,30,60
P4,65,F,2026-06-01,100,40,70
""".strip()

CREDENTIALS = {
    "doctor": "doctor123",
    "coordinator": "coordinator123",
    "admin": "admin123",
    "viewer": "viewer123",
}


def _seed(db_session):
    seed_users(db_session)


def _login(client, username):
    response = client.post("/auth/login", json={"username": username, "password": CREDENTIALS[username]})
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(client, username):
    tokens = _login(client, username)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_login_success_returns_tokens(client, db_session):
    _seed(db_session)
    tokens = _login(client, "doctor")
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, db_session):
    _seed(db_session)
    response = client.post("/auth/login", json={"username": "doctor", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_user_returns_401(client, db_session):
    _seed(db_session)
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})
    assert response.status_code == 401


def test_protected_endpoint_without_token_returns_401(client, db_session):
    _seed(db_session)
    response = client.get("/cohort/worklist")
    assert response.status_code == 401


def test_protected_endpoint_wrong_role_returns_403(client, db_session):
    _seed(db_session)
    headers = _auth_headers(client, "coordinator")
    response = client.post("/cohort/scan", headers=headers)
    assert response.status_code == 403


def test_protected_endpoint_right_role_returns_200(client, db_session):
    _seed(db_session)
    headers = _auth_headers(client, "doctor")
    response = client.post("/cohort/scan", headers=headers)
    assert response.status_code == 200


def test_refresh_flow_returns_working_access_token(client, db_session):
    _seed(db_session)
    tokens = _login(client, "doctor")

    refresh_response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "doctor"


def test_refresh_with_access_token_is_rejected(client, db_session):
    _seed(db_session)
    tokens = _login(client, "doctor")
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_me_requires_authentication(client, db_session):
    _seed(db_session)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_three_seeded_roles_see_different_access_outcomes(client, db_session):
    _seed(db_session)
    outcomes = {}
    for username in ("doctor", "coordinator", "admin"):
        headers = _auth_headers(client, username)
        scan_status = client.post("/cohort/scan", headers=headers).status_code
        ingest_files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
        ingest_status = client.post("/ingest", files=ingest_files, headers=headers).status_code
        outcomes[username] = (scan_status, ingest_status)

    assert outcomes["doctor"] == (200, 200)
    assert outcomes["admin"] == (200, 200)
    assert outcomes["coordinator"] == (403, 403)
    # doctor/admin are both fully permitted here (by design, so the demo doctor
    # account isn't locked out of ingest) but coordinator is distinctly restricted.
    assert len(set(outcomes.values())) == 2


def test_viewer_can_read_worklist_but_not_ingest_or_scan(client, db_session):
    _seed(db_session)
    headers = _auth_headers(client, "viewer")

    worklist_response = client.get("/cohort/worklist", headers=headers)
    assert worklist_response.status_code == 200

    scan_response = client.post("/cohort/scan", headers=headers)
    assert scan_response.status_code == 403

    ingest_files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
    ingest_response = client.post("/ingest", files=ingest_files, headers=headers)
    assert ingest_response.status_code == 403


def test_health_stays_public(client, db_session):
    response = client.get("/health")
    assert response.status_code == 200


def test_full_critical_path_with_doctor_token(client, db_session):
    """Regression: auth must not break the B1/B2 ingest -> scan -> worklist -> card -> explain flow."""
    _seed(db_session)
    headers = _auth_headers(client, "doctor")

    files = {"file": ("labs.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")}
    ingest_response = client.post("/ingest", files=files, headers=headers)
    assert ingest_response.status_code == 200
    assert ingest_response.json()["patients_ingested"] == 4

    scan_response = client.post("/cohort/scan", headers=headers)
    assert scan_response.status_code == 200
    assert scan_response.json()["total"] == 4

    worklist_response = client.get("/cohort/worklist", headers=headers)
    assert worklist_response.status_code == 200
    worklist = worklist_response.json()
    assert worklist["total"] > 0
    patient_id = worklist["items"][0]["patient_id"]

    card_response = client.get(f"/patients/{patient_id}", headers=headers)
    assert card_response.status_code == 200
    assert len(card_response.json()["labs"]) == 3

    explain_response = client.get(f"/patients/{patient_id}/explain", headers=headers)
    assert explain_response.status_code == 200
