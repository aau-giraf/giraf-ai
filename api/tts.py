from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_tts_service
from api.schemas import TTSSynthesizeRequest, TTSSynthesizeResponse, VoiceResponse
from config.auth import get_current_user
from config.rate_limit import limiter
from core.types import TTSRequest
from services.tts_service import TTSService

router = APIRouter(prefix="/api/v1/tts", tags=["tts"])


@router.post("", response_model=TTSSynthesizeResponse)
@limiter.limit("20/minute")
async def synthesize(
    request: Request,  # noqa: ARG001  # required by slowapi limiter
    body: TTSSynthesizeRequest,
    _user: dict[str, object] = Depends(get_current_user),
    service: TTSService = Depends(get_tts_service),
) -> TTSSynthesizeResponse:
    tts_request = TTSRequest(
        text=body.text,
        language=body.language,
        voice=body.voice,
        format=body.format,
    )
    result = await service.synthesize(tts_request)

    return TTSSynthesizeResponse(
        audio_base64=base64.b64encode(result.audio_data).decode(),
        format=result.format,
        duration_ms=result.duration_ms,
        provider=result.provider,
    )


@router.get("/voices", response_model=list[VoiceResponse])
async def list_voices(
    language: str | None = None,
    _user: dict[str, object] = Depends(get_current_user),
    service: TTSService = Depends(get_tts_service),
) -> list[VoiceResponse]:
    voices = await service.list_voices(language)
    return [
        VoiceResponse(id=v.id, name=v.name, language=v.language, gender=v.gender) for v in voices
    ]
