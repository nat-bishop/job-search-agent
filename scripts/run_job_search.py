"""Run the nursing job search workflow.

Searches for new grad RN positions in the Bay Area using Exa web search.
Tracks found jobs in local files to identify new opportunities on each run.

Requirements:
- Ollama running with model: docker compose up -d
- EXA_API_KEY configured in .env

Run:
    python scripts/run_job_search.py
"""

import sys

from src.core.config import settings
from src.core.tracing import get_langfuse_handler


def print_flush(msg: str = ""):
    """Print and flush immediately for real-time output."""
    print(msg, flush=True)


def print_event(event: dict):
    """Print relevant streaming events as they happen."""
    # Agent messages
    if "agent" in event:
        messages = event["agent"].get("messages", [])
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                # Skip if it's just tool calls with no text
                if isinstance(msg.content, str) and msg.content.strip():
                    print_flush(f"\n[Agent] {msg.content[:200]}...")

            # Show tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    # Handle both dict and object formats
                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    print_flush(f"\n[Calling] {tool_name}")

    # Tool results
    if "tools" in event:
        messages = event["tools"].get("messages", [])
        for msg in messages:
            if hasattr(msg, "name"):
                # Show brief tool result
                content = str(msg.content)[:100] if hasattr(msg, "content") else ""
                print_flush(f"[Result] {msg.name}: {content}...")


def main():
    print_flush("\n" + "=" * 60)
    print_flush("NURSING JOB SEARCH - Bay Area New Grad RN")
    print_flush("=" * 60)

    # Check required config
    if not settings.exa_api_key:
        print_flush("\n[ERROR] EXA_API_KEY not configured")
        print_flush("  Add EXA_API_KEY to your .env file")
        return

    print_flush(f"\nModel: {settings.local_model}")

    # Create agent
    try:
        from src.workflows.job_search.agent import create_job_search_agent

        agent = create_job_search_agent()
        langfuse_handler = get_langfuse_handler()
        print_flush("Agent initialized successfully")
    except Exception as e:
        print_flush(f"\n[ERROR] Failed to initialize agent: {e}")
        print_flush("\nMake sure Ollama is running: docker compose up -d")
        return

    # The job search task
    task = """Search for new grad RN job opportunities in the Bay Area.

Please follow this workflow:

1. First, check your memory for previously seen jobs by reading /memories/jobs/seen.md
   (If file doesn't exist, this is your first run - no prior jobs to compare)

2. Search for current openings at major Bay Area hospitals:
   - UCSF Health
   - Stanford Health Care
   - Kaiser Permanente
   - Sutter Health
   - John Muir Health
   - Other Bay Area hospitals

3. Identify any NEW jobs - ones not already in your seen.md file

4. Update your tracking files:
   - Add new job URLs to /memories/jobs/seen.md
   - Add promising jobs to /memories/jobs/interesting.md with details
   - Log this search in /memories/search_log.md

5. Report your findings:
   - How many new jobs found
   - Most promising opportunities with details
   - Any upcoming application deadlines

Focus on new grad RN programs and nursing residencies.
"""

    print_flush("\n" + "-" * 60)
    print_flush("Starting job search (streaming output enabled)...")
    print_flush("-" * 60)

    try:
        # Stream events for real-time progress
        final_content = None
        for event in agent.stream(
            {"messages": [{"role": "user", "content": task}]},
            config={"callbacks": [langfuse_handler]},
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
    main()
