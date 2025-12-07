"""Tests for the job search workflow.

Tests cover:
- Memory file initialization (agent.py)
- Prompt loading with date injection (agent.py)
- URL tracking helpers (tools.py)
- URL blocking for social media (tools.py)
- URL normalization and text cleaning (tools.py)
- Tool aliases (tools.py)
"""

from datetime import date
from unittest.mock import patch

import pytest

# =============================================================================
# agent.py - Memory File Initialization
# =============================================================================


class TestInitMemoryFiles:
    """Tests for _init_memory_files() function."""

    def test_creates_directory_and_files(self, tmp_path):
        """Creates memories directory and both files when nothing exists."""
        from src.workflows.job_search import agent

        # Patch the paths to use temp directory
        memories_dir = tmp_path / "memories"
        jobs_file = memories_dir / "jobs.md"
        seen_urls_file = memories_dir / "seen_urls.txt"

        with (
            patch.object(agent, "MEMORIES_DIR", memories_dir),
            patch.object(agent, "JOBS_FILE", jobs_file),
            patch.object(agent, "SEEN_URLS_FILE", seen_urls_file),
        ):
            agent._init_memory_files()

            assert memories_dir.exists()
            assert jobs_file.exists()
            assert seen_urls_file.exists()

    def test_jobs_file_has_correct_header(self, tmp_path):
        """jobs.md is created with the expected header."""
        from src.workflows.job_search import agent

        memories_dir = tmp_path / "memories"
        jobs_file = memories_dir / "jobs.md"
        seen_urls_file = memories_dir / "seen_urls.txt"

        with (
            patch.object(agent, "MEMORIES_DIR", memories_dir),
            patch.object(agent, "JOBS_FILE", jobs_file),
            patch.object(agent, "SEEN_URLS_FILE", seen_urls_file),
        ):
            agent._init_memory_files()

            content = jobs_file.read_text()
            assert content == agent.JOBS_HEADER
            assert "Bay Area New Grad RN" in content

    def test_seen_urls_file_is_empty(self, tmp_path):
        """seen_urls.txt is created empty."""
        from src.workflows.job_search import agent

        memories_dir = tmp_path / "memories"
        jobs_file = memories_dir / "jobs.md"
        seen_urls_file = memories_dir / "seen_urls.txt"

        with (
            patch.object(agent, "MEMORIES_DIR", memories_dir),
            patch.object(agent, "JOBS_FILE", jobs_file),
            patch.object(agent, "SEEN_URLS_FILE", seen_urls_file),
        ):
            agent._init_memory_files()

            content = seen_urls_file.read_text()
            assert content == ""

    def test_does_not_overwrite_existing_jobs(self, tmp_path):
        """Preserves existing jobs.md content - critical for user data."""
        from src.workflows.job_search import agent

        memories_dir = tmp_path / "memories"
        memories_dir.mkdir()
        jobs_file = memories_dir / "jobs.md"
        seen_urls_file = memories_dir / "seen_urls.txt"

        # Pre-populate with user data
        existing_content = "# Jobs\n\n## Stanford - RN Position\n- Important job!\n"
        jobs_file.write_text(existing_content)

        with (
            patch.object(agent, "MEMORIES_DIR", memories_dir),
            patch.object(agent, "JOBS_FILE", jobs_file),
            patch.object(agent, "SEEN_URLS_FILE", seen_urls_file),
        ):
            agent._init_memory_files()

            # Content should be preserved, not overwritten
            assert jobs_file.read_text() == existing_content

    def test_does_not_overwrite_existing_seen_urls(self, tmp_path):
        """Preserves existing seen_urls.txt content."""
        from src.workflows.job_search import agent

        memories_dir = tmp_path / "memories"
        memories_dir.mkdir()
        jobs_file = memories_dir / "jobs.md"
        seen_urls_file = memories_dir / "seen_urls.txt"

        # Pre-populate with URLs
        existing_urls = "https://example.com/job1\nhttps://example.com/job2\n"
        seen_urls_file.write_text(existing_urls)

        with (
            patch.object(agent, "MEMORIES_DIR", memories_dir),
            patch.object(agent, "JOBS_FILE", jobs_file),
            patch.object(agent, "SEEN_URLS_FILE", seen_urls_file),
        ):
            agent._init_memory_files()

            # URLs should be preserved
            assert seen_urls_file.read_text() == existing_urls


