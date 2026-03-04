import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.image.openai_dalle import OpenAIDalleAdapter
from core.exceptions import ProviderError
from core.types import ImageGenerationRequest


@pytest.fixture
def adapter() -> OpenAIDalleAdapter:
    return OpenAIDalleAdapter(api_key="test-key")


def _openai_response(image_bytes: bytes = b"fake-png") -> httpx.Response:
    return httpx.Response(
        200,
        json={"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]},
        request=httpx.Request("POST", "https://example.com"),
    )


async def test_generate_returns_image(adapter: OpenAIDalleAdapter) -> None:
    req = ImageGenerationRequest(prompt="apple")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _openai_response(b"image-data")
        result = await adapter.generate(req)

    assert result.image_data == b"image-data"
    assert result.format == "png"
    assert result.provider == "openai_dalle"
    assert result.prompt_used == "apple"


async def test_generate_sends_correct_payload(adapter: OpenAIDalleAdapter) -> None:
    req = ImageGenerationRequest(prompt="cat", size=(512, 512))
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _openai_response()
        await adapter.generate(req)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["prompt"] == "cat"
    assert payload["size"] == "512x512"
    assert payload["response_format"] == "b64_json"


async def test_generate_http_error_raises_provider_error(adapter: OpenAIDalleAdapter) -> None:
    req = ImageGenerationRequest(prompt="dog")
    error_resp = httpx.Response(
        429,
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp
        with pytest.raises(ProviderError, match="openai_dalle"):
            await adapter.generate(req)


async def test_generate_malformed_response_raises(adapter: OpenAIDalleAdapter) -> None:
    req = ImageGenerationRequest(prompt="tree")
    resp = httpx.Response(
        200,
        json={"data": []},
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp
        with pytest.raises(ProviderError, match="No image in response"):
            await adapter.generate(req)


async def test_generate_missing_key_raises(adapter: OpenAIDalleAdapter) -> None:
    req = ImageGenerationRequest(prompt="tree")
    resp = httpx.Response(
        200,
        json={"result": "unexpected"},
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp
        with pytest.raises(ProviderError, match="No image in response"):
            await adapter.generate(req)


async def test_health_check_success(adapter: OpenAIDalleAdapter) -> None:
    resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = resp
        assert await adapter.health_check() is True


async def test_health_check_failure(adapter: OpenAIDalleAdapter) -> None:
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("timeout")
        assert await adapter.health_check() is False
