"""Tools for the job search workflow.

Provides web search using SearXNG (self-hosted metasearch) and page fetching
using Playwright for JavaScript-rendered content.

Tools are async-compatible for parallel execution when the LLM
calls multiple tools in a single response.
"""

from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool

from src.core.config import settings

# Shared wrapper instance
_wrapper: SearxSearchWrapper | None = None


def get_wrapper() -> SearxSearchWrapper:
    """Get or create the SearxSearchWrapper instance."""
    global _wrapper
    if _wrapper is None:
        _wrapper = SearxSearchWrapper(
            searx_host=settings.searxng_host,
            k=10,
            # Use engines that work reliably (google/bing often blocked, duckduckgo times out)
            engines=["brave", "startpage", "qwant", "google"],
        )
    return _wrapper


@tool
async def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query string

    Returns:
        Search results with titles, URLs, and snippets
    """
    wrapper = get_wrapper()
    try:
        results = await wrapper.aresults(query, num_results=10)
    except Exception as e:
        return f"Search failed: {e}. Try a different query."

    if not results:
        return "No results found. Try different search terms."

    # Format results
    output = []
    for r in results:
        title = r.get("title", "No title")
        url = r.get("link", "")
        snippet = r.get("snippet", "")[:300]
        output.append(f"**{title}**\n{url}\n{snippet}")

    return "\n\n---\n\n".join(output)


# Shared transformer instance
_html2text: Html2TextTransformer | None = None


def get_html2text() -> Html2TextTransformer:
    """Get or create the Html2TextTransformer instance."""
    global _html2text
    if _html2text is None:
        _html2text = Html2TextTransformer()
    return _html2text


@tool
async def fetch_page(url: str) -> str:
    """Fetch and extract text content from a webpage.

    Uses Playwright to render JavaScript, so works with dynamic pages.

    Args:
        url: The URL to fetch

    Returns:
        Extracted text content from the page (truncated to ~10k chars)
    """
    try:
        loader = AsyncChromiumLoader([url])
        docs = await loader.aload()

        if not docs:
            return f"Failed to load page: {url}"

        # Transform HTML to readable text
        transformer = get_html2text()
        docs = transformer.transform_documents(docs)

        content = docs[0].page_content if docs else ""
        if not content:
            return f"Page loaded but no content extracted: {url}"

        # Truncate to avoid context overflow
        if len(content) > 10000:
            content = content[:10000] + "\n\n[Content truncated...]"

        return content

    except Exception as e:
        return f"Failed to fetch page: {e}"
