"""Test the simple workflow with updated tool documentation pattern.

Tests:
1. Basic time query (uses get_current_time tool)
2. Agent response without tools
3. Research delegation (subagent with web_search)

Run:
    python scripts/test_simple_workflow.py
"""

from src.workflows.simple.agent import create_simple_agent


def test_time_query():
    """Test that agent can use get_current_time tool."""
    print("\n" + "=" * 60)
    print("TEST 1: Time Query (should use get_current_time tool)")
    print("=" * 60)

    agent = create_simple_agent()

    result = agent.invoke({
        "messages": [{"role": "user", "content": "What time is it?"}]
    })

    # Print all messages to see tool calls
    print("\nConversation:")
    for i, msg in enumerate(result["messages"]):
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"\n[{i}] {role.upper()}: (called tool)")
            for tc in msg.tool_calls:
                print(f"  Tool: {tc['name']}")
                print(f"  Args: {tc['args']}")
        elif role == "tool":
            print(f"\n[{i}] TOOL RESULT:")
            try:
                print(f"  {content[:200]}")
            except UnicodeEncodeError:
                print(f"  {content[:200].encode('ascii', 'replace').decode('ascii')}")
        else:
            print(f"\n[{i}] {role.upper()}:")
            try:
                print(f"  {content[:300]}")
            except UnicodeEncodeError:
                print(f"  {content[:300].encode('ascii', 'replace').decode('ascii')}")

    # Check if tool was called
    tool_calls = [m for m in result["messages"] if hasattr(m, "tool_calls") and m.tool_calls]
    if tool_calls:
        print("\n[PASS] Agent used get_current_time tool")
    else:
        print("\n[FAIL] Agent did not call tool")

    return bool(tool_calls)


def test_simple_response():
    """Test agent can respond without tools."""
    print("\n" + "=" * 60)
    print("TEST 2: Simple Response (no tools needed)")
    print("=" * 60)

    agent = create_simple_agent()

    result = agent.invoke({
        "messages": [{"role": "user", "content": "Say hello!"}]
    })

    last_message = result["messages"][-1]
    try:
        print(f"\nAgent: {last_message.content}")
    except UnicodeEncodeError:
        print(f"\nAgent: {last_message.content.encode('ascii', 'replace').decode('ascii')}")

    if last_message.content:
        print("\n[PASS] Agent responded")
        return True
    else:
        print("\n[FAIL] Empty response")
        return False


def test_research_delegation():
    """Test research subagent delegation (if EXA_API_KEY is set)."""
    print("\n" + "=" * 60)
    print("TEST 3: Research Delegation (should use research subagent)")
    print("=" * 60)

    from src.core.config import settings

    if not settings.exa_api_key:
        print("\n[SKIP] EXA_API_KEY not configured")
        print("  Set EXA_API_KEY in .env to test web search")
        return None

    agent = create_simple_agent()

    print("\nAsking: What are the latest developments in AI?")
    print("(This may take 30-60 seconds with the 120B model...)\n")

    result = agent.invoke({
        "messages": [{"role": "user", "content": "What are the latest developments in AI? Keep it brief."}]
    })

    # Print conversation flow
    print("\nConversation:")
    for i, msg in enumerate(result["messages"]):
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"\n[{i}] {role.upper()}: (delegating)")
            for tc in msg.tool_calls:
                print(f"  Subagent: {tc['name']}")
        elif role == "tool":
            print(f"\n[{i}] SUBAGENT RESULT:")
            try:
                print(f"  {content[:300]}...")
            except UnicodeEncodeError:
                print(f"  {content[:300].encode('ascii', 'replace').decode('ascii')}...")
        else:
            print(f"\n[{i}] {role.upper()}:")
            try:
                print(f"  {content[:300]}")
            except UnicodeEncodeError:
                print(f"  {content[:300].encode('ascii', 'replace').decode('ascii')}")

    # Check if subagent was used
    subagent_calls = [m for m in result["messages"]
                      if hasattr(m, "tool_calls") and m.tool_calls
                      and any("research" in tc.get("name", "") for tc in m.tool_calls)]

    if subagent_calls:
        print("\n[PASS] Agent delegated to research subagent")
        return True
    else:
        print("\n[WARN] Agent did not delegate (may have answered directly)")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SIMPLE WORKFLOW TEST SUITE")
    print("=" * 60)
    print(f"Model: {__import__('src.core.config').core.config.settings.local_model}")

    results = {}

    # Test 1: Time query
    try:
        results["time_query"] = test_time_query()
    except Exception as e:
        print(f"\n[ERROR] in time query test: {e}")
        results["time_query"] = False

    # Test 2: Simple response
    try:
        results["simple_response"] = test_simple_response()
    except Exception as e:
        print(f"\n[ERROR] in simple response test: {e}")
        results["simple_response"] = False

    # Test 3: Research (optional)
    try:
        results["research"] = test_research_delegation()
    except Exception as e:
        print(f"\n[ERROR] in research test: {e}")
        results["research"] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test, result in results.items():
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"{status}: {test}")

    passed = sum(1 for r in results.values() if r is True)
    total = len([r for r in results.values() if r is not None])

    print(f"\nPassed: {passed}/{total}")

    if all(r in (True, None) for r in results.values()):
        print("\n[SUCCESS] All enabled tests passed!")
        return True
    else:
        print("\n[FAILED] Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
