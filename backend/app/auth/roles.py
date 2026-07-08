from enum import StrEnum

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


class Role(StrEnum):
    doctor = "doctor"
    coordinator = "coordinator"
    admin = "admin"
    viewer = "viewer"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.username == "doctor").first()
    if not user:
        raise HTTPException(status_code=401, detail="Demo user not found")
    return user


def require_role(*allowed: Role):
    allowed_values = {role.value for role in allowed}

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_values:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
