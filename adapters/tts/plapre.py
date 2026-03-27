import io
import struct

import httpx

from core.exceptions import ProviderError
from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo

PLAPRE_SAMPLE_RATE = 24000


def _pcm_to_wav(pcm: bytes, sample_rate: int = PLAPRE_SAMPLE_RATE) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV header."""
    buf = io.BytesIO()
    data_size = len(pcm)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(pcm)
    return buf.getvalue()


class PlapreAdapter(TTSPort):
    """TTS adapter for Plapre Danish TTS running on a GPU server."""

    def __init__(self, base_url: str = "http://localhost:8200") -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=60.0,  # TTS generation can be slow
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        body: dict[str, str] = {"text": request.text}
        if request.voice:
            body["speaker"] = request.voice

        try:
            resp = await self._client.post("/v1/audio/speech", json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("plapre", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("plapre", str(e)) from e

        pcm = resp.content
        wav = _pcm_to_wav(pcm)
        duration_ms = len(pcm) // 2 * 1000 // PLAPRE_SAMPLE_RATE  # 16-bit mono

        return TTSResult(
            audio_data=wav,
            format="wav",
            duration_ms=duration_ms,
            provider="plapre",
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        try:
            resp = await self._client.get("/v1/speakers")
            resp.raise_for_status()
        except httpx.RequestError as e:
            raise ProviderError("plapre", str(e)) from e

        speakers = resp.json().get("speakers", [])
        voices = [
            VoiceInfo(id=name, name=name, language="da")
            for name in speakers
        ]
        if language:
            voices = [v for v in voices if v.language == language]
        return voices

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except httpx.RequestError:
            return False
