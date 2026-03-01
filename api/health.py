from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.schemas import HealthResponse
from services.image_service import ImageService
from services.tts_service import TTSService

router = APIRouter(tags=["health"])


def get_image_service(request: Request) -> ImageService:
    return request.app.state.image_service  # type: ignore[no-any-return]


def get_tts_service(request: Request) -> TTSService:
    return request.app.state.tts_service  # type: ignore[no-any-return]


@router.get("/api/v1/health", response_model=HealthResponse)
async def health(
    image_svc: ImageService = Depends(get_image_service),
    tts_svc: TTSService = Depends(get_tts_service),
) -> HealthResponse:
    image_ok = await image_svc.health_check()
    tts_ok = await tts_svc.health_check()
    providers = {"image": image_ok, "tts": tts_ok}
    status = "healthy" if all(providers.values()) else "degraded"
    return HealthResponse(status=status, providers=providers)
