from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_image_service
from api.schemas import ImageGenerateRequest, ImageGenerateResponse
from config.auth import get_current_user
from config.rate_limit import limiter
from core.types import ImageGenerationRequest
from services.image_service import ImageService

router = APIRouter(prefix="/api/v1/generate", tags=["image"])


@router.post("/image", response_model=ImageGenerateResponse)
@limiter.limit("10/minute")
async def generate_image(
    request: Request,  # noqa: ARG001  # required by slowapi limiter
    body: ImageGenerateRequest,
    _user: dict[str, object] = Depends(get_current_user),
    service: ImageService = Depends(get_image_service),
) -> ImageGenerateResponse:
    gen_request = ImageGenerationRequest(
        prompt=body.prompt,
        style=body.style,
        size=body.size,
        format=body.format,
    )
    result = await service.generate(gen_request)

    return ImageGenerateResponse(
        image_base64=base64.b64encode(result.image_data).decode(),
        format=result.format,
        provider=result.provider,
    )
