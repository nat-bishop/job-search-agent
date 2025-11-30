"""Tools for the simple test workflow."""

from datetime import datetime

from langchain_core.tools import tool

from src.core.config import settings


@tool
def get_current_time() -> str:
    """Get the current date and time.

    Returns:
        Current datetime formatted as 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def web_search(query: str) -> str:
    """Search the web using Exa neural search.

    Args:
        query: Natural language search query

    Returns:
        Search results with titles, URLs, and content snippets
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
            num_results=10,
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
