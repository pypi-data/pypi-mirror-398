"""
Application Settings
Load configuration from environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file"""

    # App
    app_name: str = "Rule Evaluator API"
    app_version: str = "1.0.0"
    debug: bool = False

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    max_tokens: int = 20000
    temperature: float = 0.1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
