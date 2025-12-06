"""LLM factory with provider swapping support."""

from functools import lru_cache
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseChatModel

from src.core.config import LLMProvider, settings

if TYPE_CHECKING:
    pass


def get_llm(
    provider: LLMProvider | str | None = None,
    *,
    temperature: float = 0.0,
    **kwargs,
) -> BaseChatModel:
    """
    Get an LLM instance based on the configured or specified provider.

    Args:
        provider: Override the default provider. Can be LLMProvider enum or string.
        temperature: Model temperature (0.0 = deterministic).
        **kwargs: Additional arguments passed to the model constructor.

    Returns:
        A LangChain chat model instance.

    Raises:
        ValueError: If the provider is not supported or required API key is missing.

    Examples:
        >>> # Use default provider from settings
        >>> llm = get_llm()

        >>> # Override to use Anthropic
        >>> llm = get_llm("anthropic")

        >>> # With custom temperature
        >>> llm = get_llm(temperature=0.7)
    """
    # Normalize provider
    if provider is None:
        provider = settings.llm_provider
    elif isinstance(provider, str):
        provider = LLMProvider(provider.lower())

    if provider == LLMProvider.LOCAL:
        return _get_ollama_llm(temperature=temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _get_ollama_llm(temperature: float = 0.0, **kwargs) -> BaseChatModel:
    """Get Ollama (local) LLM via OpenAI-compatible endpoint.

    Uses ChatOpenAI pointed at Ollama's /v1 endpoint instead of ChatOllama.
    This provides more reliable tool calling because:
    1. ChatOpenAI's tool handling is more battle-tested
    2. Ollama's OpenAI-compatible endpoint has better tool message formatting
    3. Avoids ChatOllama's tool_call_id serialization bugs with Qwen/Llama models
    """
    from langchain_openai import ChatOpenAI

    # Remove json_mode if present (not supported by ChatOpenAI the same way)
    kwargs.pop("json_mode", None)

    # Ollama exposes OpenAI-compatible API at /v1
    base_url = settings.ollama_url.rstrip("/") + "/v1"

    return ChatOpenAI(
        model=settings.local_model,
        base_url=base_url,
        api_key="ollama",  # Required by ChatOpenAI but ignored by Ollama
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


# Convenience function for agents
def get_agent_llm(**kwargs) -> BaseChatModel:
    """
    Get an LLM configured for agent use.

    This sets sensible defaults for agent tool calling:
    - temperature=0.0 for deterministic outputs
    - Configured for the default provider

    Args:
        **kwargs: Override any default settings.

    Returns:
        LLM configured for agent use.
    """
    defaults = {
        "temperature": 0.0,
    }
    defaults.update(kwargs)
    return get_llm(**defaults)
