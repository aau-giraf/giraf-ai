from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
from core.ports import ImageGeneratorPort, TTSPort
from services.image_service import ImageService
from services.tts_service import TTSService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Image adapter
    image_adapter: ImageGeneratorPort
    if settings.image_provider == "openai_dalle":
        image_adapter = OpenAIDalleAdapter(api_key=settings.openai_api_key)
    elif settings.image_provider == "gemini":
        image_adapter = GeminiImageAdapter(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )
    else:
        image_adapter = MockImageAdapter()

    # TTS adapter
    tts_adapter: TTSPort
    if settings.tts_provider == "google_tts":
        tts_adapter = GoogleTTSAdapter(api_key=settings.google_tts_credentials)
    elif settings.tts_provider == "gemini_tts":
        tts_adapter = GeminiTTSAdapter(
            api_key=settings.gemini_api_key, model=settings.gemini_tts_model
        )
    else:
        tts_adapter = MockTTSAdapter()

    app.state.image_service = ImageService(image_adapter)
    app.state.tts_service = TTSService(tts_adapter)
    yield


app = FastAPI(title="GIRAF AI", version="0.1.0", lifespan=lifespan)
app.include_router(image_router)
app.include_router(tts_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
