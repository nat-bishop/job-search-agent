# Architecture

This document describes the current architecture of the AI Agents project.

## Terminology

| Term | Definition |
|------|------------|
| **Agent** | Autonomous unit with its own system prompt and tools |
| **Workflow** | Collection of agents working together on a domain |
| **Orchestrator** | Agent that coordinates others (supervisor, router, etc.) |

## Directory Structure

```
src/
├── core/           # Shared infrastructure
│   ├── config.py   # Pydantic settings from .env
│   ├── llm.py      # LLM factory for local Ollama + context length detection
│   └── tracing.py  # Langfuse integration (optional)
├── data/           # Agent working directory (FilesystemBackend root)
│   └── memories/   # Persistent agent memory
│       ├── jobs.md        # Job search results
│       └── seen_urls.txt  # URL deduplication
├── workflows/      # Agent workflows by domain
│   └── job_search/ # Nursing job search workflow
│       ├── agent.py    # Deep agent + research subagent
│       ├── tools.py    # web_search, fetch + aliases
│       └── prompts/    # YAML prompt files
```

## Implemented Components

### Configuration (`src/core/config.py`)

Environment-based configuration using Pydantic Settings:

- **LLM Configuration**: Model name and Ollama URL
- **Web Search**: SearXNG host URL
- **Database**: Optional PostgreSQL for LangGraph Store

Configuration is loaded from `.env` file. See `.env.example` for all available options.

**Design decisions:**
- Settings-based rather than hard-coded for flexibility
- Minimal - only includes what's needed for current implementation
- URL fields use `HttpUrl` type for validation (e.g., `ollama_url`, `searxng_host`)
- Numeric constraints where applicable (e.g., `search_result_buffer` must be > 0)

### LLM Factory (`src/core/llm.py`)

Factory for creating Ollama LLM instances:

```python
from src.core.llm import get_llm, get_agent_llm

# Get LLM with defaults
llm = get_llm()

# For agent use (temperature=0.0)
llm = get_agent_llm()
```

Uses `ChatOpenAI` pointed at Ollama's `/v1` endpoint instead of `ChatOllama`. This provides more reliable tool calling because:
1. ChatOpenAI's tool handling is more battle-tested
2. Ollama's OpenAI-compatible endpoint has better tool message formatting
3. Avoids ChatOllama's tool_call_id serialization bugs with Qwen/Llama models

**Design decisions:**
- Returns LangChain `BaseChatModel` for compatibility with LangGraph
- Late import of `ChatOpenAI` to avoid loading unused libraries
- Cached `get_default_llm()` for efficiency

## LangGraph Patterns

### Error Handling

Match error handling strategy to error type:

| Error Type | Strategy | Example |
|------------|----------|---------|
| User-fixable (missing config) | Return error string | `if not settings.api_key: return "Error: API_KEY not configured"` |
| LLM-recoverable (API errors) | Catch and return string | `except Exception as e: return f"Failed: {e}. Try different query."` |
| Transient (network, rate limits) | RetryPolicy on node | `builder.add_node(..., retry_policy=RetryPolicy(max_attempts=3))` |
| Unexpected (bugs) | Let bubble up | Don't catch - needs developer fix |

**Key insight**: Tools should return error strings, not raise exceptions. The LLM sees the error and can adjust (retry, rephrase, use different tool).

### Tool Design for Deep Agents

Deep agents use a **two-layer documentation pattern**:

1. **Tool docstring**: Minimal - describes what it does and args (schema only)
2. **System prompt**: Contains tool usage guidance (when/how to use)

This matches the Deep Agents quickstart pattern and keeps tools focused while giving the agent workflow context.

**Tool Example** (minimal docstring):

```python
@tool
async def web_search(
    query: str,
    time_range: Literal["day", "week", "month", "year"] | None = None,
) -> str:
    """Search the web for information.

    Args:
        query: Search query string
        time_range: Filter to recent results (day, week, month, year)

    Returns:
        Search results with titles, URLs, and snippets
    """
    # Implementation...
```

**Tool Aliases** for model robustness:

Different LLMs may be trained to call tools with different names. Aliases prevent tool-not-found errors:

```python
# Primary tool
@tool
async def web_search(query: str, time_range: str | None = None) -> str:
    """Search the web."""
    ...

# Alias - delegates to primary
@tool
async def search(query: str, time_range: str | None = None) -> str:
    """Search the web. Alias for web_search."""
    return await web_search.ainvoke({"query": query, "time_range": time_range})
```

