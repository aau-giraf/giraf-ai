from collections.abc import Generator

import jwt
import pytest
from fastapi.testclient import TestClient

from config.settings import settings

_TEST_SECRET = "test-secret-that-is-at-least-32-bytes-long"


@pytest.fixture(autouse=True)
def _mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", _TEST_SECRET)
    monkeypatch.setattr(settings, "image_provider", "mock")
    monkeypatch.setattr(settings, "tts_provider", "mock")


@pytest.fixture
def auth_header() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "1", "org_roles": {"1": "member"}},
        _TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> Generator[TestClient]:
    from main import app

    with TestClient(app) as c:
        yield c
