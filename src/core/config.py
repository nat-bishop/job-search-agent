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
    searxng_engines: str = Field(default="brave,startpage,qwant,mojeek")
    search_result_buffer: float = Field(default=2.0)

    # Logging
    log_file: str | None = Field(default="logs/ai-agents.jsonl")
    log_json: bool = Field(default=True)  # JSON format for file, console stays readable


settings = Settings()
