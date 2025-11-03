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
from config.settings import get_llm_with_tools, get_tools, get_llm, SYSTEM_MESSAGE

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


# ========================================
# Planning & Reflection Nodes
# ========================================

PLANNER_PROMPT = """You are a planning assistant. The user has made a complex request that requires multiple steps.

Create a clear, numbered plan to accomplish their goal. Keep it simple and actionable.

Guidelines:
- Create 2-5 steps maximum (keep it simple!)
- Each step should be a concrete action (e.g., "List all tasks", "Check calendar")
- Don't over-plan - only break down truly complex requests
- If the request is simple, return "NO_PLAN_NEEDED"

Examples:

Request: "organize my week"
Plan:
1. List all current tasks
2. Check which tasks have due dates
3. Prioritize tasks by deadline
4. Suggest a schedule

Request: "prepare for tomorrow"
Plan:
1. List tasks due tomorrow
2. Check tomorrow's calendar
3. Suggest preparation steps

Request: "add milk to my list"
Plan: NO_PLAN_NEEDED

Now create a plan for the user's request."""


def planner_node(state: State) -> Dict[str, Any]:
    """
    The Planner Node: Creates a multi-step plan for complex requests.

    This node analyzes the user's message and decides if it needs planning.
    For simple requests (like "add milk"), it returns NO_PLAN_NEEDED.
    For complex requests (like "organize my week"), it creates a numbered plan.

    Args:
        state: Current state containing messages

    Returns:
        Dictionary with plan (if needed) and plan_step=0
    """
    messages = state["messages"]
    last_user_message = None

    # Find the last user message
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break

    if not last_user_message:
        return {"plan": None, "plan_step": 0}

    # Create planning prompt
    planning_messages = [
        SystemMessage(content=PLANNER_PROMPT),
        SystemMessage(content=f"User request: {last_user_message}")
    ]

    try:
        llm = get_llm_with_tools()
        response = llm.invoke(planning_messages)
        plan_text = response.content.strip()

        # Check if planning is needed
        if "NO_PLAN_NEEDED" in plan_text.upper():
            logger.info("Planner: Simple request detected, no plan needed")
            return {"plan": None, "plan_step": 0}

        # Plan created
        logger.info(f"Planner: Created plan:\n{plan_text}")

        # Add plan as a system message so agent can see it
        plan_message = SystemMessage(content=f"📋 Plan:\n{plan_text}\n\nFollow this plan step-by-step.")

        return {
            "plan": plan_text,
            "plan_step": 0,
            "messages": [plan_message]
        }

    except Exception as e:
        logger.error(f"Error in planner_node: {e}")
        # If planning fails, just proceed without a plan
        return {"plan": None, "plan_step": 0}


def reflection_node(state: State) -> Dict[str, Any]:
    """
    The Reflection Node: Evaluates progress through the plan.

    After tools execute, this node checks:
    1. Did we accomplish the current step in the plan?
    2. Should we move to the next step?
    3. Is the plan complete?

    Args:
        state: Current state containing plan, plan_step, and messages

    Returns:
        Dictionary with updated plan_step or plan completion status
    """
    plan = state.get("plan")
    plan_step = state.get("plan_step", 0)

    # If no plan, skip reflection
    if not plan:
        return {}

    messages = state["messages"]

    # Simple reflection: Check if we got a tool result
    # If yes, increment plan_step
    last_message = messages[-1] if messages else None

    if last_message and hasattr(last_message, 'type') and last_message.type == 'tool':
        # Tool executed successfully, move to next step
        new_step = plan_step + 1

        # Count how many steps are in the plan (simple heuristic: count numbered lines)
        plan_lines = [line.strip() for line in plan.split('\n') if line.strip()]
        numbered_steps = [line for line in plan_lines if line and line[0].isdigit()]
        total_steps = len(numbered_steps)

        if new_step >= total_steps:
            # Plan complete!
            logger.info("Reflection: Plan completed!")
            completion_message = SystemMessage(
                content="✅ Plan completed! Now provide a final summary to the user."
            )
            return {
                "plan": None,  # Clear the plan
                "plan_step": 0,
                "messages": [completion_message]
            }
        else:
            # Move to next step
            logger.info(f"Reflection: Step {plan_step + 1} complete, moving to step {new_step + 1}")
            next_step_message = SystemMessage(
                content=f"✓ Step {plan_step + 1} complete. Now proceed to step {new_step + 1}."
            )
            return {
                "plan_step": new_step,
                "messages": [next_step_message]
            }

    # No tool result yet, continue with current step
    return {}


# ========================================
# Routing Functions
# ========================================

def should_plan(state: State) -> Literal["planner", "agent"]:
    """
    Router: Decides if the request needs planning.

    Checks for keywords and patterns that indicate a complex, multi-step request.
    Simple requests go directly to the agent.

    Args:
        state: Current state containing messages

    Returns:
        "planner" if complex request needs planning, "agent" otherwise
    """
    messages = state["messages"]

    # Find the last user message
    last_user_message = None
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content.lower()
            break

    if not last_user_message:
        return "agent"

    # Keywords that indicate complex requests needing planning
    planning_keywords = [
        "organize", "plan", "prepare", "schedule",
        "prioritize", "what should", "help me with",
        "figure out", "my week", "my day", "my tomorrow"
    ]

    # Check if any planning keyword is in the message
    needs_planning = any(keyword in last_user_message for keyword in planning_keywords)

    if needs_planning:
        logger.info(f"Router: Complex request detected, routing to planner")
        return "planner"
    else:
        logger.info(f"Router: Simple request, routing directly to agent")
        return "agent"


def should_reflect(state: State) -> Literal["reflection", "agent"]:
    """
    Router: Decides if reflection is needed after tool execution.

    If we're following a plan, route to reflection to check progress.
    Otherwise, go back to agent directly.

    Args:
        state: Current state with plan information

    Returns:
        "reflection" if following a plan, "agent" otherwise
    """
    plan = state.get("plan")

    if plan:
        logger.info("Router: Plan active, routing to reflection")
        return "reflection"
    else:
        return "agent"
