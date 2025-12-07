# Implementation Plan

Living document tracking progress on the AI Agents project. High-level to allow flexibility during implementation.

## Current Focus

**Phase 1: Foundation** - COMPLETE

**Phase 2: First Workflow** - COMPLETE

**Phase 2.5: Deep Agents Adoption** - IN PROGRESS

**Phase 2.7: Containerization** - COMPLETE

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
- [x] src/core/llm.py - LLM factory for local Ollama models
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
  - `web_search` - uses SearXNG (self-hosted metasearch)
- [x] scripts/test_simple_agent.py - Interactive test script
- [x] Verify tool calling works with local Qwen 2.5

### SearXNG Setup (for web_search tool)
SearXNG provides self-hosted web search. Setup:
1. Copy config: `cp searxng/settings.yml.example searxng/settings.yml`
2. Generate secret: `python -c "import secrets; print(secrets.token_hex(32))"`
3. Start services: `docker compose up -d`

SearXNG runs in Docker alongside Ollama.

### Validation
- [x] Agent reasons and picks correct tool
- [x] Agent loops: tool → observe → decide
- [x] Agent knows when to stop
- [ ] Test with both local and API models

---

## Phase 2.5: Deep Agents Adoption

Goal: Migrate to deep agents framework for subagent support and context management, using local models.

### Setup
- [x] Add `deepagents` to pyproject.toml
- [x] Test deep agents with local model via Ollama

### Migration
- [x] Convert simple workflow from `create_react_agent` to `create_deep_agent`
- [ ] Verify built-in tools (write_todos, filesystem) work with local model
- [x] Test subagent delegation with local model
- [ ] Test memory stored long term (currently using InMemoryStore)

### Research Subagent
- [x] Add research subagent to simple workflow
- [x] Configure long-term memory with CompositeBackend
- [x] Configure for context isolation (results summarized, not raw)
- [x] Validate with web_search tool

### Documentation
- [x] Update ARCHITECTURE.md with deep agents patterns
- [x] Update to two-layer tool documentation pattern (minimal docstrings, system prompt has usage)
- [x] Add deep agents resources to Resources section

---

## Phase 2.7: Containerization

Goal: Containerize Ollama with GPU access to prepare for Phase 4 concurrency requirements.

### Container Setup
- [x] docker-compose.yml - Ollama service with GPU passthrough
- [x] .gitignore - Exclude .ollama-data/ directory
- [x] Migrate gpt-oss:120b model to .ollama-data/
- [x] Start and verify Ollama container
- [x] Test Python app with containerized Ollama

### Infrastructure
- [x] WSL2 + Docker Desktop configuration
- [x] NVIDIA Container Toolkit setup (Docker Desktop handles this)
- [x] GPU passthrough verification

### Documentation
- [x] Update README.md with Docker setup instructions
- [x] Update CLAUDE.md with containerized architecture
- [x] Add troubleshooting guide for common Docker issues (deferred - not needed yet)

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

Goal: Run agents on schedules with proper concurrency control to prevent GPU resource conflicts.

### Concurrency Architecture

**Problem:** With 96GB VRAM and 65-77GB models, concurrent workflows cause GPU OOM errors.

**Solution:** Redis queue + worker pattern for serialized Ollama access.

```yaml
services:
  ollama:      # Isolated GPU access (containerized)
  scheduler:   # APScheduler pushes jobs to queue
  redis:       # Job queue (serializes GPU requests)
  worker:      # Pulls from queue, runs one agent at a time
```

### FastAPI Server
- [ ] src/api/main.py - App entry point with scheduler
- [ ] src/api/routes/agents.py - Trigger/status endpoints
- [ ] src/api/routes/jobs.py - View found jobs
- [ ] src/api/dependencies.py - Compiled graphs, services

### Scheduling & Queue
- [ ] Add Redis to docker-compose.yml
- [ ] src/core/scheduler.py - APScheduler integration
- [ ] src/core/queue.py - Redis queue client wrapper
- [ ] src/core/worker.py - Worker process for agent execution
- [ ] config/schedules.yaml - Cron schedules per agent

### Resource Management
- [ ] GPU access serialization via queue
- [ ] Container resource limits (memory, CPU)
- [ ] Worker pool configuration (start with 1 worker = serial execution)

### Monitoring
- [ ] src/core/monitoring.py - Run tracking, metrics
- [ ] SQLite for run history
- [ ] Structured logging with run IDs
- [ ] Queue depth/status endpoint

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
- [ ] Research agent (enhanced web search capabilities)
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
| Deep agents for subagents | Context isolation, built-in planning/filesystem tools | 2024-11-30 |
| Local-first for deep agents | Privacy, cost; cloud fallback if needed | 2024-11-30 |
| Two-layer tool docs | Minimal tool docstrings, system prompt has usage guidance | 2024-11-30 |
| Containerize Ollama | Prepare for Phase 4 concurrency, GPU resource isolation | 2024-11-30 |
| Redis queue for Phase 4 | Prevent GPU OOM with 65-77GB models running concurrently | 2024-11-30 |
| gpt-oss:120b as primary | Newer (Aug 2025), better for agents, 5.1B active vs 22B | 2024-11-30 |

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
- [Deep Agents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Deep Agents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [Deep Agents Long-Term Memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory)
- [Qwen 2.5 Tool Calling](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
- [SearXNG Documentation](https://docs.searxng.org/)
- [Docker: Local LLM Tool Calling](https://www.docker.com/blog/local-llm-tool-calling-a-practical-evaluation/)
