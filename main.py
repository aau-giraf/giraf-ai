from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from adapters.image.gemini import GeminiImageAdapter
from adapters.image.mock import MockImageAdapter
from adapters.image.openai_dalle import OpenAIDalleAdapter
from adapters.tts.gemini_tts import GeminiTTSAdapter
from adapters.tts.google_tts import GoogleTTSAdapter
from adapters.tts.mock import MockTTSAdapter
from api.health import router as health_router
from api.image import router as image_router
from api.tts import router as tts_router
from config.settings import settings
from core.exceptions import AuthenticationError, MalformedClaimError, ProviderError
from core.ports import ImageGeneratorPort, TTSPort
from services.image_service import ImageService
from services.tts_service import TTSService

_IMAGE_ADAPTERS: dict[str, Callable[[], ImageGeneratorPort]] = {
    "openai_dalle": lambda: OpenAIDalleAdapter(
        api_key=settings.openai_api_key, base_url=settings.openai_base_url
    ),
    "gemini": lambda: GeminiImageAdapter(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
    ),
}

_TTS_ADAPTERS: dict[str, Callable[[], TTSPort]] = {
    "google_tts": lambda: GoogleTTSAdapter(
        api_key=settings.google_tts_credentials, base_url=settings.google_tts_base_url
    ),
    "gemini_tts": lambda: GeminiTTSAdapter(
        api_key=settings.gemini_api_key,
        model=settings.gemini_tts_model,
        base_url=settings.gemini_base_url,
    ),
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    image_factory = _IMAGE_ADAPTERS.get(settings.image_provider)
    image_adapter = image_factory() if image_factory else MockImageAdapter()

    tts_factory = _TTS_ADAPTERS.get(settings.tts_provider)
    tts_adapter = tts_factory() if tts_factory else MockTTSAdapter()

    app.state.image_service = ImageService(image_adapter)
    app.state.tts_service = TTSService(tts_adapter)
    yield


app = FastAPI(title="GIRAF AI", version="0.1.0", lifespan=lifespan)


@app.exception_handler(AuthenticationError)
async def auth_error_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(MalformedClaimError)
async def malformed_claim_handler(_request: Request, exc: MalformedClaimError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ProviderError)
async def provider_error_handler(_request: Request, exc: ProviderError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(image_router)
app.include_router(tts_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
