import base64

import httpx

from core.exceptions import ProviderError
from core.http import provider_request
from core.ports import TTSPort
from core.providers import TTSProvider
from core.types import TTSRequest, TTSResult, VoiceInfo

_FORMAT_MAP = {
    "mp3": "MP3",
    "wav": "LINEAR16",
    "ogg": "OGG_OPUS",
}


class GoogleTTSAdapter(TTSPort):
    def __init__(
        self, api_key: str, base_url: str = "https://texttospeech.googleapis.com/v1"
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            params={"key": api_key},
            timeout=30.0,
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        audio_encoding = _FORMAT_MAP.get(request.format, "MP3")
        voice_config: dict[str, str] = {"languageCode": request.language}
        if request.voice:
            voice_config["name"] = request.voice

        async with provider_request(
            self._client,
            "post",
            "/text:synthesize",
            TTSProvider.GOOGLE_TTS,
            json={
                "input": {"text": request.text},
                "voice": voice_config,
                "audioConfig": {"audioEncoding": audio_encoding},
            },
        ) as resp:
            data = resp.json()
        try:
            audio_bytes = base64.b64decode(data["audioContent"])
        except (KeyError, TypeError) as e:
            raise ProviderError(TTSProvider.GOOGLE_TTS, "No audio in response") from e

        return TTSResult(
            audio_data=audio_bytes,
            format=request.format,
            duration_ms=None,
            provider=TTSProvider.GOOGLE_TTS,
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        params = {}
        if language:
            params["languageCode"] = language
        async with provider_request(
            self._client, "get", "/voices", TTSProvider.GOOGLE_TTS, params=params
        ) as resp:
            voice_data = resp.json()

        voices = []
        for v in voice_data.get("voices", []):
            voices.append(
                VoiceInfo(
                    id=v["name"],
                    name=v["name"],
                    language=v["languageCodes"][0] if v.get("languageCodes") else "",
                    gender=v.get("ssmlGender", "").lower() or None,
                )
            )
        return voices

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/voices")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
