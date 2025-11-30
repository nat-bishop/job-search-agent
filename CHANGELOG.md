# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Simple test agent with basic tool calling
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

[unreleased]: https://github.com/nat-bishop/ai-agents/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nat-bishop/ai-agents/releases/tag/v0.1.0
