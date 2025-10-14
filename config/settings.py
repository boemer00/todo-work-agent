"""
Configuration and settings for the LangGraph agent.

Handles LLM initialization and tool registration.
"""

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_llm():
    """
    Initialize and return the LLM.

    Uses GPT-4o-mini by default for cost efficiency.
    Temperature is set to 0 for consistent, deterministic responses.

    Returns:
        Initialized ChatOpenAI instance
    """
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def get_tools():
    """
    Get all available tools for the agent.

    Note: We import tools here to avoid circular imports.
    The tools need user_id from state, which is passed automatically
    by LangGraph's ToolNode.

    Returns:
        List of tool functions
    """
    from tools.tasks import add_task, list_tasks, mark_task_done, clear_all_tasks

    return [add_task, list_tasks, mark_task_done, clear_all_tasks]


def get_llm_with_tools():
    """
    Get LLM with tools bound.

    The bind_tools() method tells the LLM about available functions,
    allowing it to decide when to call them.

    Returns:
        LLM instance with tools bound
    """
    llm = get_llm()
    tools = get_tools()
    return llm.bind_tools(tools)
