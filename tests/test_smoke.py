"""Smoke tests to verify basic imports and configuration work."""



def test_config_loads():
    """Verify settings can be loaded from environment."""
    from src.core.config import settings

    # Defaults should be set
    assert settings.local_model is not None
    assert settings.ollama_url is not None
    assert settings.searxng_host is not None


def test_llm_factory_imports():
    """Verify LLM factory can be imported."""
    from src.core.llm import get_agent_llm, get_default_llm, get_llm

    # Functions should be callable
    assert callable(get_llm)
    assert callable(get_default_llm)
    assert callable(get_agent_llm)


def test_tracing_optional():
    """Verify tracing gracefully handles missing credentials."""
    from src.core.tracing import get_langfuse_handler

    # Should return None or handler, not raise
    handler = get_langfuse_handler()
    assert handler is None or hasattr(handler, "on_llm_start")


def test_job_search_agent_imports():
    """Verify job search workflow can be imported."""
    from langchain_core.tools import StructuredTool

    from src.workflows.job_search.agent import create_job_search_agent
    from src.workflows.job_search.tools import fetch, web_search

    assert callable(create_job_search_agent)
    # @tool decorator wraps functions as StructuredTool instances
    assert isinstance(web_search, StructuredTool)
    assert isinstance(fetch, StructuredTool)