# =============================================================================
# agent.py - Prompt Loading
# =============================================================================


class TestLoadPrompt:
    """Tests for load_prompt() function."""

    def test_injects_current_date(self, tmp_path):
        """Replaces {current_date} placeholder with today's date."""
        from src.workflows.job_search import agent

        # Create a test prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        test_prompt = prompts_dir / "test_prompt.yaml"
        test_prompt.write_text(
            "system_prompt: |\n" "  Today is {current_date}.\n" "  Do the thing.\n"
        )

        with patch.object(agent, "PROMPTS_DIR", str(prompts_dir)):
            result = agent.load_prompt("test_prompt")

            today = date.today().isoformat()
            assert today in result["system_prompt"]
            assert "{current_date}" not in result["system_prompt"]

    def test_returns_dict_with_system_prompt(self, tmp_path):
        """Returns dictionary containing the system_prompt key."""
        from src.workflows.job_search import agent

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        test_prompt = prompts_dir / "test_prompt.yaml"
        test_prompt.write_text(
            "name: test\n"
            "description: A test prompt\n"
            "system_prompt: |\n"
            "  You are a test assistant.\n"
        )

        with patch.object(agent, "PROMPTS_DIR", str(prompts_dir)):
            result = agent.load_prompt("test_prompt")

            assert "system_prompt" in result
            assert "name" in result
            assert result["name"] == "test"


# =============================================================================
# tools.py - URL Tracking Helpers
# =============================================================================


class TestLoadSeenUrls:
    """Tests for _load_seen_urls() helper."""

    def test_returns_empty_set_for_missing_file(self, tmp_path):
        """Returns empty set when file doesn't exist."""
        from src.workflows.job_search import tools

        missing_file = tmp_path / "nonexistent.txt"

        with patch.object(tools, "SEEN_URLS_PATH", missing_file):
            result = tools._load_seen_urls()
            assert result == set()

    def test_returns_empty_set_for_empty_file(self, tmp_path):
        """Returns empty set for empty file."""
        from src.workflows.job_search import tools

        empty_file = tmp_path / "empty.txt"
        empty_file.touch()

        with patch.object(tools, "SEEN_URLS_PATH", empty_file):
            result = tools._load_seen_urls()
            assert result == set()

    def test_parses_urls_correctly(self, tmp_path):
        """Correctly parses URLs, one per line."""
        from src.workflows.job_search import tools

        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "https://example.com/job1\n" "https://example.com/job2\n" "https://example.com/job3\n"
        )

        with patch.object(tools, "SEEN_URLS_PATH", urls_file):
            result = tools._load_seen_urls()
            assert result == {
                "https://example.com/job1",
                "https://example.com/job2",
                "https://example.com/job3",
            }

    def test_handles_trailing_newlines(self, tmp_path):
        """Handles files with trailing newlines (no empty string in set)."""
        from src.workflows.job_search import tools

        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://example.com/job1\n\n\n")

        with patch.object(tools, "SEEN_URLS_PATH", urls_file):
            result = tools._load_seen_urls()
            # Should not include empty strings from trailing newlines
            assert "" not in result
            assert result == {"https://example.com/job1"}


class TestSaveUrl:
    """Tests for _save_url() helper."""

    def test_appends_url_with_newline(self, tmp_path):
        """Appends URL to file with trailing newline."""
        from src.workflows.job_search import tools

        urls_file = tmp_path / "urls.txt"
        urls_file.touch()

        with patch.object(tools, "SEEN_URLS_PATH", urls_file):
            tools._save_url("https://example.com/job1")
            tools._save_url("https://example.com/job2")

            content = urls_file.read_text()
            assert content == "https://example.com/job1\nhttps://example.com/job2\n"


# =============================================================================
# tools.py - URL Blocking
# =============================================================================


