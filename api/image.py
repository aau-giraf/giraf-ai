import base64

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import ImageGenerateRequest, ImageGenerateResponse
from config.auth import get_org_roles
from core.exceptions import ProviderError
from core.types import ImageGenerationRequest

router = APIRouter(prefix="/api/v1/generate", tags=["image"])


def _get_image_service():
    from main import app_state

    return app_state["image_service"]


@router.post("/image", response_model=ImageGenerateResponse)
async def generate_image(
    body: ImageGenerateRequest,
    _org_roles: dict[str, str] = Depends(get_org_roles),
):
    service = _get_image_service()
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
