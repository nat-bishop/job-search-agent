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
pip install -e ".[dev]"    # Install/update deps
ruff check src/            # Lint
mypy src/                  # Type check
```

## Principles

**Keep it simple:**
- This is a personal project, not enterprise software
- Don't abstract until there's duplication (Rule of Three)
- If it feels complex, find a simpler approach
- YAGNI - don't build what we don't need yet

**Deep agents:**
- Use `create_deep_agent` as the standard pattern
- System prompt via `prompt` parameter
- Tools are colocated with their workflow
- Use subagents for delegation (e.g., research subagent)
- Built-in tools for Langgraph deep agents: write_todos, filesystem (ls, read_file, write_file, edit_file)
- Long-term memory via CompositeBackend (path routing)
- Tools return error strings for LLM-recoverable failures (not exceptions)
- Add service layer only when there's actual duplication
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#deep-agents) for detailed patterns

**Tool design pattern:**
- Tool docstrings: minimal - describe what it does, args, returns (schema only)
- System prompt: contains tool usage guidance (when/how to use)
- This two-layer pattern matches Deep Agents quickstart and keeps tools portable
- Example: `web_search` docstring says "Search web using Exa", system prompt says "Use for current events and research"

**Local models:**
- Using `qwen2.5:72b-instruct-q8_0` via Ollama
- Handle tool call failures gracefully

## Anti-Patterns to Avoid

- Manager/orchestrator classes (use LangGraph directly)
- Config for features that don't exist yet
- Abstracting before there's duplication
- Flat tools/ directory separate from agents
- Documenting aspirational features as if they exist
