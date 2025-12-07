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
│       ├── agent.py     # create_deep_agent with prompt loading
│       ├── tools.py     # Tools specific to this workflow
│       └── prompts/     # YAML prompt files
│           ├── main_agent.yaml
│           └── {subagent}.yaml
└── core/       # config.py, llm.py, tracing.py
```

Multi-agent workflows add:
- `graph.py` - Entrypoint defining how agents connect
- `agents/` - Individual agent files
- `tools/` - Shared tools for the domain

## Key Files

- `src/core/config.py` → `settings` object, loads from `.env`
- `src/core/llm.py` → `get_llm()` factory for local Ollama models
- `src/core/tracing.py` → `get_langfuse_handler()` for LLM tracing (optional)

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

# Docker services (Ollama + SearXNG)
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
- Long-term memory via FilesystemBackend (stores in `/memories/` directory)
- Tools return error strings for LLM-recoverable failures (not exceptions)
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#deep-agents) for detailed patterns

**Tool design pattern:**
- Tool docstrings: minimal - describe what it does, args, returns (schema only)
- System prompt: contains tool usage guidance (when/how to use)
- This two-layer pattern matches Deep Agents quickstart and keeps tools portable
- Example: `web_search` docstring says "Search the web", system prompt says "Use for current events and research"

**YAML prompts with variable injection:**
- Store prompts in `prompts/*.yaml` files for easy iteration
- Use `{current_date}` placeholder - replaced at load time with today's date
- Load with `load_prompt()` function in agent.py
- Example YAML:
  ```yaml
  system_prompt: |
    Today's date: {current_date}
    You are a job search assistant...
  ```

**Simple task triggers:**
- Run scripts should use simple task messages: `"Search for new jobs and update your files."`
- System prompt handles all details (file paths, workflow, formatting)
- Avoids conflicts between task and system prompt instructions
- Let the agent follow its system prompt, don't repeat instructions in the task

**Async execution:**
- If any tool is `async def`, the runner MUST use async methods (`astream`/`ainvoke`)
- Sync `stream()`/`invoke()` with async tools raises: "StructuredTool does not support sync invocation"
- Async tools enable parallel execution when LLM calls multiple tools at once
- Pattern for async runner:
  ```python
  async def main():
      async for event in agent.astream({"messages": [...]}, config={...}):
          handle_event(event)

  asyncio.run(main())
  ```

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

# Async (use with async tools)
async for event in agent.astream(
    {"messages": messages},
    config={"callbacks": [handler]}
):
    handle_event(event)

# Sync (only if all tools are sync)
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
- Main agent delegates to `research` subagent for web searches (SearXNG)
- Persistent memory in `/memories/` survives across runs (FilesystemBackend)
- Agent tracks seen jobs to report only NEW findings
- Prompts stored in YAML with `{current_date}` injection

**Key files:**
- `src/workflows/job_search/agent.py` - Main agent + research subagent, loads YAML prompts
- `src/workflows/job_search/tools.py` - web_search (SearXNG), fetch_page (Playwright)
- `src/workflows/job_search/prompts/` - YAML prompt files
- `scripts/run_job_search.py` - Entry point (simple task trigger)

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
- Verbose task messages that duplicate system prompt (use simple triggers)
- Hardcoding prompts in Python (use YAML files for easy iteration)
