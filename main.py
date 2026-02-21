from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from adapters.image.mock import MockImageAdapter
from adapters.image.openai_dalle import OpenAIDalleAdapter
from adapters.tts.google_tts import GoogleTTSAdapter
from adapters.tts.mock import MockTTSAdapter
from api.health import router as health_router
from api.image import router as image_router
from api.tts import router as tts_router
from config.settings import settings
from services.image_service import ImageService
from services.tts_service import TTSService

app_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Image adapter
    if settings.image_provider == "openai_dalle":
        image_adapter = OpenAIDalleAdapter(api_key=settings.openai_api_key)
    else:
        image_adapter = MockImageAdapter()

    # TTS adapter
    if settings.tts_provider == "google_tts":
        tts_adapter = GoogleTTSAdapter(api_key=settings.google_tts_credentials)
    else:
        tts_adapter = MockTTSAdapter()

    app_state["image_service"] = ImageService(image_adapter)
    app_state["tts_service"] = TTSService(tts_adapter)
    yield


app = FastAPI(title="GIRAF AI", version="0.1.0", lifespan=lifespan)
app.include_router(image_router)
app.include_router(tts_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