Current aliases:
- `search` -> `web_search`
- `fetch_page` -> `fetch`

**System Prompt Example** (contains usage guidance):

```python
SYSTEM_PROMPT = """You are an expert researcher.

## Tools

### `web_search`

Use this to search the web for information. You can run multiple searches
to gather comprehensive information on a topic.
"""
```

**Why this pattern?**
- Tools are self-contained and portable (just describe what they do)
- System prompt provides workflow-specific guidance (when to use tools, multi-tool strategies)
- Works well with Deep Agents' comprehensive default prompts

**Validation order in tools:**
1. Check config/preconditions first (cheap, fail fast)
2. Validate inputs (cheap)
3. Call external APIs last (expensive)

### Configuration Access

Always import the singleton settings instance:

```python
# Correct
from src.core.config import settings

# Wrong - creates new instance, ignores .env
from src.core.config import Settings
my_settings = Settings()
```

## Deep Agents

We use `create_deep_agent` as the standard pattern for creating agents. Deep agents extend LangGraph's agent capabilities with built-in tools for complex, autonomous workflows.

### Creating a Deep Agent

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    model=get_llm(),
    tools=[custom_tool],
    system_prompt="You are a helpful assistant...",
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)
```

### Built-in Tools

Deep agents come with built-in tools that enable autonomous operation:

- **write_todos** - Task management for tracking work items
- **Filesystem tools** - `ls`, `read_file`, `write_file`, `edit_file` for file operations

### Subagent Pattern

For complex tasks requiring delegation, use subagents:

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# Define subagent as a dictionary
RESEARCH_SUBAGENT = {
    "name": "research",
    "description": "Searches the web and synthesizes information.",
    "system_prompt": "You are a research specialist...",
    "tools": [web_search, fetch],
}

# Main agent delegates to subagent via task() tool
main_agent = create_deep_agent(
    model=get_llm(),
    tools=[],  # Main agent delegates to subagent
    subagents=[RESEARCH_SUBAGENT],
    system_prompt="You coordinate research tasks...",
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)
```

### Long-term Memory

Deep agents support persistent memory via `FilesystemBackend`:

```python
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    model=get_llm(),
    tools=[...],
    system_prompt=SYSTEM_PROMPT,
    backend=lambda rt: FilesystemBackend(root_dir="data", virtual_mode=True),
)
```

The `FilesystemBackend` stores agent memory in the local filesystem:
- Files persist across sessions in the `data/` directory
- Agent uses `read_file`, `write_file`, `edit_file` tools to manage memory
- `virtual_mode=True` enables sandboxed file operations

**Memory structure for job search workflow:**
| Path | Purpose |
|------|---------|
| `/memories/jobs.md` | Curated job opportunities list |
| `/memories/seen_urls.txt` | URLs already processed (deduplication) |

## Workflow Structure

Each workflow is a subdirectory containing:
- `agent.py` - Deep agent with system prompt via `system_prompt` parameter
- `tools.py` - Tools specific to that workflow
- `prompts/` - YAML prompt files with variable injection

```python
# src/workflows/job_search/agent.py
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# load_prompt() returns validated PromptConfig model
prompt = load_prompt("main_agent")

agent = create_deep_agent(
    model=get_agent_llm(),
    tools=[],  # Main agent uses subagents
    subagents=[RESEARCH_SUBAGENT],
    system_prompt=prompt.system_prompt,  # Type-safe access
    backend=lambda rt: FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
)
```

## Technology Stack

- Python 3.11+
- LangGraph (agent framework)
- LangChain Core (LLM abstraction)
- Pydantic Settings (configuration)
- Ollama (local LLM serving, containerized)
- Docker (optional, for Ollama with GPU passthrough)

### Content Extraction Libraries

The `fetch` tool uses a layered approach for content extraction:

| Library | Use Case |
|---------|----------|
| **Trafilatura** | Primary HTML content extraction (fast, no browser) |
| **BeautifulSoup** | Fallback when Trafilatura fails |
| **pymupdf/pymupdf4llm** | PDF to Markdown conversion |
| **httpx** | Async HTTP client with connection pooling |

## Infrastructure

### Containerized Ollama (Phase 2.7)

