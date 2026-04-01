from dataclasses import dataclass, field


@dataclass
class ImageGenerationRequest:
    prompt: str
    style: str = "pictogram"
    size: tuple[int, int] = (512, 512)
    format: str = "png"
    metadata: dict[str, str] | None = None


@dataclass
class ImageGenerationResult:
    image_data: bytes
    format: str
    prompt_used: str
    provider: str
    metadata: dict[str, str] | None = None


@dataclass
class TTSRequest:
    text: str
    language: str = "da"
    voice: str | None = None
    format: str = "wav"


@dataclass
class TTSResult:
    audio_data: bytes
    format: str
    duration_ms: int | None
    provider: str


@dataclass
class VoiceInfo:
    id: str
    name: str
    language: str
    gender: str | None = None


@dataclass
class HealthStatus:
    service: str
    healthy: bool
    providers: dict[str, bool] = field(default_factory=dict)
