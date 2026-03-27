from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from core.exceptions import ProviderError


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["providers"]["image"] is True
    assert data["providers"]["tts"] is True


def test_generate_image_requires_auth(client: TestClient) -> None:
    resp = client.post("/api/v1/generate/image", json={"prompt": "test"})
    assert resp.status_code == 401


def test_generate_image(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/generate/image",
        json={"prompt": "lasagna"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_base64"]
    assert data["format"] == "png"
    assert data["provider"] == "mock"
    assert "prompt_used" not in data


def test_generate_image_prompt_too_long(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/generate/image",
        json={"prompt": "a" * 501},
        headers=auth_header,
    )
    assert resp.status_code == 422


def test_generate_image_prompt_empty(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/generate/image",
        json={"prompt": ""},
        headers=auth_header,
    )
    assert resp.status_code == 422


def test_tts_text_too_long(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/tts",
        json={"text": "a" * 2001, "language": "da"},
        headers=auth_header,
    )
    assert resp.status_code == 422


def test_tts_synthesize(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.post(
        "/api/v1/tts",
        json={"text": "Lasagne", "language": "da"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["audio_base64"]
    assert data["provider"] == "mock"


def test_tts_voices(client: TestClient, auth_header: dict[str, str]) -> None:
    resp = client.get("/api/v1/tts/voices?language=da", headers=auth_header)
    assert resp.status_code == 200
    voices = resp.json()
    assert len(voices) >= 1


def test_tts_requires_auth(client: TestClient) -> None:
    resp = client.post("/api/v1/tts", json={"text": "test"})
    assert resp.status_code == 401


def test_generate_image_provider_error_returns_502(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    with patch(
        "services.image_service.ImageService.generate",
        new_callable=AsyncMock,
        side_effect=ProviderError("test", "boom"),
    ):
        resp = client.post(
            "/api/v1/generate/image",
            json={"prompt": "fail"},
            headers=auth_header,
        )
    assert resp.status_code == 502
    assert "boom" in resp.json()["detail"]


def test_docs_disabled_by_default(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_image_rate_limit_returns_429(client: TestClient, auth_header: dict[str, str]) -> None:
    for _ in range(10):
        client.post(
            "/api/v1/generate/image",
            json={"prompt": "test"},
            headers=auth_header,
        )
    resp = client.post(
        "/api/v1/generate/image",
        json={"prompt": "one too many"},
        headers=auth_header,
    )
    assert resp.status_code == 429


def test_tts_provider_error_returns_502(client: TestClient, auth_header: dict[str, str]) -> None:
    with patch(
        "services.tts_service.TTSService.synthesize",
        new_callable=AsyncMock,
        side_effect=ProviderError("test", "boom"),
    ):
        resp = client.post(
            "/api/v1/tts",
            json={"text": "fail", "language": "da"},
            headers=auth_header,
        )
    assert resp.status_code == 502
    assert "boom" in resp.json()["detail"]