class TestFetchBlocking:
    """Tests for URL blocking in fetch() tool."""

    @pytest.mark.asyncio
    async def test_blocks_linkedin_urls(self):
        """Blocks LinkedIn URLs with appropriate message."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://www.linkedin.com/jobs/view/12345"})
        assert "Skipped social media" in result
        assert "authentication" in result

    @pytest.mark.asyncio
    async def test_blocks_instagram_urls(self):
        """Blocks Instagram URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://www.instagram.com/ucsfhealthcareers"})
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_facebook_urls(self):
        """Blocks Facebook URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://www.facebook.com/StanfordHealth"})
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_twitter_urls(self):
        """Blocks Twitter URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://twitter.com/ucsfhealth"})
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_x_urls(self):
        """Blocks X (formerly Twitter) URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://x.com/ucsfhealth"})
        assert "Skipped social media" in result


# =============================================================================
# tools.py - URL Normalization and Text Cleaning
# =============================================================================


class TestUrlNormalization:
    """Tests for _normalize_url() helper."""

    def test_prepends_https_to_bare_domain(self):
        """Auto-prepends https:// to URLs without scheme."""
        from src.workflows.job_search.tools import _normalize_url

        assert _normalize_url("example.com") == "https://example.com"
        assert _normalize_url("indeed.com/jobs/123") == "https://indeed.com/jobs/123"

    def test_preserves_existing_scheme(self):
        """Keeps existing http:// or https:// scheme."""
        from src.workflows.job_search.tools import _normalize_url

        assert _normalize_url("https://example.com") == "https://example.com"
        assert _normalize_url("http://example.com") == "http://example.com"


class TestRedditUrlModification:
    """Tests for _modify_reddit_url() helper."""

    def test_converts_reddit_to_old_reddit(self):
        """Converts reddit.com URLs to old.reddit.com."""
        from src.workflows.job_search.tools import _modify_reddit_url

        assert (
            _modify_reddit_url("https://reddit.com/r/nursing") == "https://old.reddit.com/r/nursing"
        )
        assert (
            _modify_reddit_url("https://www.reddit.com/r/nursing")
            == "https://old.reddit.com/r/nursing"
        )

    def test_leaves_non_reddit_urls_unchanged(self):
        """Non-Reddit URLs are unchanged."""
        from src.workflows.job_search.tools import _modify_reddit_url

        assert _modify_reddit_url("https://example.com") == "https://example.com"


class TestTextCleaning:
    """Tests for _clean_text() helper."""

    def test_removes_emojis(self):
        """Removes emoji characters from text."""
        from src.workflows.job_search.tools import _clean_text

        result = _clean_text("Hello 👋 World 🌍")
        assert "👋" not in result
        assert "🌍" not in result
        assert "Hello" in result
        assert "World" in result

    def test_collapses_whitespace(self):
        """Collapses multiple spaces into one."""
        from src.workflows.job_search.tools import _clean_text

        result = _clean_text("Hello    World")
        assert "    " not in result
        assert "Hello World" in result


class TestWordTruncation:
    """Tests for _truncate_to_words() helper."""

    def test_truncates_long_text(self):
        """Truncates text exceeding word limit."""
        from src.workflows.job_search.tools import _truncate_to_words

        text = " ".join(["word"] * 100)
        result = _truncate_to_words(text, word_limit=50)
        assert result.count("word") == 50
        assert "[Content truncated...]" in result

    def test_preserves_short_text(self):
        """Preserves text under word limit."""
        from src.workflows.job_search.tools import _truncate_to_words

        text = " ".join(["word"] * 10)
        result = _truncate_to_words(text, word_limit=50)
        assert result == text
        assert "[Content truncated...]" not in result


# =============================================================================
# tools.py - Tool Aliases
# =============================================================================


class TestToolAliases:
    """Tests for tool alias functionality."""

    def test_search_alias_exists(self):
        """search alias tool exists and is callable."""
        from langchain_core.tools import StructuredTool

        from src.workflows.job_search.tools import search

        assert isinstance(search, StructuredTool)

    def test_fetch_page_alias_exists(self):
        """fetch_page alias tool exists and is callable."""
        from langchain_core.tools import StructuredTool

        from src.workflows.job_search.tools import fetch_page

        assert isinstance(fetch_page, StructuredTool)


