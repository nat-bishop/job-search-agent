"""Tools for the job search workflow.

Provides web search using SearXNG (self-hosted metasearch) and page fetching
using Trafilatura for fast content extraction with PDF support.

Tools are async-compatible for parallel execution when the LLM
calls multiple tools in a single response.

URL deduplication is handled automatically:
- web_search filters out already-seen URLs before returning to LLM
- fetch tracks URLs after successful fetch

Tool Aliases:
- web_search: also responds to "search", "find", "lookup", "search_web"
- fetch: also responds to "fetch_page", "get_page", "scrape", "get_url"
"""

import re
import unicodedata
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import filetype  # type: ignore[import-untyped]
import httpx
import pymupdf  # type: ignore[import-untyped]
import pymupdf4llm  # type: ignore[import-untyped]
import trafilatura
from bs4 import BeautifulSoup
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger("tools")

# Path to seen URLs file (same data dir as agent's filesystem)
SEEN_URLS_PATH = Path(__file__).parent.parent.parent / "data" / "memories" / "seen_urls.txt"

# Domains that require authentication - can't scrape
BLOCKED_DOMAINS = ["instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com"]

# User-Agent header to prevent blocking
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Tool aliases for model robustness (different models may use different names)
WEB_SEARCH_ALIASES = ["search", "find", "lookup", "search_web", "web"]
FETCH_ALIASES = ["fetch_page", "get_page", "scrape", "get_url", "load_page", "fetch_url"]


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


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme (auto-prepend https:// if missing)."""
    parsed = urlparse(url)
    if not parsed.scheme:
        return "https://" + url
    return url


def _modify_reddit_url(url: str) -> str:
    """Convert reddit.com URLs to old.reddit.com for better scraping."""
    match = re.match(r"^(https?://)(www\.)?(reddit\.com)(.*)$", url, re.IGNORECASE)
    if match:
        protocol = match.group(1)
        path_and_query = match.group(4)
        return f"{protocol}old.reddit.com{path_and_query}"
    return url


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize unicode, remove emojis, collapse whitespace."""
    # Normalize unicode
    lines = [unicodedata.normalize("NFKC", line).strip() for line in text.splitlines()]
    # Remove empty lines and collapse multiple spaces
    cleaned_lines = [re.sub(r"\s{2,}", " ", line) for line in lines if line]
    # Remove emojis
    text = "\n".join(cleaned_lines)
    return "".join(c for c in text if not unicodedata.category(c).startswith("So")).strip()


def _truncate_to_words(text: str, word_limit: int = 5000) -> str:
    """Truncate text to a maximum number of words."""
    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit]) + "\n\n[Content truncated...]"


# Shared wrapper instance
_wrapper: SearxSearchWrapper | None = None


def get_wrapper() -> SearxSearchWrapper:
    """Get or create the SearxSearchWrapper instance."""
    global _wrapper
    if _wrapper is None:
        _wrapper = SearxSearchWrapper(
            searx_host=settings.searxng_host,
            k=15,  # Fetch more, filter later
            # Use only DuckDuckGo - other engines are rate-limited
            engines=["duckduckgo"],
        )
    return _wrapper


@tool
async def web_search(
    query: str,
    time_range: Literal["day", "week", "month", "year"] | None = None,
) -> str:
    """Search the web for information.

    Args:
        query: Search query string
        time_range: Filter to recent results (day, week, month, year). Use "week"
            or "month" for job searches to find recent postings.

    Returns:
        Search results with titles, URLs, and snippets
    """
    logger.info("web_search_start", query=query, time_range=time_range)
    wrapper = get_wrapper()

    # Build additional params for SearXNG API
    params: dict[str, str] = {}
    if time_range and time_range in ["day", "week", "month", "year"]:
        params["time_range"] = time_range

    try:
        # LangChain's typing for aresults doesn't include **kwargs, but implementation accepts them
        results = await wrapper.aresults(
            query,
            num_results=15,
            **params,  # type: ignore[arg-type]
        )
    except Exception as e:
        logger.warning("web_search_failed", query=query, error=str(e))
        return f"Search failed: {e}. Try a different query."

    if not results:
        logger.warning("web_search_no_results", query=query, reason="empty_response")
        return "No results found. Try different search terms."

    # Filter incomplete results (upstream SearxSearchWrapper bug - some engines return partial data)
    complete_results = [r for r in results if r.get("title") and r.get("link")]

    if not complete_results:
        logger.warning("web_search_no_results", query=query, reason="incomplete_data")
        return "No complete results found (some engines returned partial data). Try different search terms."

    # Filter out already-seen URLs BEFORE returning to LLM (shift-left deduplication)
    seen_urls = _load_seen_urls()
    new_results = [r for r in complete_results if r.get("link", "") not in seen_urls]

    if not new_results:
        logger.info("web_search_all_seen", query=query, total=len(complete_results))
        return "No NEW results found (all URLs already processed). Try different search terms."

    # Limit to 10 results after filtering
    new_results = new_results[:10]

    logger.info(
        "web_search_complete",
        query=query,
        total_results=len(results),
        new_results=len(new_results),
    )

    # Format results
    output = []
    for r in new_results:
        title = r.get("title", "No title")
        url = r.get("link", "")
        snippet = r.get("snippet", "")[:300]
        output.append(f"**{title}**\n{url}\n{snippet}")

    return "\n\n---\n\n".join(output)


# Shared httpx client for connection pooling
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared httpx AsyncClient."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=30.0,
        )
    return _http_client


@tool
async def fetch(url: str) -> str:
    """Fetch and extract text content from a webpage or PDF.

    Uses Trafilatura for fast content extraction. Supports PDFs by converting
    them to Markdown. Falls back to BeautifulSoup for pages where Trafilatura
    fails.

    Args:
        url: The URL to fetch (https:// is auto-prepended if missing)

    Returns:
        Extracted text content (truncated to ~5000 words)
    """
    # Auto-prepend https:// if missing
    url = _normalize_url(url)
    logger.info("fetch_start", url=url)

    # Skip social media (require authentication)
    if any(domain in url.lower() for domain in BLOCKED_DOMAINS):
        logger.info("fetch_blocked", url=url, reason="social_media")
        return f"Skipped social media URL (requires authentication): {url}"

    # Modify Reddit URLs for better scraping
    fetch_url = _modify_reddit_url(url)

    client = get_http_client()

    try:
        response = await client.get(fetch_url)
        response.raise_for_status()
        raw_content = response.content

        # Check if it's a PDF
        kind = filetype.guess(raw_content)
        if kind is not None and kind.mime == "application/pdf":
            # Process PDF -> Markdown
            doc = pymupdf.open(stream=raw_content, filetype="pdf")
            content = pymupdf4llm.to_markdown(doc)
            doc.close()
            content = _clean_text(content)
            content_type = "pdf"
        else:
            # HTML - use Trafilatura (fast, handles most pages well)
            html_content = response.text
            content = trafilatura.extract(
                html_content,
                favor_recall=True,  # Prefer more text when unsure
                include_comments=False,
                include_tables=True,
            )

            # Fallback to BeautifulSoup if Trafilatura fails
            if not content:
                soup = BeautifulSoup(html_content, "html.parser")
                content = soup.get_text(separator="\n", strip=True)

            content = _clean_text(content) if content else ""
            content_type = "html"

        if not content:
            logger.warning("fetch_no_content", url=url)
            return f"Page loaded but no content extracted: {url}"

        # Word-based truncation (more predictable for LLM tokens)
        word_count = len(content.split())
        content = _truncate_to_words(content, word_limit=5000)

        # Track this URL AFTER successful fetch
        _save_url(url)

        logger.info("fetch_complete", url=url, content_type=content_type, words=word_count)
        return content

    except httpx.HTTPStatusError as e:
        logger.warning("fetch_http_error", url=url, status=e.response.status_code)
        return f"HTTP error {e.response.status_code}: {url}"
    except httpx.RequestError as e:
        logger.warning("fetch_request_error", url=url, error=str(e))
        return f"Request failed for {url}: {e}"
    except Exception as e:
        logger.error("fetch_error", url=url, error=str(e))
        return f"Failed to fetch page {url}: {e}"


# --- Tool Aliases ---
# These provide alternative names for tools to handle model training variations.
# Different LLMs may be trained to call tools with different names (e.g., "search"
# vs "web_search"). Aliases prevent tool-not-found errors.


@tool
async def search(
    query: str,
    time_range: Literal["day", "week", "month", "year"] | None = None,
) -> str:
    """Search the web for information. Alias for web_search.

    Args:
        query: Search query string
        time_range: Filter to recent results (day, week, month, year)

    Returns:
        Search results with titles, URLs, and snippets
    """
    result: str = await web_search.ainvoke({"query": query, "time_range": time_range})
    return result


@tool
async def fetch_page(url: str) -> str:
    """Fetch and extract text content from a webpage. Alias for fetch.

    Args:
        url: The URL to fetch

    Returns:
        Extracted text content
    """
    result: str = await fetch.ainvoke({"url": url})
    return result
