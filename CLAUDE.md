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
│       ├── agent.py   # create_react_agent with state_modifier
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

## Commands

```bash
pip install -e ".[dev]"    # Install
ruff check src/            # Lint
mypy src/                  # Type check
```

## Principles

**Keep it simple:**
- This is a personal project, not enterprise software
- Don't abstract until there's duplication (Rule of Three)
- If it feels complex, find a simpler approach
- YAGNI - don't build what we don't need yet

**LangGraph patterns:**
- Use `create_react_agent` for simple agents
- System prompt via `state_modifier` parameter
- Tools are colocated with their workflow
- Add service layer only when there's actual duplication

**Local models:**
- Tool descriptions must be clear (Qwen less capable than Claude)
- Handle tool call failures gracefully
- Start with `qwen2.5:7b`, upgrade when needed

## Anti-Patterns to Avoid

- Manager/orchestrator classes (use LangGraph directly)
- Config for features that don't exist yet
- Abstracting before there's duplication
- Flat tools/ directory separate from agents
- Documenting aspirational features as if they exist
