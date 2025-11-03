"""
State schema for the LangGraph agent.

Defines the structure of data that flows through the graph.
"""

from typing import Annotated, Optional
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
        plan: Optional plan for complex multi-step requests.
              When present, agent should follow the plan step-by-step.
        plan_step: Current step number in the plan (0-indexed).
                   Increments as each step is completed.
    """
    messages: Annotated[list, add_messages]  # Conversation history
    user_id: str  # User identifier for multi-user support
    plan: Optional[str]  # Multi-step plan for complex requests
    plan_step: int  # Current step in plan (default: 0)
