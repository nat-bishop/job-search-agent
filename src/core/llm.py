"""LLM factory for local Ollama models.

Uses ChatOpenAI pointed at Ollama's /v1 endpoint instead of ChatOllama.
This provides more reliable tool calling because:
1. ChatOpenAI's tool handling is more battle-tested
2. Ollama's OpenAI-compatible endpoint has better tool message formatting
3. Avoids ChatOllama's tool_call_id serialization bugs with Qwen/Llama models
"""

from functools import lru_cache
from typing import Any

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from src.core.config import settings


def get_llm(*, temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """
    Get an LLM instance configured for local Ollama.

    Args:
        temperature: Model temperature (0.0 = deterministic).
        **kwargs: Additional arguments passed to the model constructor.

    Returns:
        A LangChain chat model instance.

    Examples:
        >>> llm = get_llm()
        >>> llm = get_llm(temperature=0.7)
    """
    from langchain_openai import ChatOpenAI

    # Remove json_mode if present (not supported by ChatOpenAI the same way)
    kwargs.pop("json_mode", None)

    # Ollama exposes OpenAI-compatible API at /v1
    base_url = settings.ollama_url.rstrip("/") + "/v1"

    return ChatOpenAI(
        model=settings.local_model,
        base_url=base_url,
        api_key=SecretStr("ollama"),  # Required by ChatOpenAI but ignored by Ollama
        temperature=temperature,
        **kwargs,
    )


@lru_cache(maxsize=1)
def get_default_llm() -> BaseChatModel:
    """
    Get the default LLM instance (cached).

    Use this for single-LLM applications where you don't need to switch providers.
    The instance is cached for efficiency.

    Returns:
        The default LLM based on settings.
    """
    return get_llm()


def get_agent_llm(**kwargs: Any) -> BaseChatModel:
    """
    Get an LLM configured for agent use.

    This sets sensible defaults for agent tool calling:
    - temperature=0.0 for deterministic outputs

    Args:
        **kwargs: Override any default settings.

    Returns:
        LLM configured for agent use.
    """
    defaults = {"temperature": 0.0}
    defaults.update(kwargs)
    return get_llm(**defaults)
