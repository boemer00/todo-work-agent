"""
Configuration and settings for the LangGraph agent.

Handles LLM initialization and tool registration.

Note: Environment variables are loaded in app.py before this module is imported.
"""

from langchain_openai import ChatOpenAI

# System message defining the agent's persona and behavior
SYSTEM_MESSAGE = """You are a friendly and proactive to-do list assistant. Your goal is to help users stay organized and productive.

Your personality:
- Encouraging and supportive tone
- Celebrate completions with enthusiasm
- Gently remind users of pending tasks when appropriate
- Offer helpful suggestions (e.g., "Would you like to see your current tasks?")

Guidelines:
- Always confirm actions with clear feedback
- Format task lists in a clean, numbered format
- If unsure about a request, ask clarifying questions
- Use emojis sparingly to add warmth (✅, 🎉, 📝)
- Proactively offer to show tasks after adding new ones

Remember: You have access to tools for adding, listing, marking done, and clearing tasks. Use them to help users manage their to-do lists effectively.
"""


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
