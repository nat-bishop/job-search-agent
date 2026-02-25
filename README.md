# AI Agents

An autonomous LLM agent system that searches for jobs, extracts content from career pages, and persists structured results — running entirely on local infrastructure. Built with LangGraph's ReAct agent loop, a 120B Mixture-of-Experts model (5.1B active parameters) via Ollama, and self-hosted SearXNG for web search.

## Architecture

```
run_job_search.py
 → create_job_search_agent()          # agent.py — factory
   → get_agent_llm()                  # llm.py — ChatOpenAI → Ollama /v1
   → load_prompt("main_agent")        # YAML with {current_date} injection
   → create_react_agent(model, tools, prompt)   # LangGraph ReAct loop
     → agent.astream()                # async streaming with tool calls
       ├─ web_search  → SearXNG      # tenacity retry, shift-left URL dedup
       ├─ fetch       → trafilatura   # layered extraction, Jina fallback
       ├─ add_job     → jobs.jsonl    # append-only, dedup by URL
       ├─ read_file   → data/        # sandboxed to data directory
       └─ ls          → data/
```

The LLM factory (`src/core/llm.py`) uses `ChatOpenAI` pointed at Ollama's `/v1` endpoint rather than `ChatOllama`. This is a deliberate choice: ChatOpenAI has more mature tool-call handling, and Ollama's OpenAI-compatible endpoint produces better tool message formatting. It avoids `tool_call_id` serialization bugs that surface with Qwen and Llama models through `ChatOllama`. Context length is detected on first use by querying Ollama's `/api/show` endpoint and cached per model via `@lru_cache`.

Prompts live in YAML files (`src/workflows/job_search/prompts/`), validated at load time through a `PromptConfig` Pydantic model. The `{current_date}` placeholder is injected before the agent starts, giving the LLM awareness of today's date for deadline reasoning.

Persistence follows an append-only pattern. `jobs.jsonl` is the source of truth — each `add_job()` call appends a single JSON line. At startup, `generate_jobs_markdown()` reads the JSONL, filters expired entries, and writes a derived `jobs.md`. The JSONL is never modified; expired jobs stay in the historical record.

## Agent and Tool Design

The design decisions here focus on making the LLM's job easier and the system more resilient to the ways LLM agents actually fail.

**Shift-left URL deduplication.** URLs are filtered out at three layers, all *before* the LLM reasons about them. `web_search` removes already-seen URLs from search results (`tools.py:191`), so the LLM never sees stale links. `fetch` checks `seen_urls.txt` before making HTTP requests (`tools.py:260`). `add_job` checks existing URLs in the JSONL before appending (`tools.py:433`). This saves tokens and eliminates an entire class of duplicate-reasoning bugs.

**Error strings, not exceptions.** Every tool returns a human-readable error string on failure — never raises into the agent loop. The messages include actionable guidance: `"Search failed after retries. Try a different query."`, `"Already fetched this URL. Use the content from earlier."` This lets the LLM recover and try alternative approaches rather than crashing the run.

**Two-layer tool documentation.** Tool docstrings contain only the schema: what the tool does, its arguments, and return type. All behavioral guidance — when to use the tool, search strategy, query patterns — lives in the YAML system prompt. This separation keeps tools reusable across workflows while giving each workflow full control over how tools are used.

**Layered content extraction.** The `fetch` tool implements a pipeline: MIME detection via `filetype.guess()`, then PDF extraction (`pymupdf4llm` → markdown), or HTML extraction (`trafilatura` with `favor_recall=True` → `BeautifulSoup` fallback). On 403 errors, `_classify_403()` inspects response headers (`cf-ray`, `retry-after`, `x-ratelimit-*`) to categorize the block, then routes Cloudflare-blocked pages to Jina Reader as a fallback. Output is Unicode-normalized, emoji-stripped, and truncated to 5000 words.

**Persist-as-you-go.** The system prompt explicitly instructs the agent to call `add_job()` immediately for each finding, not accumulate results and save at the end. This addresses a real failure mode: LLMs lose information over long tool-use chains. Immediate persistence means a crash at step 12 doesn't lose the jobs found in steps 3-11.

**Async tools for parallel execution.** `web_search` and `fetch` are `async def`, which means when the LLM emits multiple tool calls in a single response, they execute concurrently. The runner uses `agent.astream()` throughout.

**Rate limiting and retry.** `web_search` adds a random 2-4 second delay before each SearXNG query to avoid triggering upstream rate limits. The underlying `_searxng_search()` uses `tenacity` for exponential backoff retry (3 attempts, up to 10 seconds). Search results are over-fetched by a configurable buffer (`search_result_buffer: 2.0`) to compensate for URL deduplication reducing the result count.

## Observability

Tracing uses Langfuse with two layers of instrumentation. A `CallbackHandler` (`src/core/tracing.py`) captures the full agent loop — every LLM call, tool invocation, and message. `web_search` additionally uses Langfuse's `@observe` decorator for a fine-grained span with custom metadata, logging `results_original`, `results_after_filter`, and `seen_urls_filtered` as span metrics to track deduplication effectiveness across runs.

Structured logging (`src/core/logging.py`) uses `structlog` with configurable output: colored console for development (`json_logs=False`) or JSON to both console and file (`logs/ai-agents.jsonl`) for machine parsing. Trace correlation is async-safe via `structlog.contextvars` — calling `bind_trace_id()` at the start of a run means every log message in that async context includes the Langfuse trace ID, enabling cross-referencing between logs and traces.

Both systems degrade gracefully. If Langfuse credentials aren't configured, `get_langfuse_handler()` returns `None` and the agent runs without tracing. No code paths depend on observability being present.

## Code Quality

Static analysis runs on every commit via pre-commit hooks: `ruff` for linting and formatting, `mypy` in strict mode (`strict = true`, `warn_return_any = true`). Claude Code hooks run `ruff --fix` on every file write for immediate feedback, implemented as PEP 723 UV single-file scripts with embedded dependencies.

Pydantic validates data at system boundaries: `Settings` (`.env` config with `HttpUrl` validation), `PromptConfig` (YAML prompt structure), and `SearchResult` (SearXNG API responses — filters incomplete results from an upstream wrapper bug).

## Project Structure

```
src/
├── core/                          # Shared infrastructure
│   ├── config.py                  # Pydantic Settings from .env
│   ├── llm.py                     # LLM factory (ChatOpenAI → Ollama)
│   ├── tracing.py                 # Langfuse handler (optional)
│   └── logging.py                 # structlog + trace correlation
├── workflows/job_search/          # Job search workflow
│   ├── agent.py                   # Agent factory, prompt loading, memory management
│   ├── tools.py                   # web_search, fetch, add_job, read_file, ls
│   └── prompts/main_agent.yaml    # System prompt with {current_date} injection
└── data/memories/                 # Persistent state (JSONL, seen URLs)
```

## Getting Started

Requires Python 3.11+, Docker, and an NVIDIA GPU with ~60GB VRAM.

```bash
git clone https://github.com/nat-bishop/ai-agents.git && cd ai-agents
docker compose up -d                                    # Ollama + SearXNG
docker compose exec ollama ollama pull gpt-oss:120b     # 65GB download
uv sync --extra dev                                     # Install dependencies
uv run python scripts/run_job_search.py                 # Run the agent
```

See [CLAUDE.md](CLAUDE.md) for detailed configuration, alternative setup options, and development workflow.

## License

MIT
