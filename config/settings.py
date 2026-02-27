from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"

    image_provider: str = "mock"  # "mock" | "openai_dalle" | "gemini"
    tts_provider: str = "mock"  # "mock" | "google_tts"

    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_tts_credentials: str = ""

    host: str = "0.0.0.0"
    port: int = 8100

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
