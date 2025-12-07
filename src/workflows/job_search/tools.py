"""Tools for the job search workflow.

Provides web search using SearXNG (self-hosted metasearch) and page fetching
using Playwright for JavaScript-rendered content.

Tools are async-compatible for parallel execution when the LLM
calls multiple tools in a single response.

URL deduplication is handled automatically:
- web_search filters out already-seen URLs before returning to LLM
- fetch tracks URLs after successful fetch
"""

from pathlib import Path

from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool

from src.core.config import settings

# Path to seen URLs file (same data dir as agent's filesystem)
SEEN_URLS_PATH = Path(__file__).parent.parent.parent / "data" / "memories" / "seen_urls.txt"

# Domains that require authentication - can't scrape
BLOCKED_DOMAINS = ["instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com"]


def _load_seen_urls() -> set[str]:
    """Load already-processed URLs from disk.

    File is created by agent.py at init, so it always exists.
    """
    if not SEEN_URLS_PATH.exists():
        return set()
    content = SEEN_URLS_PATH.read_text().strip()
    return set(content.split("\n")) if content else set()


def _save_url(url: str) -> None:
    """Append a URL to the seen list."""
    with open(SEEN_URLS_PATH, "a") as f:
        f.write(url + "\n")

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

    # Filter incomplete results (upstream SearxSearchWrapper bug - some engines return partial data)
    results = [r for r in results if r.get("title") and r.get("link")]

    if not results:
        return "No complete results found (some engines returned partial data). Try different search terms."

    # Filter out already-seen URLs BEFORE returning to LLM (shift-left deduplication)
    seen_urls = _load_seen_urls()
    results = [r for r in results if r.get("link", "") not in seen_urls]

    if not results:
        return "No NEW results found (all URLs already processed). Try different search terms."

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
async def fetch(url: str) -> str:
    """Fetch and extract text content from a webpage.

    Uses Playwright to render JavaScript, so works with dynamic pages.

    Args:
        url: The URL to fetch

    Returns:
        Extracted text content from the page (truncated to ~10k chars)
    """
    # Skip social media (require authentication)
    if any(domain in url.lower() for domain in BLOCKED_DOMAINS):
        return f"Skipped social media URL (requires authentication): {url}"

    # Skip PDFs (can't render)
    if url.lower().endswith(".pdf"):
        return f"Cannot fetch PDF files: {url}. Search for the HTML job posting page instead."

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

        # Track this URL AFTER successful fetch
        _save_url(url)

        return content

    except Exception as e:
        return f"Failed to fetch page: {e}"
