from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.patient import Patient
from app.services.etl import ingest_csv
from app.services.cohort_scan import run_cohort_scan

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {"username": "doctor", "password": "doctor123", "role": "doctor"},
    {"username": "coordinator", "password": "coordinator123", "role": "coordinator"},
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "viewer", "password": "viewer123", "role": "viewer"},
]

SEED_CSV = Path(__file__).parent / "seed_data" / "patients.csv"


def seed_users(db: Session) -> None:
    for spec in SEED_USERS:
        existing = db.query(User).filter(User.username == spec["username"]).one_or_none()
        if existing is not None:
            continue
        db.add(
            User(
                username=spec["username"],
                password_hash=pwd_context.hash(spec["password"]),
                role=spec["role"],
            )
        )
    db.commit()


def seed_patients(db: Session) -> None:
    if db.query(Patient).count() > 0:
        return
    if not SEED_CSV.exists():
        print(f"Seed CSV not found at {SEED_CSV}")
        return
    print("Seeding patients and labs from CSV...")
    with open(SEED_CSV, encoding="utf-8") as f:
        ingest_csv(f, db)
    print("Ingestion completed successfully.")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_patients(db)
        print("Running automatic cohort scan...")
        summary = run_cohort_scan(db)
        print(f"Scan complete: total={summary.total}, lost={summary.lost_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

