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
from src.core.logging import get_logger
from src.workflows.job_search.tools import fetch, web_search

logger = get_logger(__name__)

# Directories
WORKFLOW_DIR = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(WORKFLOW_DIR, "prompts")
DATA_DIR = os.path.join(WORKFLOW_DIR, "..", "..", "..", "data")

# Memory files (created at init so agent always finds them)
MEMORIES_DIR = Path(DATA_DIR) / "memories"
JOBS_FILE = MEMORIES_DIR / "jobs.md"
JOBS_JSONL_FILE = MEMORIES_DIR / "jobs.jsonl"
SEEN_URLS_FILE = MEMORIES_DIR / "seen_urls.txt"

JOBS_HEADER = "# Bay Area New Grad RN Opportunities\n"


class RestrictedFilesystemBackend(FilesystemBackend):  # type: ignore[misc]
    """FilesystemBackend that blocks edit operations on jobs.md.

    The main agent should use add_job() tool instead of editing jobs.md directly.
    This prevents the LLM from accidentally wiping the jobs file.
    """

    def edit(self, path: str, *args: Any, **kwargs: Any) -> str:
        """Block edit operations on jobs.md to prevent accidental data wipes."""
        if "jobs.md" in path:
            return "Error: Cannot edit jobs.md directly. Use add_job() tool instead."
        return super().edit(path, *args, **kwargs)  # type: ignore[no-any-return]


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

    Creates empty seen_urls.txt and jobs.jsonl if they don't exist.
    This guarantees the agent always finds these files on read.
    """
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    if not SEEN_URLS_FILE.exists():
        SEEN_URLS_FILE.touch()

    if not JOBS_JSONL_FILE.exists():
        JOBS_JSONL_FILE.touch()


def generate_jobs_markdown() -> None:
    """Generate jobs.md from jobs.jsonl, filtering expired entries.

    This creates a human-readable markdown view of active job opportunities.
    Expired jobs (deadline < today) are filtered out but kept in the JSONL source.
    Called at agent startup to ensure jobs.md reflects current state.
    """
    import json

    if not JOBS_JSONL_FILE.exists() or JOBS_JSONL_FILE.stat().st_size == 0:
        JOBS_FILE.write_text("# Bay Area New Grad RN Opportunities\n\nNo jobs found yet.\n")
        logger.info("jobs_markdown_generated", total=0, active=0)
        return

    # Load and parse jobs, skipping corrupted lines
    jobs: list[dict[str, Any]] = []
    for line in JOBS_JSONL_FILE.read_text().strip().split("\n"):
        if line:
            try:
                jobs.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("jobs_jsonl_corrupted_line", line=line[:50])
                continue

    # Filter expired (keep if deadline is "Rolling", "Unknown", or >= today)
    today = date.today().isoformat()
    active_jobs = [
        j
        for j in jobs
        if j.get("deadline", "").lower() in ["rolling", "unknown"] or j.get("deadline", "") >= today
    ]

    # Sort by deadline (Rolling/Unknown at end)
    def sort_key(j: dict[str, Any]) -> tuple[bool, str]:
        deadline = j.get("deadline", "")
        is_special = deadline.lower() in ["rolling", "unknown"]
        return (is_special, deadline)

    active_jobs.sort(key=sort_key)

    # Generate markdown
    md = "# Bay Area New Grad RN Opportunities\n\n"
    md += f"*Last updated: {date.today().isoformat()}*\n\n"

    if not active_jobs:
        md += "No active job opportunities found.\n"
    else:
        for job in active_jobs:
            md += f"## {job.get('organization', 'Unknown')} - {job.get('program', 'Unknown')}\n"
            md += f"- **Deadline**: {job.get('deadline', 'Unknown')}\n"
            md += f"- **Source**: {job.get('url', 'N/A')}\n"
            md += f"- {job.get('details', 'No details available')}\n\n"

    JOBS_FILE.write_text(md)
    logger.info("jobs_markdown_generated", total=len(jobs), active=len(active_jobs))


def create_job_search_agent() -> Any:
    """Create the job search agent with persistent local filesystem.

    Uses RestrictedFilesystemBackend (no edit_file) to prevent accidental data wipes.
    The main agent has add_job tool to persist job findings with deduplication.
    """
    from src.workflows.job_search.tools import add_job

    llm = get_agent_llm()
    _init_memory_files()
    generate_jobs_markdown()  # Regenerate jobs.md from JSONL source

    return create_deep_agent(
        model=llm,
        tools=[add_job],  # Main agent can add jobs directly
        subagents=[RESEARCH_SUBAGENT],
        system_prompt=SYSTEM_PROMPT,
        backend=lambda _: RestrictedFilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
        # SummarizationMiddleware is added by default in create_deep_agent
    )
