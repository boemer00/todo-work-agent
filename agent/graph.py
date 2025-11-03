"""
Graph construction for the LangGraph agent.

Builds and compiles the agent workflow with checkpointing support.
"""

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from .state import State
from .nodes import (
    agent_node,
    should_continue,
    tool_node_with_state_injection,
    planner_node,
    reflection_node,
    should_plan,
    should_reflect
)
from database.connection import get_db_path


def create_graph():
    """
    Construct the agent graph with persistence and planning capabilities.

    Flow (with planning):
    START → (check complexity) → planner OR agent
                                   ↓          ↓
                                 agent ← ← ← ┘
                                   ↓
                              (has tools?)
                                   ↓
                                 tools
                                   ↓
                              (has plan?)
                                   ↓
                           reflection OR agent
                                   ↓          ↓
                                 agent ← ← ← ┘
                                   ↓
                                  END

    Features:
    - Plan-Execute pattern for complex multi-step requests
    - Reflection node to track progress through plans
    - Simple requests bypass planning for efficiency
    - LangGraph checkpointing for conversation memory
    - SQLite backend for state persistence

    Returns:
        Compiled graph with checkpointing enabled
    """
    # Initialize checkpointer for conversation memory
    # This saves the entire state after each node execution
    import sqlite3
    checkpoint_db_path = get_db_path("checkpoints.db")

    # Thread-safe SQLite configuration for concurrent FastAPI requests
    # - check_same_thread=False: Allow connection use across threads (required for ThreadPoolExecutor)
    # - timeout=10.0: Wait up to 10 seconds for lock instead of failing immediately
    # - WAL mode: SQLite's Write-Ahead Logging enables concurrent readers + serialized writers
    conn = sqlite3.connect(
        checkpoint_db_path,
        check_same_thread=False,
        timeout=10.0
    )
    conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for thread safety

    memory = SqliteSaver(conn)

    # Initialize graph with our State schema
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("planner", planner_node)                    # Creates plan for complex requests
    builder.add_node("agent", agent_node)                        # Main reasoning node
    builder.add_node("tools", tool_node_with_state_injection)    # Tool execution with user_id injection
    builder.add_node("reflection", reflection_node)              # Progress tracking

    # Entry point: Check if request needs planning
    builder.add_conditional_edges(
        START,
        should_plan,
        {
            "planner": "planner",  # Complex request → create plan first
            "agent": "agent"       # Simple request → go directly to agent
        }
    )

    # After planning, go to agent
    builder.add_edge("planner", "agent")

    # Agent decides whether to call tools or finish
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # If agent wants to use tools
            "end": END         # If agent is done
        }
    )

    # After tools execute, check if we need reflection
    builder.add_conditional_edges(
        "tools",
        should_reflect,
        {
            "reflection": "reflection",  # If following a plan
            "agent": "agent"              # If no plan, back to agent
        }
    )

    # After reflection, loop back to agent for next step
    builder.add_edge("reflection", "agent")

    # Compile the graph with checkpointing enabled
    # The checkpointer automatically saves state after each node
    return builder.compile(checkpointer=memory)
