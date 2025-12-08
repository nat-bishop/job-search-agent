"""LLM factory for local Ollama models.

Uses ChatOpenAI pointed at Ollama's /v1 endpoint instead of ChatOllama.
This provides more reliable tool calling because:
1. ChatOpenAI's tool handling is more battle-tested
2. Ollama's OpenAI-compatible endpoint has better tool message formatting
3. Avoids ChatOllama's tool_call_id serialization bugs with Qwen/Llama models
"""

from functools import lru_cache
from typing import Any

import httpx
from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger("llm")


@lru_cache(maxsize=8)
def get_model_context_length(model: str) -> int:
    """Query Ollama for model's context length. Cached per model name.

    Args:
        model: The Ollama model name (e.g., "gpt-oss:120b").

    Returns:
        Context length in tokens. Falls back to 131072 if query fails.
    """
    url = f"{str(settings.ollama_url).rstrip('/')}/api/show"

    try:
        resp = httpx.post(url, json={"name": model}, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        # Context length is nested in model_info
        context_length = data.get("model_info", {}).get("context_length")
        if context_length:
            logger.debug("context_length_detected", model=model, length=context_length)
            return int(context_length)
    except Exception as e:
        logger.warning("context_length_fallback", model=model, error=str(e))

    return 131072  # Safe fallback


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
    base_url = str(settings.ollama_url).rstrip("/") + "/v1"

    model = ChatOpenAI(
        model=settings.local_model,
        base_url=base_url,
        api_key=SecretStr("ollama"),  # Required by ChatOpenAI but ignored by Ollama
        temperature=temperature,
        **kwargs,
    )

    # Set profile for LangChain middleware (enables fraction-based triggers)
    context_length = get_model_context_length(settings.local_model)
    model.profile = {"max_input_tokens": context_length}

    return model


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
