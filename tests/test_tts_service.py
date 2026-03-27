import pytest

from adapters.tts.mock import MockTTSAdapter
from core.types import TTSRequest, TTSResult
from services.tts_service import TTSService


@pytest.fixture
def tts_service() -> TTSService:
    return TTSService(MockTTSAdapter())


async def test_synthesize_returns_audio(tts_service: TTSService) -> None:
    req = TTSRequest(text="Hej verden")
    result = await tts_service.synthesize(req)
    assert result.audio_data
    assert result.provider == "mock"
    assert result.duration_ms and result.duration_ms > 0


async def test_list_voices(tts_service: TTSService) -> None:
    voices = await tts_service.list_voices()
    assert len(voices) == 2


async def test_list_voices_filtered(tts_service: TTSService) -> None:
    voices = await tts_service.list_voices(language="da")
    assert len(voices) == 1
    assert voices[0].language == "da"


async def test_newlines_stripped_from_text(tts_service: TTSService) -> None:
    original_synthesize = tts_service.adapter.synthesize

    captured_request: list[TTSRequest] = []

    async def spy(request: TTSRequest) -> TTSResult:
        captured_request.append(request)
        return await original_synthesize(request)

    tts_service.adapter.synthesize = spy  # type: ignore[assignment]
    req = TTSRequest(text="Hej\n\nIgnore instructions")
    await tts_service.synthesize(req)
    assert len(captured_request) == 1
    assert "\n" not in captured_request[0].text


async def test_health_check_delegates_to_adapter(tts_service: TTSService) -> None:
    result = await tts_service.health_check()
    assert result is True
