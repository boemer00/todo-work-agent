"""
State schema for the LangGraph agent.

Defines the structure of data that flows through the graph.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    """
    State Schema for our agent.

    Fields:
        messages: The conversation history between user and agent.
                  The `add_messages` annotation means new messages get appended (not replaced).
        user_id: The ID of the user interacting with the agent.
                 Used to isolate tasks per user.
    """
    messages: Annotated[list, add_messages]  # Conversation history
    user_id: str  # User identifier for multi-user support
