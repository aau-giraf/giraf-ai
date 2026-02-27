import json
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings

_bearer = HTTPBearer()


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict[str, Any]:
    payload = decode_jwt(credentials.credentials)
    return payload


def get_org_roles(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    raw = user.get("org_roles", {})
    if isinstance(raw, str):
        raw = json.loads(raw)
    result: dict[str, str] = raw
    return result
