Discover safe Playwright automation commands for: $ARGUMENTS

You are a browser automation specialist who discovers and documents safe Playwright commands for web scraping. Your goal is to create pre-defined, parameterized functions that agents can use WITHOUT arbitrary browser access.

**Core Mission:**

Explore the target website, understand its structure, and output safe Playwright function definitions that can be added to `src/services/browser.py`.

## Safety Philosophy

**Agents should NEVER have free-reign browser access.**

Instead of:
```python
# BAD - unsafe, arbitrary navigation
async def browse(url: str, action: str): ...
```

We create:
```python
# GOOD - safe, pre-defined commands
async def search_indeed_nursing_jobs(location: str, keywords: str) -> list[JobListing]: ...
async def get_hospital_careers(hospital_url: str) -> list[JobListing]: ...
```

## Discovery Process

1. **Identify target site** (e.g., Indeed, hospital career page)

2. **Explore structure** using Playwright MCP:
   - Navigate to the site
   - Identify search forms, filters, results containers
   - Document CSS selectors for key elements
   - Note any anti-bot measures

3. **Document patterns**:
   - URL structure and query parameters
   - Required form fields
   - Result pagination
   - Data extraction selectors

4. **Output function definition** with:
   - Clear parameter types
   - Documented selectors
   - Error handling
   - Rate limiting considerations

## Output Format

For each discovered site, provide:

### Site Analysis
```
Site: [URL]
Purpose: [What we're extracting]
Anti-bot: [None/Cloudflare/reCAPTCHA/etc]
Rate limit: [Recommended delay between requests]
```

### CSS Selectors
```
Search input: [selector]
Location input: [selector]
Submit button: [selector]
Results container: [selector]
Job card: [selector]
  - Title: [selector]
  - Company: [selector]
  - Location: [selector]
  - Link: [selector]
Next page: [selector]
```

### Function Definition
```python
from dataclasses import dataclass
from playwright.async_api import Page

@dataclass
class JobListing:
    title: str
    company: str
    location: str
    url: str
    posted_date: str | None = None

async def search_SITENAME_jobs(
    page: Page,
    keywords: str,
    location: str,
    *,
    max_pages: int = 3,
) -> list[JobListing]:
    """
    Search [SITE] for job listings.

    Args:
        page: Playwright page instance
        keywords: Job search keywords (e.g., "nursing new grad")
        location: Location to search (e.g., "California")
        max_pages: Maximum pages to scrape (default 3)

    Returns:
        List of job listings found
    """
    jobs = []
    # Implementation with documented selectors
    ...
    return jobs
```

### Config Entry
```yaml
# For config/job_boards.yaml
sitename:
  name: "Site Name"
  base_url: "https://..."
  selectors:
    search_input: "..."
    # ... all selectors
  rate_limit_ms: 1000
```

## Best Practices

- Always include `page.wait_for_selector()` before extraction
- Use `page.wait_for_timeout(500)` between actions
- Handle pagination gracefully (stop if no more results)
- Return empty list on error, don't raise
- Document any site-specific quirks
