from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.dependencies import get_image_service
from api.schemas import ImageGenerateRequest, ImageGenerateResponse
from config.auth import get_org_roles
from core.types import ImageGenerationRequest
from services.image_service import ImageService

router = APIRouter(prefix="/api/v1/generate", tags=["image"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/image", response_model=ImageGenerateResponse)
@limiter.limit("10/minute")
async def generate_image(
    request: Request,
    body: ImageGenerateRequest,
    _org_roles: dict[str, str] = Depends(get_org_roles),
    service: ImageService = Depends(get_image_service),
) -> ImageGenerateResponse:
    request = ImageGenerationRequest(
        prompt=body.prompt,
        style=body.style,
        size=body.size,
        format=body.format,
    )
    result = await service.generate(request)

    return ImageGenerateResponse(
        image_base64=base64.b64encode(result.image_data).decode(),
        format=result.format,
        provider=result.provider,
    )
