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
    elif provider == LLMProvider.ANTHROPIC:
        return _get_anthropic_llm(temperature=temperature, **kwargs)
    elif provider == LLMProvider.OPENAI:
        return _get_openai_llm(temperature=temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _get_ollama_llm(temperature: float = 0.0, **kwargs) -> BaseChatModel:
    """Get Ollama (local) LLM."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.local_model,
        base_url=settings.ollama_url,
        temperature=temperature,
        # Enable tool calling format for Qwen/Llama models
        format="json" if kwargs.pop("json_mode", False) else None,
        **kwargs,
    )


def _get_anthropic_llm(temperature: float = 0.0, **kwargs) -> BaseChatModel:
    """Get Anthropic LLM."""
    if not settings.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required when using the Anthropic provider. "
            "Set it in your .env file."
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        **kwargs,
    )


def _get_openai_llm(temperature: float = 0.0, **kwargs) -> BaseChatModel:
    """Get OpenAI LLM."""
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is required when using the OpenAI provider. "
            "Set it in your .env file."
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
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
