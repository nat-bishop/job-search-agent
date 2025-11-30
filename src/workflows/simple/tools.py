"""Tools for the simple test workflow."""

from datetime import datetime

from langchain_core.tools import tool

from src.core.config import settings


@tool
def get_current_time() -> str:
    """Get the current date and time.

    Use this tool when the user asks about:
    - The current time
    - Today's date
    - What day it is

    Returns:
        Current datetime formatted as 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def web_search(query: str) -> str:
    """Search the web for information using Exa.

    Use this tool when the user asks about:
    - Current events or news
    - Information you don't know
    - Facts that may have changed since your training

    Args:
        query: The search query (natural language works best)

    Returns:
        Search results with titles, URLs, and snippets
    """
    # User-fixable: missing config
    if not settings.exa_api_key:
        return "Error: EXA_API_KEY not configured. Add it to your .env file."

    from exa_py import Exa

    # LLM-recoverable: wrap API call so LLM can see errors and adjust
    try:
        exa = Exa(api_key=settings.exa_api_key)
        results = exa.search_and_contents(
            query,
            num_results=3,
            text={"max_characters": 500},
        )
    except Exception as e:
        return f"Search failed: {e}. Try a different query."

    # Handle empty results
    if not results.results:
        return "No results found. Try different search terms."

    # Format results for the LLM (plain text, not markdown)
    output = []
    for r in results.results:
        snippet = r.text[:300] if r.text else "No content available"
        output.append(f"{r.title}\n{r.url}\n{snippet}...")

    return "\n\n".join(output)
