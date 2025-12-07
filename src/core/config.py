"""Application configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Local LLM (Ollama)
    local_model: str = Field(default="qwen2.5:7b")
    ollama_url: str = Field(default="http://localhost:11434")

    # SearXNG (local web search)
    searxng_host: str = Field(default="http://localhost:8080")

    # Database (PostgreSQL for LangGraph Store, optional)
    database_url: str | None = Field(default=None)


settings = Settings()
