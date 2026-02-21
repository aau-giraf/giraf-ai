from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo


class TTSService:
    def __init__(self, adapter: TTSPort) -> None:
        self.adapter = adapter

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        return await self.adapter.synthesize(request)

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return await self.adapter.list_voices(language)
