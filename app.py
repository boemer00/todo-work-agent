"""
To-Do Agent - CLI Entry Point

A modular LangGraph agent with persistence for task management.

FEATURES:
- Task persistence (SQLite database)
- Conversation memory (LangGraph checkpointing)
- Multi-user support
- Clean modular architecture
- LangSmith observability (automatic tracing)

USAGE:
    python app.py
    python app.py --user <username>
"""

# CRITICAL: Clean up environment before ANY imports
import os
import sys

# WORKAROUND: Remove stale GOOGLE_APPLICATION_CREDENTIALS from shell environment
# This may be inherited from parent processes (terminal, IDE, etc.)
# We use either OAuth (CLOUD_RUN=false) or Secret Manager (CLOUD_RUN=true), not this env var
# Must happen BEFORE any Google client libraries are imported
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    print("⚠️  Cleaned up stale GOOGLE_APPLICATION_CREDENTIALS from environment")

# CRITICAL: Load environment variables FIRST, before any LangChain imports
# This ensures LangSmith tracing is activated when LLM is instantiated
from dotenv import load_dotenv
load_dotenv()

# Now setup LangSmith tracing BEFORE importing agent components
from monitoring import setup_langsmith, add_metadata
from monitoring.metrics import get_metrics
setup_langsmith()  # This must run before any LangChain components are created

# Standard library imports
import time
import argparse
import getpass

# LangChain imports (after environment is configured)
from langchain_core.messages import HumanMessage

# Agent imports (after LangSmith is configured)
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
    - LangSmith tracing for observability (already configured at module level)
    """
    # Create the graph (LangSmith tracing already active from module initialization)
    graph = create_graph()

    # Check if LangSmith is configured
    import os
    langsmith_enabled = bool(os.getenv("LANGSMITH_API_KEY"))

    # Auto-detect user ID if not provided
    if user_id is None:
        try:
            user_id = getpass.getuser()
        except Exception:
            user_id = "default"

    print("=" * 60)
    print("🤖 To-Do Agent with Persistence & Observability")
    print("=" * 60)

    # Generate unique thread ID for this conversation
    # Format: {user_id}_session_{timestamp}
    thread_id = f"{user_id}_session_{int(time.time())}"

    # Configuration for checkpointing + metadata
    # The thread_id tells LangGraph which conversation to track
    config = {"configurable": {"thread_id": thread_id}}

    # Add LangSmith metadata for tracing
    if langsmith_enabled:
        metadata = add_metadata(
            user_id=user_id,
            thread_id=thread_id,
            session_type="interactive"
        )
        config["metadata"] = metadata

    # Initialize metrics tracking
    metrics = get_metrics()
    metrics.track_session_start()

    print(f"\n✓ User: {user_id}")
    print(f"✓ Session ID: {thread_id}")
    if langsmith_enabled:
        print(f"✓ LangSmith Tracing: Enabled")
    print("\nCommands:")
    print("  - Type your message to interact with the agent")
    print("  - Type 'quit', 'exit', or 'q' to exit")
    print("  - Type 'metrics' to see performance summary")
    print("  - Type 'dashboard' to see full performance dashboard")
    print("=" * 60)
    print()

    # Initialize state with user_id
    # The user_id is used by tools to isolate tasks per user
    state = {"messages": [], "user_id": user_id, "plan_step": 0}

    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            # Show metrics summary on exit
            metrics.print_summary()
            break

        # Check for metrics command
        if user_input.lower() == "metrics":
            metrics.print_summary()
            continue

        # Check for dashboard command
        if user_input.lower() == "dashboard":
            from monitoring.performance_dashboard import display_dashboard
            display_dashboard()
            continue

        # Skip empty input
        if not user_input:
            continue

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))

        try:
            # Track response time
            start_time = time.time()

            # Stream the graph execution to show live progress
            # This makes 2.56s feel instant by providing immediate feedback
            # stream_mode="values" returns the FULL STATE after each node
            final_state = None
            step = 0
            for event in graph.stream(state, config, stream_mode="values"):
                step += 1
                # Show animated progress indicator
                spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                print(f"\r{spinner[step % len(spinner)]} Agent working...", end="", flush=True)

                # Keep the last event (this IS the full state with stream_mode="values")
                final_state = event

            # Clear the status line
            print("\r" + " "*25 + "\r", end="", flush=True)

            # Use the final state as result (now has correct structure)
            result = final_state if final_state else state

            # Calculate response time
            duration_ms = (time.time() - start_time) * 1000
            metrics.track_response_time(duration_ms)

            # Update our state with the result
            state = result

            # Track tool usage (scan messages for tool calls)
            for msg in state["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        metrics.track_tool_call(tool_call["name"])

            # Get the last message (agent's response)
            last_message = state["messages"][-1]

            # Print agent response
            if hasattr(last_message, "content") and last_message.content:
                print(f"🤖 Agent: {last_message.content}\n")
            else:
                print("🤖 Agent: [No response]\n")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            # Track the error
            metrics.track_error(
                error_type=type(e).__name__,
                error_msg=str(e),
                context={"user_id": user_id, "thread_id": thread_id}
            )
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
