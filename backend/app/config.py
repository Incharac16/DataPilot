from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Which AI provider to use for AI Insights. Groq is the only provider
    # implemented right now, but this is read by app/services/ai/factory.py
    # so a new provider (Gemini, OpenAI, ...) can be registered later and
    # selected here without touching any calling code.
    ai_provider: str = "groq"

    # Optional so the app can start (Upload/Preview/Analytics/Charts don't
    # need it) even when no key is configured yet. AI Insights checks for
    # this explicitly at call time and returns a clean 503 if it's missing.
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    upload_dir: str = "uploads"
    max_upload_mb: int = 50

    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    @property
    def cors_origin_list(self):
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
