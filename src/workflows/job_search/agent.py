"""Job search agent using deep agents pattern.

Main agent orchestrates the search and maintains memory.
Research subagent handles web searches and returns results.
Prompts are loaded from YAML files for easier iteration.
"""

import os
from datetime import date

import yaml
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from src.core.llm import get_agent_llm
from src.workflows.job_search.tools import fetch_page, web_search

# Directories
WORKFLOW_DIR = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(WORKFLOW_DIR, "prompts")
DATA_DIR = os.path.join(WORKFLOW_DIR, "..", "..", "..", "data")


def load_prompt(name: str) -> dict:
    """Load a prompt YAML file with variable injection."""
    path = os.path.join(PROMPTS_DIR, f"{name}.yaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Inject current date into system_prompt
    if "system_prompt" in data:
        data["system_prompt"] = data["system_prompt"].replace(
            "{current_date}", date.today().isoformat()
        )
    return data


# =============================================================================
# Load prompts from YAML
# =============================================================================

_main_prompt = load_prompt("main_agent")
_research_prompt = load_prompt("research_subagent")

SYSTEM_PROMPT = _main_prompt["system_prompt"]

RESEARCH_SUBAGENT = {
    "name": _research_prompt["name"],
    "description": _research_prompt["description"],
    "system_prompt": _research_prompt["system_prompt"],
    "tools": [web_search, fetch_page],
    # Inherits default_middleware from SubAgentMiddleware (TodoListMiddleware, FilesystemMiddleware)
    # Research subagent CAN access filesystem but prompt instructs it not to write
}


# =============================================================================
# Agent Factory
# =============================================================================

def create_job_search_agent():
    """Create the job search agent with persistent local filesystem."""
    llm = get_agent_llm()
    os.makedirs(DATA_DIR, exist_ok=True)

    return create_deep_agent(
        model=llm,
        tools=[],  # Main agent delegates to research subagent
        subagents=[RESEARCH_SUBAGENT],
        system_prompt=SYSTEM_PROMPT,
        backend=lambda rt: FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
        # Note: general_purpose_agent is controlled by SubAgentMiddleware, not create_deep_agent
        # The prompt guides the agent to use the research subagent by name
    )
