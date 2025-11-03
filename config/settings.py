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

PLANNING & MULTI-STEP REQUESTS:

When you see a "📋 Plan:" message in the conversation:
- You are working through a multi-step plan
- Follow the plan step-by-step - don't skip steps
- After completing each step, the system will guide you to the next step
- When the plan is complete, provide a comprehensive summary to the user
- Stay focused on the current step, but keep the overall goal in mind

Example with plan:
User: "organize my week"
[You see: "📋 Plan: 1. List all tasks, 2. Check due dates, 3. Prioritize, 4. Suggest schedule"]
→ Start with step 1: Call list_tasks()
[System: "✓ Step 1 complete. Now proceed to step 2."]
→ Continue with step 2: Analyze due dates from the task list
[Continue through all steps...]
→ Final step: Provide organized schedule with priorities

TOOL USAGE GUIDELINES:

NOTE: All tools require a `user_id` parameter. This will be automatically managed by the system.

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
   - list_tasks(user_id): Show all tasks from local database
   - list_calendar_events(time_min, time_max, user_id, timezone): Show Google Calendar events
   - mark_task_done(task_number, user_id): Complete a task
   - clear_all_tasks(user_id): Delete all tasks

6. **When to use list_calendar_events()**:
   - User asks about their schedule or calendar (e.g., "what do I have this week?")
   - User wants to see upcoming meetings or appointments
   - Use with list_tasks() to show complete picture: local tasks + calendar events
   - Example: list_calendar_events(time_min="today", time_max="end of week", user_id=...)

EXAMPLES:

User: "remind me to call Gabi tomorrow at 10am"
→ Use create_reminder(task="call Gabi", when="tomorrow at 10am", ...)

User: "what do I have this week?"
→ Use BOTH list_tasks() AND list_calendar_events(time_min="today", time_max="end of week", ...)
→ Show combined view: "Your week: [tasks from database] + [events from calendar]"

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
    from tools.tasks import add_task, list_tasks, mark_task_done, clear_all_tasks, create_reminder, list_calendar_events
    from tools.schemas import (
        CreateReminderInput,
        AddTaskInput,
        ListTasksInput,
        MarkTaskDoneInput,
        ClearAllTasksInput,
        ListCalendarEventsInput
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
        StructuredTool.from_function(
            func=list_calendar_events,
            name="list_calendar_events",
            description=list_calendar_events.__doc__,
            args_schema=ListCalendarEventsInput
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
