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

from src.core.config import settings
from src.core.logging import bind_trace_id, clear_trace_context, get_logger, setup_logging
from src.core.tracing import get_langfuse_handler

# Initialize logging before anything else
setup_logging(json_logs=settings.log_json, log_file=settings.log_file)
logger = get_logger("job_search")


def print_flush(msg: str = "") -> None:
    """Print and flush immediately for real-time output.

    Handles Windows console encoding issues by replacing
    non-ASCII characters that can't be displayed.
    """
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        # Windows console can't handle some Unicode chars
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def print_event(event: dict[str, object]) -> None:
    """Print relevant streaming events as they happen.

    LangGraph create_react_agent emits:
    - {"agent": {"messages": [AIMessage(...)]}} for agent responses
    - {"tools": {"messages": [ToolMessage(...)]}} for tool results
    """
    if not isinstance(event, dict):
        return

    for key, value in event.items():
        # Skip internal keys
        if key.startswith("__"):
            continue

        label = f"[{key.capitalize()}]"

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
                    tool_name = (
                        tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    )
                    print_flush(f"{label} calling: {tool_name}")

            # Show tool results
            if hasattr(msg, "name") and hasattr(msg, "content"):
                content = str(msg.content)[:150] if msg.content else ""
                print_flush(f"{label} {msg.name}: {content}...")

            # Show agent text responses (not tool calls)
            elif hasattr(msg, "content") and msg.content:
                if isinstance(msg.content, str) and msg.content.strip():
                    # Only show if it's not a tool-call-only message
                    if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                        print_flush(f"{label}: {msg.content[:200]}...")


async def main() -> None:
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
        if langfuse_handler:
            print_flush("Langfuse tracing enabled")
    except Exception as e:
        logger.error("agent_init_failed", error=str(e))
        print_flush(f"\n[ERROR] Failed to initialize agent: {e}")
        print_flush("\nMake sure services are running: docker compose up -d")
        return

    # The job search task - keep simple, system prompt has the details
    task = "Search for new nursing job opportunities and update your files."

    print_flush("\n" + "-" * 60)
    print_flush("Starting job search (streaming output enabled)...")
    print_flush("-" * 60)

    # Get Langfuse client for trace ID binding (if available)
    langfuse = None
    if langfuse_handler:
        try:
            from langfuse import get_client

            langfuse = get_client()
        except Exception:
            pass  # Continue without trace_id binding

    try:
        # Stream events for real-time progress
        final_content = None
        config: dict[str, object] = {"recursion_limit": 100}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        # Wrap in Langfuse span to get trace_id for log correlation
        if langfuse:
            with langfuse.start_as_current_observation(as_type="span", name="job-search-run"):
                trace_id = langfuse.get_current_trace_id()
                if trace_id:
                    bind_trace_id(trace_id)
                logger.info("job_search_start", model=settings.local_model)
                print_flush(f"Trace ID: {trace_id}")

                async for event in agent.astream(
                    {"messages": [{"role": "user", "content": task}]},
                    config=config,
                ):
                    print_event(event)
                    # Capture final agent response
                    if "agent" in event:
                        messages = event["agent"].get("messages", [])
                        for msg in messages:
                            if hasattr(msg, "content") and isinstance(msg.content, str):
                                if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                    final_content = msg.content

                logger.info("job_search_complete")
                clear_trace_context()
        else:
            # No Langfuse - run without trace correlation
            logger.info("job_search_start", model=settings.local_model)
            async for event in agent.astream(
                {"messages": [{"role": "user", "content": task}]},
                config=config,
            ):
                print_event(event)
                # Capture final agent response
                if "agent" in event:
                    messages = event["agent"].get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "content") and isinstance(msg.content, str):
                            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                final_content = msg.content
            logger.info("job_search_complete")

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
        if langfuse_handler:
            print_flush("Search complete. View traces at http://localhost:3000")
        else:
            print_flush("Search complete.")
        print_flush("=" * 60)

    except KeyboardInterrupt:
        logger.info("job_search_interrupted")
        print_flush("\n\nSearch interrupted by user")
    except Exception as e:
        logger.error("job_search_failed", error=str(e))
        print_flush(f"\n[ERROR] Search failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
