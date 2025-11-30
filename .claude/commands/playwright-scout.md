Discover safe Playwright automation patterns for: $ARGUMENTS

Use the **Playwright MCP** to explore the target website and create a safe, parameterized function.

## Safety Philosophy

Agents should never have arbitrary browser access. Instead of generic `browse(url, action)` functions, create specific, pre-defined commands:

```python
# Goal-oriented function with clear purpose
async def search_site_for_items(query: str, location: str) -> list[Item]: ...
```

## Discovery Process (using Playwright MCP)

1. **Navigate** to the target site
2. **Identify** key elements: forms, inputs, buttons, result containers
3. **Document** CSS selectors for each element
4. **Note** anti-bot measures, rate limits, pagination patterns
5. **Test** the selectors work reliably

## Output

Provide a self-contained Python function:

```python
async def descriptive_function_name(
    page: Page,
    param1: str,
    param2: str,
) -> list[ResultType]:
    """
    Brief description of what this does.

    Selectors (document for maintenance):
        search_input: "input[name='q']"
        submit_btn: "button[type='submit']"
        results: ".result-item"
    """
    # Implementation
```

## Best Practices

- Use `page.wait_for_selector()` before interacting
- Add small delays between actions (`page.wait_for_timeout(500)`)
- Handle pagination gracefully
- Return empty list on error (don't crash the agent)
- Keep functions focused on ONE specific task
