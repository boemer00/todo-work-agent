"""
To-Do Agent - CLI Entry Point

A modular LangGraph agent with persistence for task management.

FEATURES:
- Task persistence (SQLite database)
- Conversation memory (LangGraph checkpointing)
- Multi-user support
- Clean modular architecture

USAGE:
    python app.py
    python app.py --user <username>
"""

import time
import argparse
import getpass
from langchain_core.messages import HumanMessage
from agent.graph import create_graph


def run_agent(user_id=None):
    """
    Run the agent in an interactive CLI loop.

    Args:
        user_id: Optional user ID for multi-user support.
                 If not provided, auto-detected from system username.

    Features:
    - Auto-detects user ID from system username
    - Generates unique thread ID for conversation tracking
    - Maintains conversation context across messages
    - Supports conversation resumption via thread_id
    """
    # Create the graph (includes checkpointing)
    graph = create_graph()

    # Auto-detect user ID if not provided
    if user_id is None:
        try:
            user_id = getpass.getuser()
        except Exception:
            user_id = "default"

    print("=" * 60)
    print("🤖 To-Do Agent with Persistence")
    print("=" * 60)

    # Generate unique thread ID for this conversation
    # Format: {user_id}_session_{timestamp}
    thread_id = f"{user_id}_session_{int(time.time())}"

    # Configuration for checkpointing
    # The thread_id tells LangGraph which conversation to track
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n✓ User: {user_id}")
    print(f"✓ Session ID: {thread_id}")
    print("\nCommands:")
    print("  - Type your message to interact with the agent")
    print("  - Type 'quit', 'exit', or 'q' to exit")
    print("=" * 60)
    print()

    # Initialize state with user_id
    # The user_id is used by tools to isolate tasks per user
    state = {"messages": [], "user_id": user_id}

    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!\n")
            break

        # Skip empty input
        if not user_input:
            continue

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))

        try:
            # Run the graph with thread_id for persistence
            # This executes the agent loop and returns final state
            result = graph.invoke(state, config)

            # Update our state with the result
            state = result

            # Get the last message (agent's response)
            last_message = state["messages"][-1]

            # Print agent response
            if hasattr(last_message, "content") and last_message.content:
                print(f"\n🤖 Agent: {last_message.content}\n")
            else:
                print("\n🤖 Agent: [No response]\n")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            # Don't crash - let user continue or quit


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="To-Do Agent with Persistence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                    # Auto-detect user from system
  python app.py --user alice       # Specify user explicitly
        """
    )
    parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="User ID for multi-user support (default: auto-detect from system)"
    )

    args = parser.parse_args()
    run_agent(user_id=args.user)
