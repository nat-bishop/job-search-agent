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
│   ├── llm.py      # LLM factory with provider swapping
│   └── tracing.py  # Langfuse integration
├── workflows/      # Agent workflows by domain
│   └── simple/     # Single-agent test workflow
├── services/       # External service integrations (empty)
└── api/            # FastAPI server (empty)
```

## Implemented Components

### Configuration (`src/core/config.py`)

Environment-based configuration using Pydantic Settings:

- **LLM Provider Selection**: Choose between local (Ollama), Anthropic, or OpenAI
- **Model Configuration**: Set model names and API keys per provider
- **External APIs**: Placeholder for service API keys (e.g., Exa for web search)

Configuration is loaded from `.env` file. See `.env.example` for all available options.

**Design decisions:**
- Settings-based rather than hard-coded to support easy provider switching
- Enum-based provider type for type safety
- Minimal - only includes what's needed for current implementation

### LLM Factory (`src/core/llm.py`)

Factory pattern for creating LLM instances:

```python
from src.core.llm import get_llm

# Use default provider from .env
llm = get_llm()

# Override to use Anthropic
llm = get_llm("anthropic")

# For agent use (temperature=0.0)
llm = get_agent_llm()
```

**Supported providers:**
- **Local (Ollama)**: Default, optimized for Qwen 2.5 with tool calling support
- **Anthropic**: Claude Sonnet 4 for fallback/comparison
- **OpenAI**: GPT-4 for fallback/comparison

**Design decisions:**
- Returns LangChain `BaseChatModel` for compatibility with LangGraph
- Late imports to avoid loading unused provider libraries
- Provider-specific configuration encapsulated in private functions
- Cached `get_default_llm()` for efficiency in single-provider scenarios

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
def web_search(query: str) -> str:
    """Search the web using Exa neural search.

    Args:
        query: Natural language search query

    Returns:
        Search results with titles, URLs, and content snippets
    """
    # Implementation...
```

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

agent = create_deep_agent(
    model=get_llm(),
    tools=[custom_tool],
    system_prompt="You are a helpful assistant..."
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

# Define subagent as a dictionary
RESEARCH_SUBAGENT = {
    "name": "research",
    "description": "Searches the web and synthesizes information.",
    "system_prompt": "You are a research specialist...",
    "tools": [web_search],
}

# Main agent delegates to subagent via task() tool
main_agent = create_deep_agent(
    model=get_llm(),
    tools=[get_current_time],
    subagents=[RESEARCH_SUBAGENT],
    system_prompt="You coordinate research tasks..."
)
```

### Long-term Memory

Deep agents support persistent memory via `CompositeBackend` with path-based routing:

| Path | Storage Type | Use Case |
|------|--------------|----------|
| `/memories/` | Persistent | Facts, preferences, learned information |
| `/workspace/` | Ephemeral | Scratch space, temporary working data |

Memory is automatically managed - agents read/write to paths and the backend routes to appropriate storage.

## Workflow Structure

Each workflow is a subdirectory containing:
- `agent.py` - Deep agent with system prompt via `prompt` parameter
- `tools.py` - Tools specific to that workflow

```python
# src/workflows/simple/agent.py
agent = create_deep_agent(
    model=get_llm(),
    tools=[get_current_time],
    prompt="You are a helpful assistant..."
)
```

## Technology Stack

- Python 3.11+
- LangGraph (agent framework)
- LangChain Core (LLM abstraction)
- Pydantic Settings (configuration)
- Ollama (local LLM serving, containerized)
- Docker (optional, for Ollama with GPU passthrough)

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
| Release | Aug 2025 | Mar 2024 |
| Architecture | MoE (5.1B active) | Dense (22B all-active) |
| VRAM | ~60GB | ~75GB |
| Strengths | Agentic tasks, reasoning | General knowledge |

**Why gpt-oss:120b?**
- Newer model with improvements for agentic workflows
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
2. **Provider Agnostic**: Support local and cloud LLMs interchangeably
3. **Local First**: Optimize for running on local models (privacy, cost)
4. **Configuration Over Code**: Runtime behavior controlled via `.env`
5. **Type Safety**: Use Pydantic and type hints throughout

## Next Steps

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for next development steps.
