# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project State

**Early development** - only foundation exists (config, LLM factory). No agents yet.

## Stack

- LangGraph (ReAct agents)
- Ollama/Qwen 2.5 for local models, Anthropic/OpenAI fallback
- Playwright (future - for web scraping)
- FastAPI (future - for API/scheduling)

## Structure

```
src/
├── agents/     # LangGraph graphs (empty - build next)
├── tools/      # Tool functions
├── core/       # config.py, llm.py
└── api/        # FastAPI (future)
```

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
- Tools are just functions - don't over-abstract
- Add service layer only when there's actual duplication

**Local models:**
- Tool descriptions must be clear (Qwen less capable than Claude)
- Handle tool call failures gracefully
- Start with `qwen2.5:7b`, upgrade when needed

## Anti-Patterns to Avoid

- Manager/orchestrator classes (use LangGraph directly)
- Config for features that don't exist yet
- Abstracting before there's duplication
- Documenting aspirational features as if they exist
