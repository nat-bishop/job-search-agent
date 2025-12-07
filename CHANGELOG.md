# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Auto-detection of model context length for summarization (`get_model_context_length()` in llm.py)
  - Queries Ollama API for model's context_length at startup
  - Sets `model.profile["max_input_tokens"]` for LangChain middleware
  - Cached per model name for efficiency
  - Falls back to 131072 if query fails
- `time_range` parameter for `web_search` tool (day, week, month, year)
  - Filters search results to recent timeframes via SearXNG API
  - Useful for finding recent job postings
- PDF support in `fetch` tool via pymupdf/pymupdf4llm
  - Converts PDF documents to Markdown for LLM processing
  - Auto-detects PDF content type from response bytes
- Tool aliases for model robustness
  - `search` is an alias for `web_search`
  - `fetch_page` is an alias for `fetch`
  - Prevents tool-not-found errors when different LLMs use different naming conventions
- URL normalization in `fetch` tool (auto-prepends `https://` if missing)
- Reddit URL rewriting in `fetch` tool (reddit.com -> old.reddit.com for better scraping)
- Text cleaning utilities (unicode normalization, emoji removal, whitespace collapse)
- Word-based truncation (5000 words) instead of character-based for more predictable LLM token usage
- Job search workflow (`src/workflows/job_search/`)
  - Main agent delegates to research subagent for web searches
  - SearXNG integration for self-hosted web search (replaces Exa)
  - Persistent memory via FilesystemBackend (stores in `data/` directory)
  - YAML-based prompts with `{current_date}` injection
  - Memory file initialization on agent startup (creates `data/memories/` directory and files)
- SearXNG Docker service for local web search
  - `searxng/settings.yml.example` template
  - Configured engines: Brave, StartPage, Qwant, Google
- Langfuse tracing integration (now optional)
  - `src/core/tracing.py` returns `None` if credentials missing
  - Graceful degradation when tracing not configured
- Docker containerization for Ollama with GPU passthrough
  - `docker-compose.yml` with Nvidia GPU support
  - Persistent model storage in `.ollama-data/` volume
  - Pinned image versions for reproducibility
- Smoke tests (`tests/test_smoke.py`)
- Job search tests (`tests/test_job_search.py`) covering memory, prompts, URL handling, and tool aliases
- LLM tests (`tests/test_llm.py`) for context length detection and LLM factory
- URL deduplication in job search workflow
  - `web_search` filters out already-seen URLs before returning results
  - `fetch` tracks URLs after successful fetch
- URL blocking in `fetch` tool
  - Blocks social media URLs (Instagram, Facebook, Twitter/X, LinkedIn)
- Pre-commit hooks configuration (`.pre-commit-config.yaml`)
  - ruff for linting and formatting (auto-fix enabled)
  - mypy for type checking
- Claude Code hooks for instant feedback on file writes/edits

### Changed
- `fetch` tool rewritten to use Trafilatura instead of Playwright
  - Faster content extraction (no browser required)
  - Falls back to BeautifulSoup when Trafilatura fails
  - Shared httpx client with connection pooling and User-Agent header
- **Breaking:** Simplified LLM factory to local Ollama only
  - Removed `LLMProvider` enum (was single-value)
  - Removed provider switching - uses Ollama directly
  - Updated `get_llm()` to use ChatOpenAI with Ollama endpoint
- Primary model updated to `gpt-oss:120b` (from Qwen 2.5)
- Web search migrated from Exa API to self-hosted SearXNG
- Renamed `fetch_page` tool to `fetch` (reduces tool hallucinations with local models)

### Removed
- Simple workflow (`src/workflows/simple/`) - replaced by job search workflow
- Playwright dependency (replaced by Trafilatura for content extraction)
- PDF URL blocking in `fetch` tool (PDFs are now supported)
- `src/api/` directory (empty placeholder for future API)
- `src/services/` directory (empty placeholder)
- `config/` directory (unused)
- Unused dependencies: langchain-anthropic, langchain-ollama, fastapi, uvicorn, apscheduler, redis, docker
- `LLM_PROVIDER` environment variable (only local supported)
- Exa API integration (replaced by SearXNG)

## [0.2.0] - 2025-11-30

### Changed
- Migrated from `create_react_agent` to `create_deep_agent` as standard pattern
- Updated documentation to reflect deep agents architecture
- Tool documentation pattern: minimal tool docstrings, system prompt contains usage guidance
  - Tool docstrings now only describe what the tool does (schema focus)
  - System prompts contain when/how to use tools (workflow context)
  - Matches Deep Agents quickstart pattern for cleaner separation

### Added
- Deep agents pattern with built-in tools (write_todos, filesystem operations)
- Subagent pattern for task delegation
- Long-term memory support via CompositeBackend with path-based routing
  - `/memories/` path for persistent storage
  - `/workspace/` path for ephemeral data
- Simple workflow (`src/workflows/simple/`)
  - Deep agent with system prompt
  - `get_current_time` tool - returns current time (no dependencies)
  - `web_search` tool - ready for Exa API (requires API key)
- Interactive test script (`scripts/test_simple_agent.py`)
- Error handling pattern: tools return error strings for LLM recovery

### Validated
- Tool calling works with local Qwen 2.5:7b via Ollama
- Agent correctly selects tools based on user query
- Agent responds without tools when appropriate (e.g., greetings)

### Planned
- Job search agent with Playwright integration
- API server with FastAPI
- Scheduling system for automated runs

## [0.1.0] - 2024-11-29

### Added
- Initial project structure with Python package configuration
- Core configuration system (`src/core/config.py`)
  - Pydantic Settings for environment-based configuration
  - Support for multiple LLM providers (local/Ollama, Anthropic, OpenAI)
  - Provider enum for type-safe provider selection
- LLM factory (`src/core/llm.py`)
  - `get_llm()` function with provider swapping
  - Support for Ollama/local models (optimized for Qwen 2.5)
  - Support for Anthropic Claude models
  - Support for OpenAI GPT models
  - Cached `get_default_llm()` for single-provider use cases
  - Agent-optimized `get_agent_llm()` with sensible defaults
- Project documentation
  - README with quick start and roadmap
  - IMPLEMENTATION_PLAN for tracking development progress
  - .env.example template for configuration
- Directory structure for future components
  - `src/agents/` - For LangGraph agents (empty)
  - `src/tools/` - For agent tools (empty)
  - `src/services/` - For external service integrations (empty)
  - `src/api/` - For FastAPI server (empty)

[unreleased]: https://github.com/nat-bishop/ai-agents/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/nat-bishop/ai-agents/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nat-bishop/ai-agents/releases/tag/v0.1.0
