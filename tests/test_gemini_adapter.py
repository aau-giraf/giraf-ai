import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.image.gemini import _ASPECT_RATIO_MAP, GeminiImageAdapter
from core.exceptions import ProviderError
from core.types import ImageGenerationRequest


@pytest.fixture
def adapter() -> GeminiImageAdapter:
    return GeminiImageAdapter(api_key="test-key")


def _gemini_response(image_bytes: bytes = b"fake-png") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": base64.b64encode(image_bytes).decode(),
                                }
                            }
                        ]
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://example.com"),
    )


async def test_generate_returns_image(adapter: GeminiImageAdapter) -> None:
    req = ImageGenerationRequest(prompt="apple")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _gemini_response(b"image-data")
        result = await adapter.generate(req)

    assert result.image_data == b"image-data"
    assert result.format == "png"
    assert result.provider == "gemini"
    assert result.prompt_used == "apple"


async def test_generate_sends_correct_payload(adapter: GeminiImageAdapter) -> None:
    req = ImageGenerationRequest(prompt="cat", size=(1024, 768))
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _gemini_response()
        await adapter.generate(req)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["contents"][0]["parts"][0]["text"] == "cat"
    assert payload["generationConfig"]["imageConfig"]["aspectRatio"] == "4:3"


async def test_generate_http_error_raises_provider_error(adapter: GeminiImageAdapter) -> None:
    req = ImageGenerationRequest(prompt="dog")
    error_resp = httpx.Response(
        429,
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp
        with pytest.raises(ProviderError, match="gemini"):
            await adapter.generate(req)


async def test_generate_no_image_in_response_raises(adapter: GeminiImageAdapter) -> None:
    req = ImageGenerationRequest(prompt="tree")
    resp = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": "no image"}]}}]},
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp
        with pytest.raises(ProviderError, match="No image in response"):
            await adapter.generate(req)


async def test_health_check_success(adapter: GeminiImageAdapter) -> None:
    resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = resp
        assert await adapter.health_check() is True


async def test_health_check_failure(adapter: GeminiImageAdapter) -> None:
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("timeout")
        assert await adapter.health_check() is False


def test_aspect_ratio_map_defaults_to_square() -> None:
    assert (512, 512) in _ASPECT_RATIO_MAP
    assert _ASPECT_RATIO_MAP[(512, 512)] == "1:1"
    # Unknown sizes should not be in the map
    assert (999, 999) not in _ASPECT_RATIO_MAP
