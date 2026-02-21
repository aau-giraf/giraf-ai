import pytest

from adapters.tts.mock import MockTTSAdapter
from core.types import TTSRequest
from services.tts_service import TTSService


@pytest.fixture
def tts_service():
    return TTSService(MockTTSAdapter())


async def test_synthesize_returns_audio(tts_service):
    req = TTSRequest(text="Hej verden")
    result = await tts_service.synthesize(req)
    assert result.audio_data
    assert result.provider == "mock"
    assert result.duration_ms and result.duration_ms > 0


async def test_list_voices(tts_service):
    voices = await tts_service.list_voices()
    assert len(voices) == 2


async def test_list_voices_filtered(tts_service):
    voices = await tts_service.list_voices(language="da")
    assert len(voices) == 1
    assert voices[0].language == "da"
