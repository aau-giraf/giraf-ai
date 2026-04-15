import httpx

from core.audio import pcm_to_wav
from core.http import provider_request
from core.ports import TTSPort
from core.providers import TTSProvider
from core.types import TTSRequest, TTSResult, VoiceInfo

PLAPRE_SAMPLE_RATE = 24000


class PlapreAdapter(TTSPort):
    """TTS adapter for Plapre Danish TTS (GPU or CPU server)."""

    supported_formats = frozenset({"wav"})

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        provider: TTSProvider = TTSProvider.PLAPRE,
        timeout: float = 60.0,
    ) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        body: dict[str, str] = {"text": request.text}
        if request.voice:
            body["speaker"] = request.voice

        async with provider_request(
            self._client, "post", "/v1/audio/speech", self._provider, json=body
        ) as resp:
            pcm = resp.content
        wav = pcm_to_wav(pcm)
        duration_ms = len(pcm) // 2 * 1000 // PLAPRE_SAMPLE_RATE  # 16-bit mono

        return TTSResult(
            audio_data=wav,
            format="wav",
            duration_ms=duration_ms,
            provider=self._provider,
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        async with provider_request(self._client, "get", "/v1/speakers", self._provider) as resp:
            speakers = resp.json().get("speakers", [])
        voices = [VoiceInfo(id=name, name=name, language="da") for name in speakers]
        if language:
            voices = [v for v in voices if v.language == language]
        return voices

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
