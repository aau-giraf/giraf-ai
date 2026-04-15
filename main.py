import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from adapters.image.gemini import GeminiImageAdapter
from adapters.image.imagegen import ImagegenAdapter
from adapters.image.mock import MockImageAdapter
from adapters.image.openai_dalle import OpenAIDalleAdapter
from adapters.tts.gemini_tts import GeminiTTSAdapter
from adapters.tts.mock import MockTTSAdapter
from adapters.tts.plapre import PlapreAdapter
from api.health import router as health_router
from api.image import router as image_router
from api.tts import router as tts_router
from config.rate_limit import limiter
from config.settings import settings
from core.exceptions import (
    AuthenticationError,
    ProviderError,
    UnsupportedFormatError,
)
from core.ports import ImageGeneratorPort, TTSPort
from core.providers import ImageProvider, TTSProvider
from services.image_service import ImageService
from services.tts_service import TTSService

logger = logging.getLogger(__name__)

_IMAGE_ADAPTERS: dict[ImageProvider, Callable[[], ImageGeneratorPort]] = {
    ImageProvider.OPENAI_DALLE: lambda: OpenAIDalleAdapter(
        api_key=settings.openai_api_key, base_url=settings.openai_base_url
    ),
    ImageProvider.GEMINI: lambda: GeminiImageAdapter(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
    ),
    ImageProvider.IMAGEGEN: lambda: ImagegenAdapter(base_url=settings.imagegen_base_url),
}

_TTS_ADAPTERS: dict[TTSProvider, Callable[[], TTSPort]] = {
    TTSProvider.GEMINI_TTS: lambda: GeminiTTSAdapter(
        api_key=settings.gemini_api_key,
        model=settings.gemini_tts_model,
        base_url=settings.gemini_base_url,
    ),
    TTSProvider.PLAPRE: lambda: PlapreAdapter(base_url=settings.plapre_base_url),
    TTSProvider.PLAPRE_CPU: lambda: PlapreAdapter(
        base_url=settings.plapre_cpu_base_url,
        provider=TTSProvider.PLAPRE_CPU,
        timeout=120.0,
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

    image_ok = await image_adapter.health_check()
    tts_ok = await tts_adapter.health_check()
    if not image_ok:
        logger.warning(
            "Image provider '%s' failed health check at startup", settings.image_provider
        )
    if not tts_ok:
        logger.warning(
            "TTS provider '%s' failed health check at startup — TTS requests will return 502. "
            "Ensure GEMINI_API_KEY is set and valid.",
            settings.tts_provider,
        )

    yield

    try:
        await image_adapter.close()
    finally:
        await tts_adapter.close()


app = FastAPI(
    title="GIRAF AI",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.debug else None,
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"})


if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(UnsupportedFormatError)
async def unsupported_format_handler(
    _request: Request, exc: UnsupportedFormatError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ProviderError)
async def provider_error_handler(_request: Request, exc: ProviderError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(image_router)
app.include_router(tts_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
