from __future__ import annotations

import base64

from fastapi import APIRouter, Depends

from api.dependencies import get_image_service
from api.schemas import ImageGenerateRequest, ImageGenerateResponse
from config.auth import get_org_roles
from core.types import ImageGenerationRequest
from services.image_service import ImageService

router = APIRouter(prefix="/api/v1/generate", tags=["image"])


@router.post("/image", response_model=ImageGenerateResponse)
async def generate_image(
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
        prompt_used=result.prompt_used,
        provider=result.provider,
    )
