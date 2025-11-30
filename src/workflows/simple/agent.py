"""Simple ReAct agent for testing the architecture."""

from langgraph.prebuilt import create_react_agent

from src.core.llm import get_agent_llm
from src.workflows.simple.tools import get_current_time

SYSTEM_PROMPT = """You are a helpful assistant that can tell the time.

Instructions:
- Use get_current_time when asked about the current time or date
- Be concise in your responses
- If a tool fails, explain the error to the user
"""


def create_simple_agent():
    """Create and return the simple test agent."""
    llm = get_agent_llm()
    # Start with just get_current_time (no API key required)
    # Add web_search later when Exa is configured
    tools = [get_current_time]

    return create_react_agent(
        llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
