from __future__ import annotations

from fastapi import APIRouter

from api.schemas import HealthResponse
from services.image_service import ImageService
from services.tts_service import TTSService

router = APIRouter(tags=["health"])


def _get_services() -> tuple[ImageService, TTSService]:
    from main import app_state

    return app_state["image_service"], app_state["tts_service"]


@router.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    image_svc, tts_svc = _get_services()
    image_ok = await image_svc.adapter.health_check()
    tts_ok = await tts_svc.adapter.health_check()
    providers = {"image": image_ok, "tts": tts_ok}
    status = "healthy" if all(providers.values()) else "degraded"
    return HealthResponse(status=status, providers=providers)
