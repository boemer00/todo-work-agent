"""
Agent nodes and routing logic.

Contains the agent node (LLM reasoning) and routing functions.
"""

import time
import logging
from typing import Literal, Dict, Any
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from openai import RateLimitError, APIError, APITimeoutError, APIConnectionError, AuthenticationError
from .state import State
from config.settings import get_llm_with_tools, get_tools, SYSTEM_MESSAGE

logger = logging.getLogger(__name__)


def agent_node(state: State) -> Dict[str, Any]:
    """
    The Agent Node: Where the LLM thinks and decides what to do.

    This node:
    1. Takes all messages from state
    2. Injects system message if not present
    3. Sends them to the LLM with tools bound
    4. LLM either responds OR decides to call a tool
    5. Returns the LLM's response (which might include tool calls)

    Think of this as the "brain" of your agent.

    Includes robust error handling for production:
    - Retries transient errors (rate limits, API errors, timeouts)
    - Fails gracefully with user-friendly messages
    - Logs all errors for debugging and monitoring

    Args:
        state: Current state containing messages and user_id

    Returns:
        Dictionary with updated messages
    """
    messages = state["messages"]

    # Inject system message at the start if not already present
    # This ensures the agent's persona is always active
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_MESSAGE)] + messages

    llm_with_tools = get_llm_with_tools()

    # Retry strategy: 3 attempts with exponential backoff (1s, 2s, 4s)
    # Total max delay: 7 seconds (acceptable for user experience)
    for attempt in range(3):
        try:
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}

        except (RateLimitError, APIError, APITimeoutError, APIConnectionError) as e:
            # Transient errors - worth retrying
            error_type = type(e).__name__
            if attempt < 2:  # Not the last attempt
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/3) with {error_type}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:  # Last attempt failed
                logger.error(f"LLM call failed after 3 attempts with {error_type}: {e}")
                return {"messages": [AIMessage(content=(
                    "I'm having trouble connecting to my brain right now. "
                    "This is usually temporary. Please try again in a moment, "
                    "or type 'help' if you need assistance."
                ))]}

        except AuthenticationError as e:
            # Permanent error - don't retry
            logger.error(f"OpenAI authentication error: {e}")
            return {"messages": [AIMessage(content=(
                "I'm experiencing an authentication issue. "
                "Please contact support if this persists."
            ))]}

        except Exception as e:
            # Unexpected error - log and fail gracefully
            logger.error(f"Unexpected error in agent_node: {type(e).__name__}: {e}", exc_info=True)
            return {"messages": [AIMessage(content=(
                "I encountered an unexpected error. "
                "Please try again, or type 'help' for assistance."
            ))]}

    # Should never reach here, but just in case
    return {"messages": [AIMessage(content=(
        "I'm experiencing technical difficulties. Please try again later."
    ))]}


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
