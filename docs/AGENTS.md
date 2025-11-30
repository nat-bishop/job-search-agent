# Agent Development Guide

## Current Approach

Agents are built using **LangGraph's Deep Agents** with the **create_deep_agent** function.

### Deep Agents Pattern

Deep agents extend LangGraph's agent capabilities with:

1. **Built-in Tools**: write_todos, filesystem (ls, read_file, write_file, edit_file)
2. **Subagent Delegation**: Delegate complex tasks to specialized subagents
3. **Long-term Memory**: Persistent storage via CompositeBackend with path routing
4. **System Prompts**: Rich context provided via `system_prompt` parameter

### Creating an Agent

```python
from deepagents import create_deep_agent
from src.core.llm import get_agent_llm
from src.workflows.simple.tools import get_current_time, web_search

# System prompt with tool usage guidance
SYSTEM_PROMPT = """You are a helpful assistant.

## Tools

### `get_current_time`
Use this when the user asks about the current time or date.

### `web_search`
Use this to search the web for current events and information.
"""

# Create agent
agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[get_current_time, web_search],
    system_prompt=SYSTEM_PROMPT,
)

# Run agent
result = agent.invoke({"messages": [("user", "What time is it?")]})
```

### Tool Design Pattern

Tools use a **two-layer documentation pattern**:

1. **Tool docstring**: Minimal - what it does, args, returns (schema only)
2. **System prompt**: Tool usage guidance (when/how to use)

**Tool Example**:
```python
@tool
def web_search(query: str) -> str:
    """Search the web using Exa neural search.

    Args:
        query: Natural language search query

    Returns:
        Search results with titles, URLs, and content snippets
    """
    # Implementation...
```

**System Prompt Example**:
```python
SYSTEM_PROMPT = """
## Tools

### `web_search`
Use this to search the web for information. You can run multiple searches
to gather comprehensive information on a topic.
"""
```

**Why this pattern?**
- Tools are portable and self-contained
- System prompt provides workflow-specific context
- Matches Deep Agents quickstart pattern

### Subagents

For complex delegation, define subagents:

```python
RESEARCH_SUBAGENT = {
    "name": "research",
    "description": "Searches the web and synthesizes information.",
    "system_prompt": "You are a research specialist...",
    "tools": [web_search],
}

agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[get_current_time],
    subagents=[RESEARCH_SUBAGENT],
    system_prompt=SYSTEM_PROMPT,
)
```

The parent agent delegates to subagents using the built-in `task()` tool.

### Long-term Memory

Configure persistent storage with `CompositeBackend`:

```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

def make_backend(runtime):
    """Route /memories/ to persistent storage."""
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    )

agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[...],
    system_prompt=SYSTEM_PROMPT,
    store=InMemoryStore(),
    backend=make_backend,
)
```

Agents read/write to paths and the backend routes automatically:
- `/memories/` - Persistent (survives sessions)
- `/workspace/` - Ephemeral (cleared after session)

## Resources

- [Deep Agents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep Agents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [Deep Agents Long-Term Memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Qwen 2.5 Tool Calling](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
