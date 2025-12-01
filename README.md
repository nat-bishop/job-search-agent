# AI Agents

Personal AI agent system for automating tasks like job searching and research.

Built with [LangGraph Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview), designed to run on local models.

## Status: First Agent Working

This project is in early development. Current state:
- Core infrastructure (config, LLM factory)
- Simple test agent with tool calling (validated with local Qwen 2.5)

## Quick Start

```bash
# After setup (below), run the test agent
python scripts/test_simple_agent.py

# Try these prompts:
# > What time is it?
# > Hello!
```

## Prerequisites

- Python 3.11 or 3.12 (not 3.14 - LangChain incompatible)
- Docker & Docker Compose
- Langfuse (self-hosted) - see [Setup Guide](docs/ARCHITECTURE.md#observability)

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
├── workflows/  # Agent workflows by domain
│   └── simple/ # Test agent (get_current_time, web_search tools)
├── core/       # Config and LLM factory
│   ├── config.py   # Settings from .env
│   └── llm.py      # get_llm() - supports Ollama, Anthropic, OpenAI
├── services/   # External integrations (future)
└── api/        # FastAPI server (future)
scripts/
└── test_simple_agent.py  # Interactive CLI for testing
```

## Configuration

Set in `.env`:
```bash
LLM_PROVIDER=local          # or "anthropic", "openai"
LOCAL_MODEL=gpt-oss:120b    # Ollama model name
OLLAMA_URL=http://localhost:11434
```

Python app connects to `localhost:11434` whether Ollama runs in Docker or natively.

## Roadmap

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed progress.

- [x] Phase 1: Foundation (config, LLM factory)
- [x] Phase 2: Simple test agent
- [ ] Phase 3: Job search agent
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
