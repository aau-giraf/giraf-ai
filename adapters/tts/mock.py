import io
import struct

from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo


def _make_wav_silence(duration_ms: int = 500, sample_rate: int = 16000) -> bytes:
    """Generate a minimal silent WAV file."""
    num_samples = sample_rate * duration_ms // 1000
    buf = io.BytesIO()
    data_size = num_samples * 2  # 16-bit mono
    # WAV header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(b"\x00" * data_size)
    return buf.getvalue()


class MockTTSAdapter(TTSPort):
    """Returns silent audio. For dev/test only."""

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        duration_ms = len(request.text) * 80  # rough estimate
        audio = _make_wav_silence(duration_ms)
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
