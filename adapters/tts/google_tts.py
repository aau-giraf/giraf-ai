import base64

import httpx

from core.exceptions import ProviderError
from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo

_FORMAT_MAP = {
    "mp3": "MP3",
    "wav": "LINEAR16",
    "ogg": "OGG_OPUS",
}


class GoogleTTSAdapter(TTSPort):
    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://texttospeech.googleapis.com/v1",
            params={"key": api_key},
            timeout=30.0,
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        audio_encoding = _FORMAT_MAP.get(request.format, "MP3")
        voice_config: dict[str, str] = {"languageCode": request.language}
        if request.voice:
            voice_config["name"] = request.voice

        try:
            resp = await self._client.post(
                "/text:synthesize",
                json={
                    "input": {"text": request.text},
                    "voice": voice_config,
                    "audioConfig": {"audioEncoding": audio_encoding},
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("google_tts", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("google_tts", str(e)) from e

        data = resp.json()
        try:
            audio_bytes = base64.b64decode(data["audioContent"])
        except (KeyError, TypeError) as e:
            raise ProviderError("google_tts", "No audio in response") from e

        return TTSResult(
            audio_data=audio_bytes,
            format=request.format,
            duration_ms=None,
            provider="google_tts",
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        params = {}
        if language:
            params["languageCode"] = language
        try:
            resp = await self._client.get("/voices", params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("google_tts", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("google_tts", str(e)) from e

        voices = []
        for v in resp.json().get("voices", []):
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
