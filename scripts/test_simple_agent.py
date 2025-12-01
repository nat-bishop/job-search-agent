"""Quick test script for the simple agent.

Requires Ollama running with qwen2.5:7b model:
    ollama pull qwen2.5:7b
    ollama serve
"""

from src.core.tracing import get_langfuse_handler
from src.workflows.simple.agent import create_simple_agent


def main():
    print("Simple Agent Test")
    print("=" * 40)
    print("Tools: get_current_time")
    print("Type 'quit' to exit\n")

    # Create agent and tracing handler
    print("Connecting to Ollama...")
    try:
        agent = create_simple_agent()
        langfuse_handler = get_langfuse_handler()
        print("Connected!\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama serve")
        print("  ollama pull qwen2.5:7b")
        return

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

        # Run the agent with tracing
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"callbacks": [langfuse_handler]},
            )

            # Get the last message (agent's response)
            last_message = result["messages"][-1]
            print(f"Agent: {last_message.content}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
