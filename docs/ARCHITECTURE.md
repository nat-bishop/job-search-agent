# Architecture

This document describes the current architecture of the AI Agents project.

## Current State: First Agent Working

The project is in early development (Phase 2 complete). Core infrastructure and a simple test workflow exist.

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
│   └── llm.py      # LLM factory with provider swapping
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

### Tool Design

For local models (Qwen), tool descriptions must be explicit:

```python
@tool
def example_tool(query: str) -> str:
    """One-line summary of what this tool does.

    Use this tool when the user asks about:
    - Specific scenario 1
    - Specific scenario 2

    Args:
        query: Description of expected input

    Returns:
        Description of output format
    """
```

Validation order in tools:
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

## Workflow Structure

Each workflow is a subdirectory containing:
- `agent.py` - Agent with system prompt via `prompt` parameter
- `tools.py` - Tools specific to that workflow

```python
# src/workflows/simple/agent.py
agent = create_react_agent(
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
- Ollama (local LLM serving)

## Design Principles

1. **YAGNI (You Aren't Gonna Need It)**: Only build what's needed for current phase
2. **Provider Agnostic**: Support local and cloud LLMs interchangeably
3. **Local First**: Optimize for running on local models (privacy, cost)
4. **Configuration Over Code**: Runtime behavior controlled via `.env`
5. **Type Safety**: Use Pydantic and type hints throughout

## Next Steps

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for next development steps.
