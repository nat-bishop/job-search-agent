# AI Agents

Personal AI agent system for automating tasks like job searching and research.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) using the ReAct pattern, designed to run on local models.

## Status: Foundation

This project is in early development. Current state:
- Core infrastructure (config, LLM factory)
- No agents yet - that's next

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
├── agents/     # LangGraph agents (coming soon)
├── tools/      # Tool functions for agents
├── core/       # Config and LLM factory
│   ├── config.py   # Settings from .env
│   └── llm.py      # get_llm() - supports Ollama, Anthropic, OpenAI
└── api/        # FastAPI server (future)
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
- [ ] Phase 2: Simple test agent
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
