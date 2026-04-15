"""Provider name constants for image generation and TTS adapters."""

from enum import StrEnum


class ImageProvider(StrEnum):
    MOCK = "mock"
    OPENAI_DALLE = "openai_dalle"
    GEMINI = "gemini"
    IMAGEGEN = "imagegen"


class TTSProvider(StrEnum):
    MOCK = "mock"
    GEMINI_TTS = "gemini_tts"
    PLAPRE = "plapre"
    PLAPRE_CPU = "plapre_cpu"
