# Agent Development Guide

## Current Approach

Agents are built using **LangGraph's Deep Agents** with the **create_deep_agent** function.

### Deep Agents Pattern

Deep agents extend LangGraph's agent capabilities with:

1. **Built-in Tools**: write_todos, filesystem (ls, read_file, write_file, edit_file)
2. **Subagent Delegation**: Delegate complex tasks to specialized subagents
3. **Long-term Memory**: Persistent storage via FilesystemBackend
4. **System Prompts**: Rich context provided via `system_prompt` parameter
5. **YAML Prompts**: External prompt files with variable injection (e.g., `{current_date}`)

### Creating an Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from src.core.llm import get_agent_llm
from src.workflows.job_search.tools import web_search, fetch

# System prompt with tool usage guidance (or load from YAML)
SYSTEM_PROMPT = """You are a helpful assistant.

## Tools

### `web_search`
Use this to search the web for current events and information.

### `fetch`
Use this to get full content from a webpage URL.
"""

# Create agent with filesystem memory
agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[web_search, fetch],
    system_prompt=SYSTEM_PROMPT,
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)

# Run agent (async required for async tools)
import asyncio
async def main():
    async for event in agent.astream({"messages": [("user", "Search for AI news")]}):
        print(event)

asyncio.run(main())
```

### Tool Design Pattern

Tools use a **two-layer documentation pattern**:

1. **Tool docstring**: Minimal - what it does, args, returns (schema only)
2. **System prompt**: Tool usage guidance (when/how to use)

**Tool Example**:
```python
@tool
def web_search(query: str) -> str:
    """Search the web using SearXNG.

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
    "tools": [web_search, fetch],
}

agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[],  # Main agent delegates to subagent
    subagents=[RESEARCH_SUBAGENT],
    system_prompt=SYSTEM_PROMPT,
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)
```

The parent agent delegates to subagents using the built-in `task()` tool.

### Long-term Memory

Configure persistent storage with `FilesystemBackend`:

```python
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[...],
    system_prompt=SYSTEM_PROMPT,
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)
```

The `FilesystemBackend` stores memory in the local filesystem:
- Files persist in the `data/` directory across sessions
- Agent uses `read_file`, `write_file`, `edit_file` tools
- `virtual_mode=True` enables sandboxed file operations

**Example: Job Search Memory Structure**
- `/memories/jobs.md` - Curated job opportunities
- `/memories/seen_urls.txt` - Processed URLs for deduplication

### YAML Prompts with Variable Injection

Prompts are stored in YAML files for easier iteration:

```yaml
# prompts/main_agent.yaml
system_prompt: |
  Today's date: {current_date}

  You are a job search assistant finding new grad RN positions.

  ## Your Files
  - `/memories/jobs.md` - Curated list of opportunities
```

Load prompts with variable injection:

```python
from datetime import date
import yaml

def load_prompt(name: str) -> dict:
    """Load a prompt YAML file with variable injection."""
    path = f"prompts/{name}.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Inject current date
    if "system_prompt" in data:
        data["system_prompt"] = data["system_prompt"].replace(
            "{current_date}", date.today().isoformat()
        )
    return data
```

## Resources

- [Deep Agents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep Agents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [Deep Agents Long-Term Memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [gpt-oss Model](https://ollama.com/library/gpt-oss) - Primary local model for agent workflows
