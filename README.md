# AI Agents

Personal AI agent system for automating tasks like job searching and research.

Built with [LangGraph Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview), designed to run on local models.

## Status: Job Search Agent

Current workflow: **Nursing job search** - finds new grad RN positions in the Bay Area.

Features:
- Deep agent with research subagent (SearXNG web search)
- Persistent memory across runs (local files)
- Tracks seen jobs to report only NEW findings

## Quick Start

```bash
# After setup (below), start Docker services
docker compose up -d

# Run the job search
python scripts/run_job_search.py
```

## Prerequisites

- Python 3.11 or 3.12 (not 3.14 - LangChain incompatible)
- Docker & Docker Compose
- NVIDIA GPU with ~60GB VRAM (for gpt-oss:120b model)
- Optional: Langfuse for tracing - see [Setup Guide](docs/ARCHITECTURE.md#observability)

## Setup

### Option 1: Docker (Recommended)

Using Docker prevents GPU resource conflicts and prepares for Phase 4 scheduling:

```bash
# Clone
git clone https://github.com/nat-bishop/ai-agents.git
cd ai-agents

# Start Ollama container with GPU
docker compose up -d

# Pull the model (65GB download + processing)
docker compose exec ollama ollama pull gpt-oss:120b

# Create and activate venv (Python app runs on host)
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell
# .venv\Scripts\activate.bat  # CMD
# source .venv/bin/activate   # Git Bash / Linux

# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env
```

**Note**: Models persist in `.ollama-data/` and survive container restarts. Expect 1-5% performance overhead vs native.

### Option 2: Native Ollama

If you prefer running Ollama directly on your host:

```bash
# Clone
git clone https://github.com/nat-bishop/ai-agents.git
cd ai-agents

# Create and activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell

# Install dependencies
pip install -e ".[dev]"

# Pull a local model
ollama pull gpt-oss:120b  # 65GB, needs ~60GB VRAM

# Configure
cp .env.example .env
```

## Project Structure

```
src/
├── workflows/      # Agent workflows by domain
│   └── job_search/ # Nursing job search (main workflow)
│       ├── agent.py    # Deep agent + research subagent
│       ├── tools.py    # web_search (SearXNG), fetch
│       └── prompts/    # YAML prompt files
├── core/           # Config and LLM factory
│   ├── config.py   # Settings from .env
│   ├── llm.py      # get_llm() - local Ollama models
│   └── tracing.py  # Langfuse integration (optional)
scripts/
└── run_job_search.py  # Entry point for job search workflow
```

## Configuration

Set in `.env`:
```bash
LOCAL_MODEL=gpt-oss:120b    # Ollama model name
OLLAMA_URL=http://localhost:11434
SEARXNG_HOST=http://localhost:8080

# Optional: Langfuse tracing
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_HOST=http://localhost:3000
```

Python app connects to `localhost:11434` (Ollama) and `localhost:8080` (SearXNG).

## Roadmap

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed progress.

- [x] Phase 1: Foundation (config, LLM factory)
- [x] Phase 2: Deep agent pattern
- [x] Phase 3: Job search workflow (with persistent memory)
- [ ] Phase 4: API & scheduling
- [ ] Phase 5: Multi-agent orchestration

## Hardware

| Model | VRAM | Notes |
|-------|------|-------|
| gpt-oss:120b | ~60GB | Primary model - MoE architecture (5.1B active) |
| Qwen 2.5 7B | ~8GB | Fallback for testing |
| Qwen 2.5 72B Q8 | ~75GB | Alternative for quality |

Developed on RTX PRO 6000 Blackwell (96GB VRAM).

**Why gpt-oss:120b?**
- Newer model (Aug 2025 vs Qwen's Mar 2024)
- Optimized for agentic workflows with better reasoning
- More efficient: 5.1B active parameters (MoE) vs 22B all-active

## License

MIT
