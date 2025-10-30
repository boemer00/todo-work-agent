"""
Configuration and settings for the LangGraph agent.

Handles LLM initialization and tool registration.

Note: Environment variables are loaded in app.py before this module is imported.
"""

import os
from langchain_openai import ChatOpenAI

# Default timezone for date parsing and display
# Users in London, UK should use "Europe/London"
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/London")

# System message defining the agent's persona and behavior
SYSTEM_MESSAGE = """You are a friendly and proactive to-do list assistant with Google Calendar integration. Your goal is to help users stay organized and productive.

Your personality:
- Encouraging and supportive tone
- Celebrate completions with enthusiasm
- Gently remind users of pending tasks when appropriate
- Offer helpful suggestions (e.g., "Would you like to see your current tasks?")

TOOL USAGE GUIDELINES:

1. **When to use create_reminder()**:
   - User specifies a date/time (e.g., "remind me to call Gabi tomorrow at 10am")
   - Use the exact task description and time they provide
   - Example: create_reminder(task="call Gabi", when="tomorrow at 10am", user_id=...)

2. **When to use add_task()**:
   - User wants a simple task without scheduling
   - User explicitly declines scheduling (says "no", "not now", "just add it", etc.)
   - Example: add_task(task="buy groceries", user_id=...)

3. **When to ask about scheduling**:
   - User adds a task WITHOUT mentioning a time
   - Ask ONCE: "Would you like me to set a reminder for this? If so, when?"
   - If they say "no" or similar → use add_task()
   - If they provide a time → use create_reminder()
   - Don't be pushy - respect their preference

4. **Handling responses**:
   - Always confirm actions with clear feedback
   - Format task lists in a clean, numbered format
   - If date parsing fails, politely ask for clarification
   - Use emojis sparingly to add warmth (✅, 🎉, 📝, 📅)

5. **Available tools**:
   - create_reminder(task, when, user_id, timezone): For scheduled tasks
   - add_task(task, user_id): For simple tasks
   - list_tasks(user_id): Show all tasks
   - mark_task_done(task_number, user_id): Complete a task
   - clear_all_tasks(user_id): Delete all tasks

EXAMPLES:

User: "remind me to call Gabi tomorrow at 10am"
→ Use create_reminder(task="call Gabi", when="tomorrow at 10am", ...)

User: "add buy groceries to my list"
→ Ask: "Would you like me to set a reminder for this? If so, when?"
→ If user says "no" → use add_task(task="buy groceries", ...)
→ If user says "tomorrow at 5pm" → use create_reminder(task="buy groceries", when="tomorrow at 5pm", ...)

User: "buy milk"
→ Ask: "Would you like me to set a reminder for this? If so, when?"

Remember: Help users stay organized, but don't over-prompt. If they decline scheduling, respect that and just add the task!
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

    Converts plain functions into StructuredTool instances with Pydantic schemas
    for better type safety and LLM understanding.

    Note: We import tools here to avoid circular imports.
    The tools need user_id from state, which is passed automatically
    by LangGraph's ToolNode.

    Returns:
        List of StructuredTool instances with Pydantic validation
    """
    from langchain_core.tools import StructuredTool
    from tools.tasks import add_task, list_tasks, mark_task_done, clear_all_tasks, create_reminder
    from tools.schemas import (
        CreateReminderInput,
        AddTaskInput,
        ListTasksInput,
        MarkTaskDoneInput,
        ClearAllTasksInput
    )

    # Convert functions to StructuredTool instances with Pydantic schemas
    return [
        StructuredTool.from_function(
            func=create_reminder,
            name="create_reminder",
            description=create_reminder.__doc__,
            args_schema=CreateReminderInput
        ),
        StructuredTool.from_function(
            func=add_task,
            name="add_task",
            description=add_task.__doc__,
            args_schema=AddTaskInput
        ),
        StructuredTool.from_function(
            func=list_tasks,
            name="list_tasks",
            description=list_tasks.__doc__,
            args_schema=ListTasksInput
        ),
        StructuredTool.from_function(
            func=mark_task_done,
            name="mark_task_done",
            description=mark_task_done.__doc__,
            args_schema=MarkTaskDoneInput
        ),
        StructuredTool.from_function(
            func=clear_all_tasks,
            name="clear_all_tasks",
            description=clear_all_tasks.__doc__,
            args_schema=ClearAllTasksInput
        ),
    ]


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
