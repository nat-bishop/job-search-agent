"""Tests for the job search workflow.

Tests cover:
- Memory file initialization (agent.py)
- Prompt loading with date injection (agent.py)
- URL tracking helpers (tools.py)
- URL blocking for social media and PDFs (tools.py)
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

        with patch.object(agent, "MEMORIES_DIR", memories_dir), \
             patch.object(agent, "JOBS_FILE", jobs_file), \
             patch.object(agent, "SEEN_URLS_FILE", seen_urls_file):

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

        with patch.object(agent, "MEMORIES_DIR", memories_dir), \
             patch.object(agent, "JOBS_FILE", jobs_file), \
             patch.object(agent, "SEEN_URLS_FILE", seen_urls_file):

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

        with patch.object(agent, "MEMORIES_DIR", memories_dir), \
             patch.object(agent, "JOBS_FILE", jobs_file), \
             patch.object(agent, "SEEN_URLS_FILE", seen_urls_file):

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

        with patch.object(agent, "MEMORIES_DIR", memories_dir), \
             patch.object(agent, "JOBS_FILE", jobs_file), \
             patch.object(agent, "SEEN_URLS_FILE", seen_urls_file):

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

        with patch.object(agent, "MEMORIES_DIR", memories_dir), \
             patch.object(agent, "JOBS_FILE", jobs_file), \
             patch.object(agent, "SEEN_URLS_FILE", seen_urls_file):

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
            "system_prompt: |\n"
            "  Today is {current_date}.\n"
            "  Do the thing.\n"
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
            "https://example.com/job1\n"
            "https://example.com/job2\n"
            "https://example.com/job3\n"
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

        result = await fetch.ainvoke(
            {"url": "https://www.linkedin.com/jobs/view/12345"}
        )
        assert "Skipped social media" in result
        assert "authentication" in result

    @pytest.mark.asyncio
    async def test_blocks_instagram_urls(self):
        """Blocks Instagram URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke(
            {"url": "https://www.instagram.com/ucsfhealthcareers"}
        )
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_facebook_urls(self):
        """Blocks Facebook URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke(
            {"url": "https://www.facebook.com/StanfordHealth"}
        )
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_twitter_urls(self):
        """Blocks Twitter URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke(
            {"url": "https://twitter.com/ucsfhealth"}
        )
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_x_urls(self):
        """Blocks X (formerly Twitter) URLs."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke({"url": "https://x.com/ucsfhealth"})
        assert "Skipped social media" in result

    @pytest.mark.asyncio
    async def test_blocks_pdf_urls(self):
        """Blocks PDF URLs with helpful message."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke(
            {"url": "https://example.com/nurse-residency-flyer.pdf"}
        )
        assert "Cannot fetch PDF" in result
        assert "HTML" in result  # Suggests searching for HTML page instead

    @pytest.mark.asyncio
    async def test_blocks_pdf_urls_case_insensitive(self):
        """PDF blocking is case-insensitive."""
        from src.workflows.job_search.tools import fetch

        result = await fetch.ainvoke(
            {"url": "https://example.com/document.PDF"}
        )
        assert "Cannot fetch PDF" in result


# =============================================================================
# Smoke Tests (verify imports work)
# =============================================================================


def test_job_search_agent_imports():
    """Verify job search workflow can be imported."""
    from langchain_core.tools import StructuredTool

    from src.workflows.job_search.agent import create_job_search_agent
    from src.workflows.job_search.tools import fetch, web_search

    assert callable(create_job_search_agent)
    # @tool decorator wraps functions as StructuredTool instances
    assert isinstance(web_search, StructuredTool)
    assert isinstance(fetch, StructuredTool)


def test_blocked_domains_list():
    """Verify BLOCKED_DOMAINS contains expected social media sites."""
    from src.workflows.job_search.tools import BLOCKED_DOMAINS

    expected = ["instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com"]
    for domain in expected:
        assert domain in BLOCKED_DOMAINS
