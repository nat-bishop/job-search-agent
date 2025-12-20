"""Job search agent using LangGraph.

Single agent with all tools (web search, fetch, persistence).
Uses create_react_agent for simple react loop.
Prompts are loaded from YAML files for easier iteration.
"""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from src.core.llm import get_agent_llm
from src.core.logging import get_logger
from src.workflows.job_search.tools import add_job, fetch, ls, read_file, web_search

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


class PromptConfig(BaseModel):
    """Schema for YAML prompt files."""

    system_prompt: str


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
SYSTEM_PROMPT = _main_prompt.system_prompt


# =============================================================================
# Memory Management
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


# =============================================================================
# Agent Factory
# =============================================================================


def create_job_search_agent() -> Any:
    """Create job search agent using LangGraph.

    Single agent with all tools:
    - web_search: Search the web via SearXNG
    - fetch: Extract content from URLs
    - add_job: Persist jobs to JSONL (handles deduplication)
    - read_file: Read files from data directory
    - ls: List directory contents

    Uses create_react_agent for a simple react loop with tool calling.
    """
    llm = get_agent_llm()
    _init_memory_files()
    generate_jobs_markdown()  # Regenerate jobs.md from JSONL source

    return create_react_agent(
        model=llm,
        tools=[web_search, fetch, add_job, read_file, ls],
        prompt=SYSTEM_PROMPT,
    )
