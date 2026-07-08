import os
import tempfile

_TEST_DB_DIR = tempfile.mkdtemp(prefix="heparadar_test_")
os.environ["HEPARADAR_DATABASE_URL"] = "sqlite:///" + os.path.join(_TEST_DB_DIR, "test.db")

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
