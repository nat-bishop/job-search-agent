# Implementation Plan

Living document tracking progress on the AI Agents project. High-level to allow flexibility during implementation.

## Current Focus

**Phase 1: Foundation** - COMPLETE

**Phase 2: First Workflow** - COMPLETE

---

## Phase 1: Foundation

### Setup & Config
- [x] README.md - Project overview and quick start
- [x] IMPLEMENTATION_PLAN.md - This document
- [x] pyproject.toml - Dependencies (LangGraph, LangChain, FastAPI, Playwright, etc.)
- [x] .env.example - Environment variable template
- [x] .gitignore - Standard Python + secrets

### Core Infrastructure
- [x] src/core/config.py - Pydantic settings (LLM provider, API keys, paths)
- [x] src/core/llm.py - LLM factory with provider swapping (Ollama ↔ Anthropic)
- [x] Directory structure with `__init__.py` files

### Claude Code Agents
- [x] Update code-explorer.md for ai-agents project
- [x] Update code-reviewer.md with LangGraph patterns
- [x] Update doc-drafter.md with new file list
- [x] Create playwright-scout.md for discovering safe browser commands

---

## Phase 2: First Workflow

Goal: Get ONE simple workflow working end-to-end. Keep it minimal.

### Local Model Setup
- [x] Install Ollama from https://ollama.com/download
- [x] Pull model: `ollama pull qwen2.5:7b`
- [x] Verify running: `curl http://localhost:11434/api/tags`

### Simple Test Workflow
- [x] src/workflows/simple/agent.py - ReAct agent using `create_react_agent`
- [x] src/workflows/simple/tools.py - Two simple tools:
  - `get_current_time` - no deps, just returns time
  - `web_search` - calls Exa directly (no service layer yet)
- [x] scripts/test_simple_agent.py - Interactive test script
- [x] Verify tool calling works with local Qwen 2.5

### Exa SDK Setup (for web_search tool)
Exa provides neural web search. Setup when needed:
1. Get API key from https://exa.ai
2. Add to `.env`: `EXA_API_KEY=your-key-here`
3. The `web_search` tool will work automatically

For now, testing uses only `get_current_time` (no API key required).

### Validation
- [x] Agent reasons and picks correct tool
- [x] Agent loops: tool → observe → decide
- [x] Agent knows when to stop
- [ ] Test with both local and API models

---

## Phase 3: Job Search Workflow

Goal: Build the nursing job search workflow with safe Playwright commands.

### Discovery (using Playwright MCP)
- [ ] Identify target job boards (Indeed, hospital career pages, etc.)
- [ ] Document CSS selectors and navigation patterns
- [ ] Create safe, parameterized Playwright functions

### Implementation
- [ ] src/workflows/job_search/agent.py - Job search agent
- [ ] src/workflows/job_search/tools.py - Job board tools (search, filter, save)
- [ ] src/services/browser.py - Playwright service with safe commands
- [ ] src/services/storage.py - SQLite for tracking found jobs
- [ ] config/job_boards.yaml - Configurable board URLs/selectors

### Features
- [ ] Search multiple boards
- [ ] Deduplicate results
- [ ] Filter by criteria (new grad, location, etc.)
- [ ] Save results to database

---

## Phase 4: API & Scheduling

Goal: Run agents on schedules, expose via API.

### FastAPI Server
- [ ] src/api/main.py - App entry point
- [ ] src/api/routes/agents.py - Run/status endpoints
- [ ] src/api/routes/jobs.py - View found jobs
- [ ] src/api/dependencies.py - Compiled graphs, services

### Scheduling
- [ ] src/core/scheduler.py - APScheduler integration
- [ ] config/schedules.yaml - Cron schedules per agent

### Monitoring
- [ ] src/core/monitoring.py - Run tracking, metrics
- [ ] SQLite for run history
- [ ] Structured logging with run IDs

---

## Phase 5: Multi-Agent Workflows

Goal: Build workflows with multiple coordinated agents.

### Patterns to Support
- Supervisor → Workers (hierarchical)
- Pipeline (sequential handoffs)
- Conditional routing (graph-based)

### Example: Email Workflow
- [ ] src/workflows/email/graph.py - Entrypoint, defines agent connections
- [ ] src/workflows/email/agents/drafter.py - Writes drafts
- [ ] src/workflows/email/agents/reviewer.py - Reviews before sending
- [ ] src/workflows/email/tools/gmail.py - Gmail API tools

---

## Future Ideas (Backlog)

Not planned yet, add as needed:

- [ ] Email agent (Gmail integration)
- [ ] Calendar agent
- [ ] Research agent (deep web search with Exa)
- [ ] vLLM upgrade (for better tool calling streaming)
- [ ] Web UI for monitoring
- [ ] Human-in-the-loop approval flows
- [ ] Memory/RAG for context across sessions

---

## Notes & Decisions

### Terminology

| Term | Definition |
|------|------------|
| **Agent** | Autonomous unit with its own system prompt and tools |
| **Workflow** | Collection of agents working together on a domain |
| **Orchestrator** | Agent that coordinates others (supervisor, router, etc.) |

### Architecture Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Qwen 2.5 for local | Best tool calling F1 score (0.93) | 2024-11-29 |
| Ollama first, vLLM later | Simpler setup, can upgrade | 2024-11-29 |
| Safe Playwright commands | Security - no arbitrary browser access | 2024-11-29 |
| Delay service layer | Don't abstract until there's duplication | 2024-11-29 |
| Workflows over flat agents | Colocate agents + tools by domain | 2024-11-29 |

### Lessons Learned

1. **Don't document what doesn't exist** - README should reflect reality. Use "Roadmap" for future.

2. **Config only for what's built** - Started with 139-line config with DB paths, API server, LangSmith. Cut to 45 lines.

3. **Service layer is premature** - Tools can call APIs directly for first agent. Extract when there's duplication.

4. **Start with small model** - `qwen2.5:7b` for dev, 72b when needed. Faster iteration.

5. **CLAUDE.md must be accurate** - Only describe what exists. Concise for context efficiency.

---

## Resources

- [LangGraph Docs](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph ReAct Template](https://github.com/langchain-ai/react-agent)
- [LangGraph Supervisor](https://github.com/langchain-ai/langgraph-supervisor-py)
- [Qwen 2.5 Tool Calling](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
- [Exa Python SDK](https://github.com/exa-labs/exa-py)
- [Docker: Local LLM Tool Calling](https://www.docker.com/blog/local-llm-tool-calling-a-practical-evaluation/)
