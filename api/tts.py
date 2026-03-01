from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import TTSSynthesizeRequest, TTSSynthesizeResponse, VoiceResponse
from config.auth import get_org_roles
from core.exceptions import ProviderError
from core.types import TTSRequest
from services.tts_service import TTSService

router = APIRouter(prefix="/api/v1/tts", tags=["tts"])


def _get_tts_service() -> TTSService:
    from main import app_state

    service: TTSService = app_state["tts_service"]
    return service


@router.post("", response_model=TTSSynthesizeResponse)
async def synthesize(
    body: TTSSynthesizeRequest,
    _org_roles: dict[str, str] = Depends(get_org_roles),
) -> TTSSynthesizeResponse:
    service = _get_tts_service()
    request = TTSRequest(
        text=body.text,
        language=body.language,
        voice=body.voice,
        format=body.format,
    )
    try:
        result = await service.synthesize(request)
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return TTSSynthesizeResponse(
        audio_base64=base64.b64encode(result.audio_data).decode(),
        format=result.format,
        duration_ms=result.duration_ms,
        provider=result.provider,
    )


@router.get("/voices", response_model=list[VoiceResponse])
async def list_voices(
    language: str | None = None,
    _org_roles: dict[str, str] = Depends(get_org_roles),
) -> list[VoiceResponse]:
    service = _get_tts_service()
    voices = await service.list_voices(language)
    return [
        VoiceResponse(id=v.id, name=v.name, language=v.language, gender=v.gender) for v in voices
    ]
