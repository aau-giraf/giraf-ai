import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.tts.gemini_tts import GeminiTTSAdapter
from core.audio import pcm_to_wav
from core.exceptions import ProviderError
from core.types import TTSRequest


@pytest.fixture
def adapter() -> GeminiTTSAdapter:
    return GeminiTTSAdapter(api_key="test-key")


def _tts_response(pcm: bytes = b"\x00\x00" * 100) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "audio/L16;rate=24000",
                                    "data": base64.b64encode(pcm).decode(),
                                }
                            }
                        ]
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://example.com"),
    )


async def test_synthesize_returns_wav(adapter: GeminiTTSAdapter) -> None:
    req = TTSRequest(text="hello")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _tts_response()
        result = await adapter.synthesize(req)

    assert result.audio_data[:4] == b"RIFF"
    assert result.format == "wav"
    assert result.provider == "gemini_tts"


async def test_synthesize_sends_correct_payload(adapter: GeminiTTSAdapter) -> None:
    req = TTSRequest(text="test", voice="Puck")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _tts_response()
        await adapter.synthesize(req)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["contents"][0]["parts"][0]["text"] == "test"
    voice_cfg = payload["generationConfig"]["speechConfig"]["voiceConfig"]
    assert voice_cfg["prebuiltVoiceConfig"]["voiceName"] == "Puck"


async def test_synthesize_defaults_to_kore(adapter: GeminiTTSAdapter) -> None:
    req = TTSRequest(text="hi")
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _tts_response()
        await adapter.synthesize(req)

    payload = mock_post.call_args.kwargs["json"]
    voice_cfg = payload["generationConfig"]["speechConfig"]["voiceConfig"]
    assert voice_cfg["prebuiltVoiceConfig"]["voiceName"] == "Kore"


async def test_synthesize_http_error_raises_provider_error(
    adapter: GeminiTTSAdapter,
) -> None:
    req = TTSRequest(text="fail")
    error_resp = httpx.Response(429, request=httpx.Request("POST", "https://example.com"))
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp
        with pytest.raises(ProviderError, match="gemini_tts"):
            await adapter.synthesize(req)


async def test_synthesize_no_audio_raises(adapter: GeminiTTSAdapter) -> None:
    req = TTSRequest(text="empty")
    resp = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": "no audio"}]}}]},
        request=httpx.Request("POST", "https://example.com"),
    )
    with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp
        with pytest.raises(ProviderError, match="No audio in response"):
            await adapter.synthesize(req)


async def test_health_check_success(adapter: GeminiTTSAdapter) -> None:
    resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = resp
        assert await adapter.health_check() is True


async def test_health_check_failure(adapter: GeminiTTSAdapter) -> None:
    with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("timeout")
        assert await adapter.health_check() is False


async def test_list_voices_returns_all(adapter: GeminiTTSAdapter) -> None:
    voices = await adapter.list_voices()
    assert len(voices) >= 8
    assert any(v.id == "Kore" for v in voices)


async def test_list_voices_filters_by_language(adapter: GeminiTTSAdapter) -> None:
    voices = await adapter.list_voices(language="nonexistent")
    assert voices == []


def test_pcm_to_wav_header() -> None:
    pcm = b"\x00\x00" * 48000  # 2 seconds at 24kHz
    wav = pcm_to_wav(pcm)
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"
    assert wav[44:] == pcm
