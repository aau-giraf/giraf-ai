import base64

import httpx

from core.audio import pcm_to_wav
from core.exceptions import ProviderError
from core.http import provider_request
from core.ports import TTSPort
from core.providers import TTSProvider
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


class GeminiTTSAdapter(TTSPort):
    supported_formats = frozenset({"wav"})

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
        async with provider_request(
            self._client,
            "post",
            f"/models/{self._model}:generateContent",
            TTSProvider.GEMINI_TTS,
            json={
                "contents": [{"parts": [{"text": request.text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}
                    },
                },
            },
        ) as resp:
            data = resp.json()
        try:
            inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
        except (KeyError, IndexError) as e:
            raise ProviderError(TTSProvider.GEMINI_TTS, "No audio in response") from e

        pcm = base64.b64decode(inline["data"])
        wav = pcm_to_wav(pcm)

        return TTSResult(
            audio_data=wav,
            format="wav",
            duration_ms=None,
            provider=TTSProvider.GEMINI_TTS,
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
