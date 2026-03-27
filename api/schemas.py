from typing import Annotated, Literal

from pydantic import BaseModel, Field

PositiveInt = Annotated[int, Field(gt=0)]


class ImageGenerateRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1, max_length=500)]
    style: Literal["pictogram", "realistic", "cartoon"] = "pictogram"
    size: tuple[PositiveInt, PositiveInt] = (512, 512)
    format: Literal["png", "webp"] = "png"


class ImageGenerateResponse(BaseModel):
    image_base64: str
    format: str
    provider: str


class TTSSynthesizeRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=2000)]
    language: str = "da"
    voice: str | None = None
    format: Literal["mp3", "wav", "ogg"] = "mp3"


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
