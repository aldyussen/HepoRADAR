import os
import sys
import tempfile
from pathlib import Path

_TEST_DB_DIR = tempfile.mkdtemp(prefix="heparadar_test_")
os.environ["HEPARADAR_DATABASE_URL"] = "sqlite:///" + os.path.join(_TEST_DB_DIR, "test.db")

# backend/test/conftest.py -> repo root (sibling of `ml/`), so tests can `import ml.src.export`
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from app import models  # noqa: E402,F401  (registers ORM classes on Base.metadata)
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