Ollama runs in a Docker container with Nvidia GPU passthrough:

**Architecture:**
```
[Python App (host)] --> http://localhost:11434 --> [Ollama Container (GPU)] --> [.ollama-data/ volume]
```

**Benefits:**
- **Process isolation**: Prevents GPU OOM when running multiple agents concurrently
- **Reproducible environment**: Consistent Ollama version across machines
- **Foundation for Phase 4**: Enables Redis queue + worker pattern for scheduling

**Trade-offs:**
- 1-5% performance overhead vs native Ollama
- Requires Docker and nvidia-container-toolkit

**Model Storage:**
- Models persist in `.ollama-data/` volume (65GB+ for gpt-oss:120b)
- Volume survives container restarts
- Excluded from git via `.gitignore`

**Setup:**
```bash
docker compose up -d
docker compose exec ollama ollama pull gpt-oss:120b
```

Python code is unchanged - still connects to `localhost:11434`.

### Model Selection: gpt-oss:120b

Primary model changed from `qwen2.5:72b-instruct-q8_0` to `gpt-oss:120b`:

| Aspect | gpt-oss:120b | qwen2.5:72b-instruct-q8_0 |
|--------|--------------|---------------------------|
| Architecture | MoE (5.1B active) | Dense (22B all-active) |
| VRAM | ~60GB | ~75GB |
| Strengths | Agentic tasks, reasoning | General knowledge |

**Why gpt-oss:120b?**
- Optimized for agentic workflows and tool calling
- More efficient: 5.1B active parameters vs 22B
- Better suited for tool-calling patterns in Deep Agents

## Observability

### Langfuse Setup (Self-Hosted)

Langfuse runs as a sibling repo for LLM tracing and observability.

**Initial Setup:**
```bash
cd C:\Users\Nat\Documents\dev
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

**First Run:**
1. Open http://localhost:3000
2. Create account and project
3. Copy API keys to `.env` in ai-agents project:
   ```bash
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_HOST=http://localhost:3000
   ```

**Important:** Environment variables must be formatted exactly as shown (no spaces around `=`, no quotes around values). Use `LANGFUSE_HOST` not `LANGFUSE_BASE_URL`.

**Daily Usage:**
```bash
cd ../langfuse && docker compose up -d   # Start in background
cd ../langfuse && docker compose down    # Stop
```

**Upgrade:**
```bash
cd ../langfuse && git pull && docker compose up --pull always
```

### What Gets Traced

The LangChain CallbackHandler automatically captures:
- LLM calls (prompts, responses, token usage, latency)
- Tool invocations with inputs/outputs
- Agent decisions and flow
- Chain executions

### Adding Tracing to Code

The tracing module automatically loads `.env` before importing Langfuse (required because Langfuse reads environment variables at import time).

```python
from src.core.tracing import get_langfuse_handler

handler = get_langfuse_handler()
response = agent.invoke(
    {"messages": messages},
    config={"callbacks": [handler]}
)
```

View traces at: http://localhost:3000

## Design Principles

1. **YAGNI (You Aren't Gonna Need It)**: Only build what's needed for current phase
2. **Local First**: Optimize for running on local models (privacy, cost)
3. **Configuration Over Code**: Runtime behavior controlled via `.env`
4. **Type Safety**: Use Pydantic and type hints throughout

### Validation at Boundaries

Pydantic models validate data at system boundaries - where untrusted or external data enters the application:

| Boundary | Model | Purpose |
|----------|-------|---------|
| Environment variables | `Settings` | Validates config on startup (`HttpUrl` for URLs, `gt=0` for positive numbers) |
| YAML prompt files | `PromptConfig` | Ensures required `system_prompt` field exists |
| External APIs | `SearchResult` | Validates SearXNG responses, filters incomplete results |

**Pattern:**
```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    """Validates external API response."""
    title: str
    link: str
    snippet: str = ""

# Validate and filter - skip malformed data
results = []
for r in raw_api_response:
    try:
        results.append(SearchResult.model_validate(r))
    except ValidationError:
        continue  # Skip incomplete results
```

**Benefits:**
- Fail fast on invalid config (before agent runs)
- Type-safe access to validated data (e.g., `result.title` instead of `result.get("title")`)
- Self-documenting schemas for YAML files and API responses
- Graceful handling of malformed external data

## Next Steps

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for next development steps.
