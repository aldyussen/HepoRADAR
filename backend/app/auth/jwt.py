import datetime as dt

import jwt

from app.config import settings


def _encode(claims: dict, expires_delta: dt.timedelta) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {**claims, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(sub: str, role: str) -> str:
    return _encode(
        {"sub": sub, "role": role, "type": "access"},
        dt.timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(sub: str) -> str:
    return _encode(
        {"sub": sub, "type": "refresh"},
        dt.timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
