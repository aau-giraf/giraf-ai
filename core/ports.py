from abc import ABC, abstractmethod

from core.types import (
    ImageGenerationRequest,
    ImageGenerationResult,
    TTSRequest,
    TTSResult,
    VoiceInfo,
)


class ImageGeneratorPort(ABC):
    @abstractmethod
    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        """Release resources (e.g. HTTP clients). Override in adapters that hold connections."""


class TTSPort(ABC):
    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResult: ...

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None:
        """Release resources (e.g. HTTP clients). Override in adapters that hold connections."""
