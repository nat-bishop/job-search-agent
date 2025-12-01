"""Langfuse tracing integration for LangChain/LangGraph agents."""

from dotenv import load_dotenv

# Load .env before importing Langfuse (it reads env vars at import time)
load_dotenv()

from langfuse.langchain import CallbackHandler  # noqa: E402


def get_langfuse_handler() -> CallbackHandler:
    """Get Langfuse callback handler for LangChain/LangGraph tracing.

    Returns:
        CallbackHandler configured with environment credentials.

    Usage:
        handler = get_langfuse_handler()
        response = agent.invoke(
            {"messages": messages},
            config={"callbacks": [handler]}
        )
    """
    return CallbackHandler()
