# Architecture

This document describes the current architecture of the AI Agents project.

## Current State: Foundation Only

The project is in early development (Phase 1 complete). Only core infrastructure exists - no agents have been built yet.

## Terminology

| Term | Definition |
|------|------------|
| **Agent** | Autonomous unit with its own system prompt and tools |
| **Workflow** | Collection of agents working together on a domain |
| **Orchestrator** | Agent that coordinates others (supervisor, router, etc.) |

## Directory Structure

```
src/
├── core/           # Shared infrastructure (✓ IMPLEMENTED)
│   ├── config.py   # Pydantic settings from .env
│   └── llm.py      # LLM factory with provider swapping
├── workflows/      # Agent workflows by domain (EMPTY - Phase 2+)
│   ├── simple/     # Single-agent workflow (Phase 2)
│   ├── job_search/ # Job search workflow (Phase 3)
│   └── email/      # Multi-agent email workflow (Phase 5)
├── services/       # External service integrations (EMPTY - Phase 3+)
└── api/            # FastAPI server (EMPTY - Phase 4+)
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

## Planned Architecture (Not Yet Implemented)

The following components are planned but **do not exist yet**. This section exists only to provide context for future development.

### Workflows (Phase 2+)

Each workflow is a subdirectory containing:
- `agent.py` - Agent with system prompt via `state_modifier`
- `tools.py` - Tools specific to that workflow

For multi-agent workflows:
- `graph.py` - Entrypoint defining how agents connect
- `agents/` - Individual agent files
- `tools/` - Shared tools for the domain

```python
# Single-agent workflow (Phase 2)
# src/workflows/simple/agent.py
agent = create_react_agent(
    model=get_llm(),
    tools=[get_current_time, web_search],
    state_modifier="You are a helpful assistant..."
)

# Multi-agent workflow (Phase 5)
# src/workflows/email/graph.py
builder = StateGraph(EmailState)
builder.add_node("drafter", drafter_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_edge("drafter", "reviewer")
```

### Multi-Agent Patterns

Workflows can use different orchestration patterns:
- **Supervisor → Workers**: One agent routes to others as tools
- **Pipeline**: Sequential handoffs (A → B → C)
- **Conditional routing**: Graph-based branching
- **Peer collaboration**: Agents interact without hierarchy

### Services (Phase 3+)

Will encapsulate external integrations:
- Browser service with safe Playwright commands
- Storage service (SQLite)
- Email service (future)

**Philosophy**: Extract services when there's duplication, not before. First agent will call APIs directly.

### API (Phase 4+)

Will be a FastAPI server for:
- Running workflows on demand
- Scheduling periodic runs
- Viewing workflow results
- Monitoring status

## Technology Stack

**Current:**
- Python 3.12+
- LangChain Core (LLM abstraction)
- Pydantic Settings (configuration)
- Ollama (local LLM serving)

**Future (when needed):**
- LangGraph (agent framework)
- FastAPI (API server)
- Playwright (browser automation)
- APScheduler (scheduling)
- SQLite (storage)

## Design Principles

1. **YAGNI (You Aren't Gonna Need It)**: Only build what's needed for current phase
2. **Provider Agnostic**: Support local and cloud LLMs interchangeably
3. **Local First**: Optimize for running on local models (privacy, cost)
4. **Configuration Over Code**: Runtime behavior controlled via `.env`
5. **Type Safety**: Use Pydantic and type hints throughout

## Next Steps

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) Phase 2 for next development steps.
