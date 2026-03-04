import json
from typing import Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings
from core.exceptions import AuthenticationError, MalformedClaimError

_bearer = HTTPBearer()


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(str(e)) from e


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict[str, Any]:
    payload = decode_jwt(credentials.credentials)
    return payload


def get_org_roles(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    raw = user.get("org_roles", {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            raise MalformedClaimError("Malformed org_roles claim") from e
    result: dict[str, str] = raw
    return result
