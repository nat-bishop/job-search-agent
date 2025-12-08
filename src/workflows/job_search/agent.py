"""Job search agent using deep agents pattern.

Main agent orchestrates the search and maintains memory.
Research subagent handles web searches and returns results.
Prompts are loaded from YAML files for easier iteration.
"""

import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from deepagents import create_deep_agent  # type: ignore[import-untyped]
from deepagents.backends import FilesystemBackend  # type: ignore[import-untyped]
from pydantic import BaseModel

from src.core.llm import get_agent_llm
from src.workflows.job_search.tools import fetch, web_search

# Directories
WORKFLOW_DIR = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(WORKFLOW_DIR, "prompts")
DATA_DIR = os.path.join(WORKFLOW_DIR, "..", "..", "..", "data")

# Memory files (created at init so agent always finds them)
MEMORIES_DIR = Path(DATA_DIR) / "memories"
JOBS_FILE = MEMORIES_DIR / "jobs.md"
SEEN_URLS_FILE = MEMORIES_DIR / "seen_urls.txt"

JOBS_HEADER = "# Bay Area New Grad RN Opportunities\n"


class PromptConfig(BaseModel):
    """Schema for YAML prompt files.

    Main agent prompts only need system_prompt.
    Subagent prompts also need name and description.
    """

    system_prompt: str
    name: str | None = None
    description: str | None = None


def load_prompt(name: str) -> PromptConfig:
    """Load and validate a prompt YAML file with variable injection."""
    path = os.path.join(PROMPTS_DIR, f"{name}.yaml")
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    # Inject current date into system_prompt
    if "system_prompt" in data:
        data["system_prompt"] = data["system_prompt"].replace(
            "{current_date}", date.today().isoformat()
        )

    return PromptConfig.model_validate(data)


# =============================================================================
# Load prompts from YAML
# =============================================================================

_main_prompt = load_prompt("main_agent")
_research_prompt = load_prompt("research_subagent")

SYSTEM_PROMPT = _main_prompt.system_prompt

RESEARCH_SUBAGENT = {
    "name": _research_prompt.name,
    "description": _research_prompt.description,
    "system_prompt": _research_prompt.system_prompt,
    "tools": [web_search, fetch],
    # Inherits default_middleware from SubAgentMiddleware (TodoListMiddleware, FilesystemMiddleware)
    # Research subagent CAN access filesystem but prompt instructs it not to write
}


# =============================================================================
# Agent Factory
# =============================================================================


def _init_memory_files() -> None:
    """Ensure memory files exist before agent starts.

    Creates jobs.md with header and empty seen_urls.txt if they don't exist.
    This guarantees the agent always finds these files on read.
    """
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    if not JOBS_FILE.exists():
        JOBS_FILE.write_text(JOBS_HEADER)

    if not SEEN_URLS_FILE.exists():
        SEEN_URLS_FILE.touch()


def create_job_search_agent() -> Any:
    """Create the job search agent with persistent local filesystem."""
    llm = get_agent_llm()
    _init_memory_files()

    return create_deep_agent(
        model=llm,
        tools=[],  # Main agent delegates to research subagent
        subagents=[RESEARCH_SUBAGENT],
        system_prompt=SYSTEM_PROMPT,
        backend=lambda _: FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
        # SummarizationMiddleware is added by default in create_deep_agent
    )