# =============================================================================
# tools.py - Incomplete Results Filtering
# =============================================================================


class TestIncompleteResultsFiltering:
    """Tests for filtering incomplete search results."""

    @pytest.mark.asyncio
    async def test_filters_results_missing_title(self, tmp_path):
        """Results without title are filtered out."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        # Mock search results with one incomplete (no title)
        mock_results = [
            {"title": "Good Result", "link": "https://example.com/good", "snippet": "Has title"},
            {"link": "https://example.com/bad", "snippet": "Missing title"},  # No title
        ]

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(return_value=mock_results)

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
        ):
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            # Should only include the good result
            assert "Good Result" in result
            assert "https://example.com/good" in result
            # Should NOT include the bad result
            assert "https://example.com/bad" not in result

    @pytest.mark.asyncio
    async def test_filters_results_missing_link(self, tmp_path):
        """Results without link are filtered out."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        # Mock search results with one incomplete (no link)
        mock_results = [
            {"title": "Good Result", "link": "https://example.com/good", "snippet": "Has link"},
            {"title": "Bad Result", "snippet": "Missing link"},  # No link
        ]

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(return_value=mock_results)

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
        ):
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            # Should only include the good result
            assert "Good Result" in result
            # Should NOT include the bad result (even though it has a title)
            assert "Bad Result" not in result

    @pytest.mark.asyncio
    async def test_returns_message_when_all_results_incomplete(self, tmp_path):
        """Returns helpful message when all results are incomplete."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        # All results missing required fields
        mock_results = [
            {"snippet": "No title or link"},
            {"title": "Only title"},
        ]

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(return_value=mock_results)

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
        ):
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            assert "No complete results found" in result
            assert "partial data" in result


# =============================================================================
# agent.py - SummarizationMiddleware Configuration
# =============================================================================


class TestSummarizationMiddleware:
    """Tests for SummarizationMiddleware configuration in agent."""

    def test_middleware_import_works(self):
        """Verify SummarizationMiddleware can be imported."""
        from langchain.agents.middleware import SummarizationMiddleware

        assert SummarizationMiddleware is not None

    # Note: Tests for explicit middleware configuration removed.
    # Deep agents adds SummarizationMiddleware by default, so we rely on that.


# =============================================================================
# Smoke Tests (verify imports work)
# =============================================================================


def test_job_search_agent_imports():
    """Verify job search workflow can be imported."""
    from langchain_core.tools import StructuredTool

    from src.workflows.job_search.agent import create_job_search_agent
    from src.workflows.job_search.tools import fetch, fetch_page, search, web_search

    assert callable(create_job_search_agent)
    # @tool decorator wraps functions as StructuredTool instances
    assert isinstance(web_search, StructuredTool)
    assert isinstance(fetch, StructuredTool)
    # Aliases should also be StructuredTool instances
    assert isinstance(search, StructuredTool)
    assert isinstance(fetch_page, StructuredTool)


def test_blocked_domains_list():
    """Verify BLOCKED_DOMAINS contains expected social media sites."""
    from src.workflows.job_search.tools import BLOCKED_DOMAINS

    expected = ["instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com"]
    for domain in expected:
        assert domain in BLOCKED_DOMAINS


# =============================================================================
# tools.py - Retry Behavior
# =============================================================================


class TestRetryBehavior:
    """Tests for retry logic with tenacity."""

    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self, tmp_path):
        """Retries search on transient failures and succeeds."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        # Mock wrapper that fails twice then succeeds
        mock_results = [
            {"title": "Result 1", "link": "https://example.com/1", "snippet": "test"},
        ]

        call_count = 0

        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient failure")
            return mock_results

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = failing_then_success

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
            patch.object(tools, "langfuse"),
        ):
            # Reset retry state by reimporting
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            assert call_count == 3
            assert "Result 1" in result

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self, tmp_path):
        """Returns error message after exhausting all retries."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(side_effect=ConnectionError("Persistent failure"))

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
            patch.object(tools, "langfuse"),
        ):
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            assert "Search failed after retries" in result


# =============================================================================
# tools.py - Result Buffering
# =============================================================================


class TestResultBuffering:
    """Tests for result buffering (request 2x, return 10)."""

    @pytest.mark.asyncio
    async def test_returns_max_10_results(self, tmp_path):
        """Returns at most 10 results even when more are available."""
        from unittest.mock import AsyncMock, patch

        from src.workflows.job_search import tools

        # Create 20 mock results
        mock_results = [
            {"title": f"Result {i}", "link": f"https://example.com/{i}", "snippet": f"test {i}"}
            for i in range(20)
        ]

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(return_value=mock_results)

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.touch()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
            patch.object(tools, "langfuse"),
        ):
            from src.workflows.job_search.tools import web_search

            result = await web_search.ainvoke({"query": "test query"})

            # Count number of results by counting the separators
            result_count = result.count("---") + 1 if "---" in result else 1
            assert result_count <= 10


# =============================================================================
# tools.py - Langfuse Metadata
# =============================================================================


class TestLangfuseMetadata:
    """Tests for Langfuse span metadata."""

    @pytest.mark.asyncio
    async def test_logs_search_metrics_to_langfuse(self, tmp_path):
        """Logs results_original, results_after_filter, seen_urls_filtered."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.workflows.job_search import tools

        mock_results = [
            {"title": "Result 1", "link": "https://example.com/1", "snippet": "test"},
            {"title": "Result 2", "link": "https://example.com/2", "snippet": "test"},
            {"title": "Seen Result", "link": "https://seen.com/1", "snippet": "already seen"},
        ]

        mock_wrapper = AsyncMock()
        mock_wrapper.aresults = AsyncMock(return_value=mock_results)

        seen_urls_file = tmp_path / "seen_urls.txt"
        seen_urls_file.write_text("https://seen.com/1\n")

        mock_langfuse = MagicMock()

        with (
            patch.object(tools, "get_wrapper", return_value=mock_wrapper),
            patch.object(tools, "SEEN_URLS_PATH", seen_urls_file),
            patch.object(tools, "langfuse", mock_langfuse),
        ):
            from src.workflows.job_search.tools import web_search

            await web_search.ainvoke({"query": "test query"})

            # Verify update_current_span was called with correct metadata
            mock_langfuse.update_current_span.assert_called_once()
            call_kwargs = mock_langfuse.update_current_span.call_args[1]
            metadata = call_kwargs["metadata"]

            assert metadata["results_original"] == 3
            assert metadata["results_after_filter"] == 2
            assert metadata["seen_urls_filtered"] == 1


