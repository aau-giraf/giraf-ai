from typing import Annotated, Literal

from pydantic import BaseModel, Field

ImageDimension = Annotated[int, Field(gt=0, le=4096)]


class ImageGenerateRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1, max_length=500)]
    style: Literal["pictogram", "realistic", "cartoon"] = "pictogram"
    size: tuple[ImageDimension, ImageDimension] = (512, 512)
    format: Literal["png", "webp"] = "png"


class ImageGenerateResponse(BaseModel):
    image_base64: str
    format: str
    provider: str


class TTSSynthesizeRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=2000)]
    language: str = "da"
    voice: str | None = None
    format: Literal["mp3", "wav", "ogg"] = "wav"


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
