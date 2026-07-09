def test_app_imports_and_boots():
    """Regression guard: a broken router import (e.g. app/api/referral.py importing a
    name that doesn't exist in cascade_logic) crashes `uvicorn app.main:app` at startup
    but was previously invisible to the suite. Import app.main fresh here so a bad
    import fails this test the same way it fails a real server boot."""
    import importlib

    import app.main

    importlib.reload(app.main)

    assert app.main.app is not None


def test_health_endpoint_via_fresh_app(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
