"""
LangSmith configuration and tracing setup.

Enables automatic tracing of:
- LLM calls (tokens, latency, cost)
- Tool executions (which tools, duration, success/failure)
- Agent reasoning (decisions, state changes)
"""

import os
from typing import Dict, Any, Optional
from langsmith import Client


def setup_langsmith() -> bool:
    """
    Initialize LangSmith tracing.

    Reads from environment variables:
    - LANGSMITH_API_KEY: Your LangSmith API key
    - LANGSMITH_PROJECT: Project name (defaults to "langchain-academy")
    - LANGSMITH_TRACING_V2 or LANGSMITH_TRACING: Enable tracing (defaults to "true")
    - LANGSMITH_ENDPOINT: API endpoint (optional, for EU/custom instances)

    Returns:
        bool: True if LangSmith is configured, False otherwise
    """
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        print("⚠️  LANGSMITH_API_KEY not found. Tracing disabled.")
        return False

    # Set defaults if not already set
    # Note: LANGSMITH_TRACING is the old name, LANGSMITH_TRACING_V2 is newer
    if not os.getenv("LANGSMITH_TRACING_V2") and not os.getenv("LANGSMITH_TRACING"):
        os.environ["LANGSMITH_TRACING_V2"] = "true"

    if not os.getenv("LANGSMITH_PROJECT"):
        os.environ["LANGSMITH_PROJECT"] = "my-todo-agent"

    project = os.getenv("LANGSMITH_PROJECT")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    # Determine base URL for the UI
    if "eu.api.smith.langchain.com" in endpoint:
        base_url = "https://eu.smith.langchain.com"
    else:
        base_url = "https://smith.langchain.com"

    print(f"✓ LangSmith tracing enabled")
    print(f"  Project: {project}")
    print(f"  API Endpoint: {endpoint}")
    print(f"  View traces: {base_url}")
    print(f"")
    print(f"  💡 After running the agent, check for traces at:")
    print(f"     {base_url} → Projects → '{project}'")

    return True


def add_metadata(
    user_id: str,
    thread_id: str,
    session_type: str = "interactive",
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create metadata dictionary for LangSmith traces.

    This metadata will appear in every trace, making it easy to:
    - Filter traces by user
    - Track specific sessions
    - Group related requests

    Args:
        user_id: The user interacting with the agent
        thread_id: The conversation thread ID
        session_type: Type of session (interactive, api, test)
        additional_metadata: Any extra metadata to include

    Returns:
        Dictionary of metadata for LangSmith

    Example:
        metadata = add_metadata(
            user_id="alice",
            thread_id="alice_session_123",
            session_type="interactive",
            additional_metadata={"deployment": "staging"}
        )
    """
    metadata = {
        "user_id": user_id,
        "thread_id": thread_id,
        "session_type": session_type,
        "agent_type": "todo_assistant",
        "agent_version": "1.0.0",
    }

    if additional_metadata:
        metadata.update(additional_metadata)

    return metadata


def get_langsmith_client() -> Optional[Client]:
    """
    Get LangSmith client for programmatic access.

    Use this to:
    - Query traces programmatically
    - Create evaluation datasets
    - Analyze metrics

    Returns:
        LangSmith Client or None if not configured
    """
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        return None

    return Client()
