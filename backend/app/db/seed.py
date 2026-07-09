import datetime as dt
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.patient import Patient
from app.services.etl import ingest_csv
from app.services.cohort_scan import run_cohort_scan
from app.models.cascade_event import CascadeEvent

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

def seed_cascade_events(db: Session) -> None:
    """Seed a realistic HCV cascade spread onto existing patients so the funnel
    steps down and the reflex flag has patients to surface. Idempotent."""
    if db.query(CascadeEvent).count() > 0:
        return

    patients = db.query(Patient).order_by(Patient.id).all()
    if len(patients) < 10:
        print(f"Only {len(patients)} patients seeded; need >=10 for a full cascade demo. Seeding what fits.")
    if not patients:
        print("No patients to attach cascade events to; run seed_patients first.")
        return

    today = dt.date.today()

    def d(days_ago: int) -> dt.date:
        return today - dt.timedelta(days=days_ago)

    # Each entry: list of (stage, event_date) applied in order to one patient.
    # Funnel: 10 screened -> 6 anti_hcv+ -> 3 rna_tested -> 2 treated -> 1 svr.
    # The 3 anti_hcv_positive patients with NO rna/treated/svr are the reflex-flag stars.
    cascade_plan: list[list[tuple[str, int]]] = [
        # fully progressed to cure (1)
        [("screened", 400), ("anti_hcv_positive", 380), ("rna_tested", 360), ("treated", 300), ("svr", 120)],
        # treated, awaiting SVR confirmation (1)
        [("screened", 350), ("anti_hcv_positive", 330), ("rna_tested", 310), ("treated", 200)],
        # RNA-tested, not yet treated (1)
        [("screened", 300), ("anti_hcv_positive", 280), ("rna_tested", 260)],
        # REFLEX-FLAGGED: anti-HCV positive, never followed up with RNA (3) -- the demo stars
        [("screened", 250), ("anti_hcv_positive", 230)],
        [("screened", 240), ("anti_hcv_positive", 220)],
        [("screened", 210), ("anti_hcv_positive", 190)],
        # screened only, negative / no further action (4)
        [("screened", 180)],
        [("screened", 150)],
        [("screened", 120)],
        [("screened", 90)],
    ]

    attached = 0
    flagged = 0
    for patient, stages in zip(patients, cascade_plan):
        for stage, days_ago in stages:
            db.add(CascadeEvent(patient_id=patient.id, stage=stage, event_date=d(days_ago)))
        reached = {s for s, _ in stages}
        if "anti_hcv_positive" in reached and not reached & {"rna_tested", "treated", "svr"}:
            flagged += 1
        attached += 1

    db.commit()
    print(f"Seeded cascade events on {attached} patients ({flagged} reflex-flagged).")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_patients(db)
        print("Running automatic cohort scan...")
        summary = run_cohort_scan(db)
        print(f"Scan complete: total={summary.total}, lost={summary.lost_count}")
        seed_cascade_events(db)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