# =============================================================================
# tools.py - Configurable Engines
# =============================================================================


class TestConfigurableEngines:
    """Tests for configurable search engines from settings."""

    def test_wrapper_uses_engines_from_config(self):
        """get_wrapper() creates wrapper with engines from settings."""
        from unittest.mock import MagicMock, patch

        from src.workflows.job_search import tools

        # Reset the global wrapper
        tools._wrapper = None

        mock_settings = MagicMock()
        mock_settings.searxng_host = "http://localhost:8080"
        mock_settings.searxng_engines = "brave,qwant"
        mock_settings.search_result_buffer = 2.0

        with patch.object(tools, "settings", mock_settings):
            wrapper = tools.get_wrapper()

            assert wrapper.engines == ["brave", "qwant"]
            assert wrapper.k == 20  # 10 * 2.0

        # Clean up
        tools._wrapper = None

    def test_wrapper_uses_buffer_multiplier(self):
        """get_wrapper() applies search_result_buffer to k."""
        from unittest.mock import MagicMock, patch

        from src.workflows.job_search import tools

        # Reset the global wrapper
        tools._wrapper = None

        mock_settings = MagicMock()
        mock_settings.searxng_host = "http://localhost:8080"
        mock_settings.searxng_engines = "duckduckgo"
        mock_settings.search_result_buffer = 3.0

        with patch.object(tools, "settings", mock_settings):
            wrapper = tools.get_wrapper()

            assert wrapper.k == 30  # 10 * 3.0

        # Clean up
        tools._wrapper = None
