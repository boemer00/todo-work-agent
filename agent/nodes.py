"""
Agent nodes and routing logic.

Contains the agent node (LLM reasoning) and routing functions.
"""

from typing import Literal
from langgraph.prebuilt import ToolNode
from .state import State
from config.settings import get_llm_with_tools, get_tools


def agent_node(state: State) -> dict:
    """
    The Agent Node: Where the LLM thinks and decides what to do.

    This node:
    1. Takes all messages from state
    2. Sends them to the LLM with tools bound
    3. LLM either responds OR decides to call a tool
    4. Returns the LLM's response (which might include tool calls)

    Think of this as the "brain" of your agent.

    Args:
        state: Current state containing messages and user_id

    Returns:
        Dictionary with updated messages
    """
    messages = state["messages"]
    llm_with_tools = get_llm_with_tools()
    response = llm_with_tools.invoke(messages)

    # Return update to state - this will be merged with existing state
    return {"messages": [response]}


def should_continue(state: State) -> Literal["tools", "end"]:
    """
    Routing function: Determines the next step in the graph.

    Logic:
    - If the last message has tool_calls → route to "tools" node
    - Otherwise → route to END (we're done, return to user)

    This is the "decision maker" of your graph flow.

    Args:
        state: Current state containing messages

    Returns:
        "tools" if agent wants to call tools, "end" if done
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM decided to call tools, route to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, we're done - return response to user
    return "end"


def create_tool_node() -> ToolNode:
    """
    Create the tool node for executing tools.

    Uses LangGraph's prebuilt ToolNode which automatically:
    - Extracts tool calls from messages
    - Executes the appropriate tool functions
    - Formats results as ToolMessages

    Returns:
        Configured ToolNode instance
    """
    tools = get_tools()
    return ToolNode(tools)
