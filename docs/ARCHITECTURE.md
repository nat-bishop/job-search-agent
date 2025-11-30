# Architecture

This document describes the current architecture of the AI Agents project.

## Current State: Foundation Only

The project is in early development (Phase 1 complete). Only core infrastructure exists - no agents have been built yet.

## Directory Structure

```
src/
├── core/           # Core infrastructure (✓ IMPLEMENTED)
│   ├── config.py   # Pydantic settings from .env
│   └── llm.py      # LLM factory with provider swapping
├── agents/         # LangGraph agents (EMPTY - Phase 2+)
├── tools/          # Tool functions for agents (EMPTY - Phase 2+)
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

### Agents (Phase 2+)

Will use LangGraph's `create_react_agent` pattern:
- ReAct loop: Reasoning → Action → Observation
- Tool calling via LangChain tools
- State management via LangGraph checkpointing

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for the roadmap.

### Tools (Phase 2+)

Will be LangChain-compatible tool functions:
- Web search (via Exa API)
- Browser automation (via Playwright)
- Data storage/retrieval

### Services (Phase 3+)

Will encapsulate external integrations:
- Browser service with safe Playwright commands
- Storage service (SQLite)
- Email service (future)

**Philosophy**: Extract services when there's duplication, not before. First agent will call APIs directly.

### API (Phase 4+)

Will be a FastAPI server for:
- Running agents on demand
- Scheduling periodic runs
- Viewing agent results
- Monitoring agent status

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
