"""Run the nursing job search workflow.

Searches for new grad RN positions in the Bay Area using SearXNG web search.
Tracks found jobs in local files to identify new opportunities on each run.

Requirements:
- Docker services running: docker compose up -d
  (Ollama for LLM, SearXNG for web search)

Run:
    python scripts/run_job_search.py
"""

import asyncio
import sys

from src.core.config import settings
from src.core.tracing import get_langfuse_handler


def print_flush(msg: str = ""):
    """Print and flush immediately for real-time output.

    Handles Windows console encoding issues by replacing
    non-ASCII characters that can't be displayed.
    """
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        # Windows console can't handle some Unicode chars
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def print_event(event):
    """Print relevant streaming events as they happen.

    With subgraphs=True, events are tuples: (namespace, data)
    namespace is a tuple showing the subgraph path, e.g., ("task:abc123",)
    """
    # Handle subgraphs=True format: (namespace_tuple, event_dict)
    if isinstance(event, tuple) and len(event) == 2:
        namespace, event_data = event
        prefix = " > ".join(namespace) if namespace else "Main"
    else:
        prefix = "Main"
        event_data = event

    if not isinstance(event_data, dict):
        return

    for key, value in event_data.items():
        # Skip internal keys
        if key.startswith("__"):
            continue

        # Determine the label based on event type
        if key == "agent":
            label = f"[{prefix}] Agent"
        elif key == "tools":
            label = f"[{prefix}] Tool"
        else:
            # Subagent or other node (e.g., "research")
            label = f"[{prefix}] {key.capitalize()}"

        # Process messages in the event
        if not isinstance(value, dict):
            continue
        messages = value.get("messages", [])
        if not isinstance(messages, list):
            continue
        for msg in messages:
            # Show tool calls (agent deciding to call something)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    print_flush(f"{label} calling: {tool_name}")

            # Show tool results
            if hasattr(msg, "name") and hasattr(msg, "content"):
                content = str(msg.content)[:150] if msg.content else ""
                print_flush(f"{label} {msg.name}: {content}...")

            # Show agent/subagent text responses (not tool calls)
            elif hasattr(msg, "content") and msg.content:
                if isinstance(msg.content, str) and msg.content.strip():
                    # Only show if it's not a tool-call-only message
                    if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                        print_flush(f"{label}: {msg.content[:200]}...")


async def main():
    print_flush("\n" + "=" * 60)
    print_flush("NURSING JOB SEARCH - Bay Area New Grad RN")
    print_flush("=" * 60)

    print_flush(f"\nModel: {settings.local_model}")
    print_flush(f"Search: SearXNG @ {settings.searxng_host}")

    # Create agent
    try:
        from src.workflows.job_search.agent import create_job_search_agent

        agent = create_job_search_agent()
        langfuse_handler = get_langfuse_handler()
        print_flush("Agent initialized successfully")
    except Exception as e:
        print_flush(f"\n[ERROR] Failed to initialize agent: {e}")
        print_flush("\nMake sure services are running: docker compose up -d")
        return

    # The job search task - keep simple, system prompt has the details
    task = "Search for new nursing job opportunities and update your files."

    print_flush("\n" + "-" * 60)
    print_flush("Starting job search (streaming output enabled)...")
    print_flush("-" * 60)

    try:
        # Stream events for real-time progress
        final_content = None
        async for event in agent.astream(
            {"messages": [{"role": "user", "content": task}]},
            config={"callbacks": [langfuse_handler]},
            subgraphs=True,  # Stream subagent events too
        ):
            print_event(event)

            # Capture final message
            if "agent" in event:
                messages = event["agent"].get("messages", [])
                for msg in messages:
                    if hasattr(msg, "content") and isinstance(msg.content, str):
                        final_content = msg.content

        print_flush("\n" + "=" * 60)
        print_flush("JOB SEARCH RESULTS")
        print_flush("=" * 60)

        if final_content:
            # Handle unicode safely for Windows console
            try:
                print_flush(final_content)
            except UnicodeEncodeError:
                print_flush(final_content.encode("ascii", "replace").decode("ascii"))

        print_flush("\n" + "=" * 60)
        print_flush("Search complete. View traces at http://localhost:3000")
        print_flush("=" * 60)

    except KeyboardInterrupt:
        print_flush("\n\nSearch interrupted by user")
    except Exception as e:
        print_flush(f"\n[ERROR] Search failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
