"""Application configuration using Pydantic Settings."""

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    LOCAL = "local"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Provider
    llm_provider: LLMProvider = Field(default=LLMProvider.LOCAL)

    # Local (Ollama)
    local_model: str = Field(default="qwen2.5:7b")
    ollama_url: str = Field(default="http://localhost:11434")

    # Anthropic (fallback)
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")

    # OpenAI (fallback)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo")

    # External APIs (add as needed)
    exa_api_key: str | None = Field(default=None)


settings = Settings()
