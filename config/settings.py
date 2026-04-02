from pydantic import Field
from pydantic_settings import BaseSettings

from core.providers import ImageProvider, TTSProvider


class Settings(BaseSettings):
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

    image_provider: ImageProvider = ImageProvider.MOCK
    tts_provider: TTSProvider = TTSProvider.MOCK

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.5-flash-image"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    plapre_base_url: str = "http://localhost:8200"
    imagegen_base_url: str = "http://localhost:8300"

    cors_allowed_origins: list[str] = []

    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8100

    model_config = {"env_file": ".env", "env_prefix": "", "case_sensitive": False}


settings = Settings()  # type: ignore[call-arg]  # pydantic-settings populates from .env
