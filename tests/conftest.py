import sys
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings  # noqa: E402


@pytest.fixture(autouse=True)
def _mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret")
    monkeypatch.setattr(settings, "image_provider", "mock")
    monkeypatch.setattr(settings, "tts_provider", "mock")


@pytest.fixture
def auth_header():
    token = jwt.encode(
        {"sub": "1", "org_roles": {"1": "member"}},
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    from main import app

    with TestClient(app) as c:
        yield c
