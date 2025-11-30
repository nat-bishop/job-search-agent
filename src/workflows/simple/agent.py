"""Simple deep agent for testing the architecture.

Uses deep agents for:
- Subagent delegation (research tasks)
- Built-in planning (write_todos)
- Long-term memory (/memories/ path)
"""

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

from src.core.llm import get_agent_llm
from src.workflows.simple.tools import get_current_time, web_search

SYSTEM_PROMPT = """You are a helpful assistant that can tell the time and research information.

## Tools

### `get_current_time`

Use this to get the current date and time when the user asks about:
- What time is it
- Today's date
- What day it is

### `research` (subagent)

Delegate to this subagent when the user needs:
- Current events or recent news
- Information requiring web search
- Comprehensive research on a topic

The research subagent will search the web and synthesize findings for you.

## File Storage

- `/memories/` - Persistent storage that survives across sessions
- `/workspace/` - Temporary scratch space (cleared after session)

## General Instructions

- Use `write_todos` to plan complex multi-step tasks
- Be concise in your responses
- If a tool fails, explain the error to the user
"""

# Research subagent for web search tasks
RESEARCH_SUBAGENT = {
    "name": "research",
    "description": "Searches the web and synthesizes information. Use when the user asks about current events, facts you don't know, or needs comprehensive research.",
    "system_prompt": """You are a research specialist that conducts web research and synthesizes findings.

## Tools

### `web_search`

Use this to search the web for information. You can run multiple searches to gather comprehensive information on a topic.

## Workflow

1. Break down the research question into searchable queries
2. Use web_search for each query
3. Synthesize findings into 3-5 key bullet points
4. Save important findings to /memories/research/ for future reference
5. Return only key insights, not raw search results

## File Organization

- `/memories/research/sources.txt` - URLs and references
- `/memories/research/notes.txt` - Key facts discovered
- `/memories/research/{topic}.md` - Topic-specific research reports
""",
    "tools": [web_search],
    # No model override = uses same local model as parent
}


def make_backend(runtime):
    """Route /memories/ to persistent storage, everything else ephemeral."""
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    )


# Shared store for persistence (InMemoryStore for dev, PostgresStore for prod)
_store = InMemoryStore()


def create_simple_agent():
    """Create and return the simple test agent with subagent support."""
    llm = get_agent_llm()

    return create_deep_agent(
        model=llm,
        tools=[get_current_time],
        subagents=[RESEARCH_SUBAGENT],
        system_prompt=SYSTEM_PROMPT,
        store=_store,
        backend=make_backend,
    )
