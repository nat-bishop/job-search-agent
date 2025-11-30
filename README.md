# AI Agents

Personal AI agent system for automating tasks like job searching and research.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) using the ReAct pattern, designed to run on local models.

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

## Setup

```bash
# Clone and install
git clone https://github.com/nat-bishop/ai-agents.git
cd ai-agents
pip install -e ".[dev]"

# Pull a local model
ollama pull qwen2.5:7b  # Start small, upgrade to 72b when needed

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
LLM_PROVIDER=local              # or "anthropic", "openai"
LOCAL_MODEL=qwen2.5:7b          # Ollama model name
OLLAMA_URL=http://localhost:11434
```

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
| Qwen 2.5 7B | ~8GB | Good for dev/testing |
| Qwen 2.5 72B | ~50GB Q4 | Best tool calling |

Developed on RTX 6000 Pro (96GB VRAM).

## License

MIT
