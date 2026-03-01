from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import ImageGenerateRequest, ImageGenerateResponse
from config.auth import get_org_roles
from core.exceptions import ProviderError
from core.types import ImageGenerationRequest
from services.image_service import ImageService

router = APIRouter(prefix="/api/v1/generate", tags=["image"])


def get_image_service(request: Request) -> ImageService:
    return request.app.state.image_service  # type: ignore[no-any-return]


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
    try:
        result = await service.generate(request)
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ImageGenerateResponse(
        image_base64=base64.b64encode(result.image_data).decode(),
        format=result.format,
        prompt_used=result.prompt_used,
        provider=result.provider,
    )
