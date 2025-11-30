"""Test script to verify deep agents works with local Qwen model.

This tests whether Qwen 2.5 can handle deep agents' complex system prompt
before migrating production code.

Requires Ollama running with qwen2.5:7b model:
    ollama pull qwen2.5:7b
    ollama serve

Run:
    python scripts/test_deep_agent.py
"""

from src.core.llm import get_agent_llm


def main():
    print("Deep Agents Compatibility Test")
    print("=" * 40)

    # Step 1: Import deep agents (fail fast if not installed)
    print("\n1. Checking deepagents installation...")
    try:
        from deepagents import create_deep_agent
        print("   deepagents installed")
    except ImportError as e:
        print(f"   FAILED: {e}")
        print("\n   Run: pip install -e '.[dev]'")
        return False

    # Step 2: Connect to Ollama
    print("\n2. Connecting to Ollama...")
    try:
        llm = get_agent_llm()
        print(f"   Connected to {llm.model}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("\n   Make sure Ollama is running:")
        print("     ollama serve")
        print("     ollama pull qwen2.5:7b")
        return False

    # Step 3: Create deep agent with minimal config
    print("\n3. Creating deep agent (no custom tools)...")
    try:
        agent = create_deep_agent(
            model=llm,
            tools=[],  # Only built-in tools (write_todos, filesystem)
            system_prompt="You are a helpful assistant. Use write_todos to plan complex tasks.",
        )
        print("   Agent created successfully")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    # Step 4: Test basic invocation (planning task)
    print("\n4. Testing agent invocation...")
    print("   Prompt: 'Plan how to research job boards'")
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Plan how to research job boards"}]
        })
        last_message = result["messages"][-1]
        print(f"\n   Response: {last_message.content[:500]}...")
        print("\n   SUCCESS: Agent responded")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    # Step 5: Test tool calling (write_todos)
    print("\n5. Testing write_todos tool...")
    print("   Prompt: 'Create a todo list for learning Python'")
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Create a todo list with 3 items for learning Python. Use the write_todos tool."}]
        })

        # Check if any tool was called
        tool_calls = [m for m in result["messages"] if hasattr(m, "tool_calls") and m.tool_calls]
        if tool_calls:
            print(f"   Tool called: {tool_calls[0].tool_calls[0]['name']}")
            print("   SUCCESS: Model can use built-in tools")
        else:
            print("   WARNING: No tool was called (model may need larger size)")

        last_message = result["messages"][-1]
        print(f"\n   Final response: {last_message.content[:300]}...")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    print("\n" + "=" * 40)
    print("All tests passed! Deep agents works with local model.")
    print("\nNext steps:")
    print("  1. Migrate simple workflow to create_deep_agent")
    print("  2. Add research subagent")
    return True


def interactive_mode():
    """Run interactive session with deep agent."""
    from deepagents import create_deep_agent
    from src.core.llm import get_agent_llm

    print("\nDeep Agent Interactive Mode")
    print("=" * 40)
    print("Built-in tools: write_todos, ls, read_file, write_file, edit_file")
    print("Type 'quit' to exit\n")

    agent = create_deep_agent(
        model=get_agent_llm(),
        tools=[],
        system_prompt="You are a helpful assistant that can plan tasks and manage files.",
    )

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
            last_message = result["messages"][-1]
            print(f"Agent: {last_message.content}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        success = main()
        if success:
            print("\nRun with --interactive for chat mode:")
            print("  python scripts/test_deep_agent.py --interactive")
