from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

    image_provider: str = "mock"  # "mock" | "openai_dalle" | "gemini"
    tts_provider: str = "mock"  # "mock" | "google_tts" | "gemini_tts"

    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-image"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    google_tts_credentials: str = ""

    host: str = "0.0.0.0"
    port: int = 8100

    model_config = {"env_file": ".env", "env_prefix": "", "case_sensitive": False}


settings = Settings()  # type: ignore[call-arg]  # pydantic-settings populates from .env
