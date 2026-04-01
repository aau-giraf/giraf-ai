import re
from dataclasses import replace
from pathlib import Path

from core.exceptions import UnsupportedFormatError
from core.ports import TTSPort
from core.types import TTSRequest, TTSResult, VoiceInfo

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "tts"


def _load_tts_prompt() -> str:
    default = _PROMPTS_DIR / "default.md"
    if default.is_file():
        return default.read_text().strip()
    return "{text}"


class TTSService:
    def __init__(self, adapter: TTSPort) -> None:
        self.adapter = adapter
        self._prompt_template = _load_tts_prompt()

    async def health_check(self) -> bool:
        return await self.adapter.health_check()

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        if request.format not in self.adapter.supported_formats:
            supported = ", ".join(sorted(self.adapter.supported_formats))
            raise UnsupportedFormatError(
                f"Format '{request.format}' is not supported by the active TTS provider. "
                f"Supported formats: {supported}"
            )
        sanitized = re.sub(r"[\n\r\t\x00-\x1f]", " ", request.text).strip()
        text = self._prompt_template.replace("{text}", sanitized)
        enriched = replace(request, text=text)
        return await self.adapter.synthesize(enriched)

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return await self.adapter.list_voices(language)
