from core.audio import make_wav_silence
from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo


class MockTTSAdapter(TTSPort):
    """Returns silent audio. For dev/test only."""

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        duration_ms = len(request.text) * 80  # rough estimate
        audio = make_wav_silence(duration_ms)
        return TTSResult(
            audio_data=audio,
            format="wav",
            duration_ms=duration_ms,
            provider="mock",
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        voices = [
            VoiceInfo(
                id="mock-da-female", name="Mock Danish Female", language="da", gender="female"
            ),
            VoiceInfo(id="mock-en-male", name="Mock English Male", language="en", gender="male"),
        ]
        if language:
            voices = [v for v in voices if v.language == language]
        return voices

    async def health_check(self) -> bool:
        return True
