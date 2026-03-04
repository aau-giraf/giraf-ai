import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.tts.google_tts import GoogleTTSAdapter
from core.exceptions import ProviderError
from core.types import TTSRequest


@pytest.fixture
def adapter() -> GoogleTTSAdapter:
    return GoogleTTSAdapter(api_key="test-key")


def _tts_response(audio_bytes: bytes = b"fake-audio") -> httpx.Response:
    return httpx.Response(
        200,
        json={"audioContent": base64.b64encode(audio_bytes).decode()},
        request=httpx.Request("POST", "https://example.com"),
    )


async def test_synthesize_returns_audio(adapter: GoogleTTSAdapter) -> None:
    req = TTSRequest(text="hello")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _tts_response(b"audio-data")
        result = await adapter.synthesize(req)

    assert result.audio_data == b"audio-data"
    assert result.format == "mp3"
    assert result.provider == "google_tts"


async def test_synthesize_sends_correct_payload(adapter: GoogleTTSAdapter) -> None:
    req = TTSRequest(text="test", language="da", voice="da-DK-Standard-A")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _tts_response()
        await adapter.synthesize(req)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["input"]["text"] == "test"
    assert payload["voice"]["languageCode"] == "da"
    assert payload["voice"]["name"] == "da-DK-Standard-A"


async def test_synthesize_http_error_raises_provider_error(adapter: GoogleTTSAdapter) -> None:
    req = TTSRequest(text="fail")
    error_resp = httpx.Response(429, request=httpx.Request("POST", "https://example.com"))
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp
        with pytest.raises(ProviderError, match="google_tts"):
            await adapter.synthesize(req)


async def test_synthesize_malformed_response_raises(adapter: GoogleTTSAdapter) -> None:
    req = TTSRequest(text="empty")
    resp = httpx.Response(
        200,
        json={"result": "unexpected"},
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp
        with pytest.raises(ProviderError, match="No audio in response"):
            await adapter.synthesize(req)


async def test_list_voices_returns_voices(adapter: GoogleTTSAdapter) -> None:
    resp = httpx.Response(
        200,
        json={
            "voices": [
                {
                    "name": "da-DK-Standard-A",
                    "languageCodes": ["da-DK"],
                    "ssmlGender": "FEMALE",
                }
            ]
        },
        request=httpx.Request("GET", "https://example.com"),
    )
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = resp
        voices = await adapter.list_voices()

    assert len(voices) == 1
    assert voices[0].id == "da-DK-Standard-A"
    assert voices[0].language == "da-DK"
    assert voices[0].gender == "female"


async def test_health_check_success(adapter: GoogleTTSAdapter) -> None:
    resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = resp
        assert await adapter.health_check() is True


async def test_health_check_failure(adapter: GoogleTTSAdapter) -> None:
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("timeout")
        assert await adapter.health_check() is False
