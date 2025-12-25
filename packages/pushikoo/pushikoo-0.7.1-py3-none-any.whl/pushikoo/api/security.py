from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from pushikoo.util.setting import settings


_bearer_scheme = HTTPBearer(auto_error=False)


def _as_key_list(value: Optional[object]) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [i.strip() for i in value.split(",") if i.strip()]
    if isinstance(value, Sequence):
        # Convert e.g. list/tuple to trimmed strings
        return [str(i).strip() for i in value if str(i).strip()]
    return []


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if settings.ENVIRONMENT == "local":
        return "whatever"
    if (
        credentials is None
        or not credentials.scheme
        or credentials.scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    valid_keys = settings.SECRET_TOKENS

    if token in valid_keys:
        return token

    if settings.SSO_CLIENT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SSO_CLIENT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            sub = payload.get("sub")
            if not sub:
                raise InvalidTokenError("missing sub")
            return str(sub)
        except InvalidTokenError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire_minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})

    secret = settings.SSO_CLIENT_SECRET or "dev-secret"
    return jwt.encode(to_encode, secret, algorithm="HS256")
