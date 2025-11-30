# Agent Development Guide

**Status**: No agents exist yet. This guide will be expanded as we build agents.

## Current State

The AI Agents project has completed Phase 1 (foundation) but has not yet implemented any agents. The core LLM factory is ready, but agent development starts in Phase 2.

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for the development roadmap.

## Planned Approach

Agents will be built using **LangGraph** with the **ReAct pattern**.

### LangGraph's `create_react_agent`

The planned architecture uses LangGraph's `create_react_agent` function, which implements:

1. **Reasoning**: Agent thinks about what to do next
2. **Action**: Agent calls a tool if needed
3. **Observation**: Agent sees the tool result
4. **Loop**: Repeat until task is complete

This pattern enables agents to:
- Break down complex tasks into steps
- Use tools to interact with the world
- Self-correct based on observations
- Know when to stop

### Example (Future)

Once implemented, agents will look something like this:

```python
from langgraph.prebuilt import create_react_agent
from src.core.llm import get_agent_llm
from src.tools.web_search import web_search_tool

# Create agent with tools
agent = create_react_agent(
    model=get_agent_llm(),
    tools=[web_search_tool],
)

# Run agent
result = agent.invoke({
    "messages": [("user", "Find recent news about AI agents")]
})
```

## Next Steps

**Phase 2** will implement the first simple test agent to validate:
- Tool calling works with local models
- ReAct loop executes correctly
- Agent can reason and self-correct

Check back after Phase 2 for concrete examples and patterns.

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph ReAct Pattern](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [Qwen 2.5 Tool Calling](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
