import base64
import io
import struct

import httpx

from core.exceptions import ProviderError
from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo

# Gemini TTS voices — no list endpoint exists, so these are hardcoded.
_GEMINI_VOICES = [
    VoiceInfo(id="Kore", name="Kore", language="en", gender="female"),
    VoiceInfo(id="Puck", name="Puck", language="en", gender="male"),
    VoiceInfo(id="Charon", name="Charon", language="en", gender="male"),
    VoiceInfo(id="Fenrir", name="Fenrir", language="en", gender="male"),
    VoiceInfo(id="Aoede", name="Aoede", language="en", gender="female"),
    VoiceInfo(id="Leda", name="Leda", language="en", gender="female"),
    VoiceInfo(id="Orus", name="Orus", language="en", gender="male"),
    VoiceInfo(id="Zephyr", name="Zephyr", language="en", gender="female"),
]


def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
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


class GeminiTTSAdapter(TTSPort):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash-preview-tts",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"x-goog-api-key": api_key},
            timeout=30.0,
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        voice_name = request.voice or "Kore"
        try:
            resp = await self._client.post(
                f"/models/{self._model}:generateContent",
                json={
                    "contents": [{"parts": [{"text": request.text}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}
                        },
                    },
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("gemini_tts", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("gemini_tts", str(e)) from e

        data = resp.json()
        try:
            inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
        except (KeyError, IndexError) as e:
            raise ProviderError("gemini_tts", "No audio in response") from e

        pcm = base64.b64decode(inline["data"])
        wav = _pcm_to_wav(pcm)

        return TTSResult(
            audio_data=wav,
            format="wav",
            duration_ms=None,
            provider="gemini_tts",
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        voices = list(_GEMINI_VOICES)
        if language:
            voices = [v for v in voices if v.language == language]
        return voices

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(f"/models/{self._model}")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
