"""Langfuse tracing integration for LangChain/LangGraph agents."""

import os

from dotenv import load_dotenv

# Load .env before importing Langfuse (it reads env vars at import time)
load_dotenv()

from langfuse.langchain import CallbackHandler  # noqa: E402


def get_langfuse_handler() -> CallbackHandler | None:
    """Get Langfuse callback handler for LangChain/LangGraph tracing.

    Returns:
        CallbackHandler if Langfuse is configured, None otherwise.

    Usage:
        handler = get_langfuse_handler()
        config = {"callbacks": [handler]} if handler else {}
        response = agent.invoke({"messages": messages}, config=config)
    """
    # Check if Langfuse credentials are configured
    if not os.getenv("LANGFUSE_SECRET_KEY"):
        return None

    return CallbackHandler()
