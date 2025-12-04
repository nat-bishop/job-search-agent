# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Terminology

| Term | Definition |
|------|------------|
| **Agent** | Autonomous unit with its own system prompt and tools |
| **Workflow** | Collection of agents working together on a domain |
| **Orchestrator** | Agent that coordinates others (supervisor, router, etc.) |

## Structure

```
src/
├── workflows/  # Agent workflows by domain
│   └── {name}/
│       ├── agent.py   # create_deep_agent with prompt
│       └── tools.py   # Tools specific to this workflow
├── core/       # config.py, llm.py
├── services/   # External integrations (when needed)
└── api/        # FastAPI (future)
```

Multi-agent workflows add:
- `graph.py` - Entrypoint defining how agents connect
- `agents/` - Individual agent files
- `tools/` - Shared tools for the domain

## Key Files

- `src/core/config.py` → `settings` object, loads from `.env`
- `src/core/llm.py` → `get_llm()` factory, supports local/anthropic/openai
- `src/core/tracing.py` → `get_langfuse_handler()` for LLM tracing

## Environment Setup

Requires Python 3.11 or 3.12 (not 3.14 - LangChain incompatible).

```powershell
# Create venv (first time)
python -m venv .venv

# Activate venv (every session)
.venv\Scripts\Activate.ps1    # PowerShell
.venv\Scripts\activate.bat    # CMD
source .venv/bin/activate     # Git Bash / Linux

# Install dependencies
pip install -e ".[dev]"
```

## Commands

```bash
pip install -e ".[dev]"       # Install/update deps
ruff check src/               # Lint
mypy src/                     # Type check

# Docker services (Ollama + PostgreSQL)
docker compose up -d          # Start all containers
docker compose down           # Stop containers
docker compose exec ollama ollama pull gpt-oss:120b  # Pull model

# Run job search workflow
python scripts/run_job_search.py
```

## Principles

**Keep it simple:**
- This is a personal project, not enterprise software
- Don't abstract until there's duplication (Rule of Three)
- If it feels complex, find a simpler approach
- YAGNI - don't build what we don't need yet

**Deep agents:**
- Use `create_deep_agent` as the standard pattern
- System prompt via `system_prompt` parameter
- Tools are colocated with their workflow
- Use subagents for delegation (e.g., research subagent)
- Built-in tools: write_todos, filesystem (ls, read_file, write_file, edit_file)
- Long-term memory via CompositeBackend + PostgresStore (path routing to `/memories/`)
- Tools return error strings for LLM-recoverable failures (not exceptions)
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#deep-agents) for detailed patterns

**Tool design pattern:**
- Tool docstrings: minimal - describe what it does, args, returns (schema only)
- System prompt: contains tool usage guidance (when/how to use)
- This two-layer pattern matches Deep Agents quickstart and keeps tools portable
- Example: `web_search` docstring says "Search web using Exa", system prompt says "Use for current events and research"

**Local models:**
- Primary model: `gpt-oss:120b` via Ollama (containerized)
- Ollama runs in Docker container with GPU passthrough
- Models persist in `.ollama-data/` volume (65GB+)
- Python app runs on host, connects to localhost:11434
- Handle tool call failures gracefully

## Observability

Uses [Langfuse](https://langfuse.com) for LLM tracing. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#observability) for setup.

### Adding Tracing to New Code

```python
from src.core.tracing import get_langfuse_handler

handler = get_langfuse_handler()
response = agent.invoke(
    {"messages": messages},
    config={"callbacks": [handler]}
)
```

Note: `tracing.py` loads `.env` via dotenv before importing Langfuse (required - Langfuse reads env vars at import time).

View traces: http://localhost:3000

## Job Search Workflow

The main workflow finds new grad RN jobs in the Bay Area:

```bash
# Prerequisites: Docker services running
docker compose up -d

# Run the job search
python scripts/run_job_search.py
```

**Architecture:**
- Main agent delegates to `research` subagent for web searches (Exa API)
- Persistent memory in `/memories/` survives across runs (PostgresStore)
- Agent tracks seen jobs to report only NEW findings

**Key files:**
- `src/workflows/job_search/agent.py` - Main agent + research subagent
- `src/workflows/job_search/tools.py` - web_search tool (Exa)
- `scripts/run_job_search.py` - Entry point

## Windows Console Encoding

When printing LLM output to Windows console, handle unicode characters:

```python
# Avoid: print(response.content)  # May fail with charmap codec error
# Use:
content = response.content.encode('ascii', 'replace').decode('ascii')
print(content)
```

## Anti-Patterns to Avoid

- Manager/orchestrator classes (use LangGraph directly)
- Config for features that don't exist yet
- Abstracting before there's duplication
- Flat tools/ directory separate from agents
- Documenting aspirational features as if they exist
