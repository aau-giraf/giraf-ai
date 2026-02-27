from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "pictogram"
    size: tuple[int, int] = (512, 512)
    format: str = "png"


class ImageGenerateResponse(BaseModel):
    image_base64: str
    format: str
    prompt_used: str
    provider: str


class TTSSynthesizeRequest(BaseModel):
    text: str
    language: str = "da"
    voice: str | None = None
    format: str = "mp3"


class TTSSynthesizeResponse(BaseModel):
    audio_base64: str
    format: str
    duration_ms: int | None
    provider: str


class VoiceResponse(BaseModel):
    id: str
    name: str
    language: str
    gender: str | None = None


class HealthResponse(BaseModel):
    status: str
    providers: dict[str, bool]
