"""
Graph construction for the LangGraph agent.

Builds and compiles the agent workflow with checkpointing support.
"""

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from .state import State
from .nodes import agent_node, should_continue, create_tool_node
from database.connection import get_db_path


def create_graph():
    """
    Construct the agent graph with persistence.

    Flow:
    START → agent → (decision)
                    ├─→ tools → agent (loop back)
                    └─→ END (done)

    Features:
    - LangGraph checkpointing for conversation memory
    - SQLite backend for state persistence
    - Supports resume, undo, and time-travel debugging

    Returns:
        Compiled graph with checkpointing enabled
    """
    # Initialize checkpointer for conversation memory
    # This saves the entire state after each node execution
    import sqlite3
    checkpoint_db_path = get_db_path("checkpoints.db")
    conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    # Initialize graph with our State schema
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("agent", agent_node)
    builder.add_node("tools", create_tool_node())

    # Add edges
    builder.add_edge(START, "agent")  # Always start with agent

    # Conditional edge: agent decides whether to call tools or finish
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # If "tools" returned, go to tools node
            "end": END         # If "end" returned, finish
        }
    )

    # After tools execute, loop back to agent
    builder.add_edge("tools", "agent")

    # Compile the graph with checkpointing enabled
    # The checkpointer automatically saves state after each node
    return builder.compile(checkpointer=memory)
