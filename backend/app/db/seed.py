from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {"username": "doctor", "password": "doctor123", "role": "doctor"},
    {"username": "coordinator", "password": "coordinator123", "role": "coordinator"},
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "viewer", "password": "viewer123", "role": "viewer"},
]


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


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
