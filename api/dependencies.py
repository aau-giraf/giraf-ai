from fastapi import Request

from services.image_service import ImageService
from services.tts_service import TTSService


def get_image_service(request: Request) -> ImageService:
    return request.app.state.image_service  # type: ignore[no-any-return]


def get_tts_service(request: Request) -> TTSService:
    return request.app.state.tts_service  # type: ignore[no-any-return]
