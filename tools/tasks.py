"""
Task management tools for the LangGraph agent.

These are the functions the LLM can call to manage tasks.
All tools interact with the database through the TaskRepository.
"""

from database.models import TaskRepository
from utils.date_parser import (
    extract_date_from_task,
    datetime_to_iso,
    format_datetime_for_display,
    is_date_in_past
)
from tools.google_calendar import create_calendar_event, delete_calendar_event

# Initialize the task repository (shared across all tool calls)
task_repo = TaskRepository()


def create_reminder(task: str, when: str, user_id: str, timezone: str = "UTC") -> str:
    """
    Create a reminder with a specific date/time and add it to Google Calendar.

    This tool combines task creation with calendar scheduling.
    Use this when the user specifies a date/time for their task.

    Args:
        task: The task description (e.g., "call Gabi")
        when: When to be reminded (e.g., "tomorrow at 10am", "next Friday 2pm")
        user_id: The ID of the user
        timezone: User's timezone (default: UTC)

    Returns:
        Confirmation message with calendar details

    Examples:
        >>> create_reminder("call Gabi", "tomorrow at 10am", "user123", "America/New_York")
        "✓ Reminder set: 'call Gabi' for Tuesday, October 28, 2025 at 10:00 AM"
    """
    try:
        # Parse the date/time from the 'when' parameter
        from utils.date_parser import parse_natural_language_date

        parsed_dt = parse_natural_language_date(when, timezone)

        if not parsed_dt:
            return f"❌ Couldn't understand the time '{when}'. Try formats like 'tomorrow at 10am' or 'next Friday 2pm'."

        # Check if date is in the past
        if is_date_in_past(parsed_dt):
            return f"❌ That time is in the past! Please specify a future date/time."

        # Create task in database with due_date
        task_id = task_repo.create_task(
            user_id=user_id,
            description=task,
            due_date=datetime_to_iso(parsed_dt),
            timezone=timezone
        )

        # Create calendar event
        calendar_event_id = create_calendar_event(
            summary=task,
            start_datetime=parsed_dt,
            description=f"Task reminder: {task}"
        )

        # If calendar creation succeeded, update task with event ID
        if calendar_event_id:
            task_repo.update_calendar_event_id(task_id, user_id, calendar_event_id)
            return (
                f"✓ Reminder set: '{task}' for {format_datetime_for_display(parsed_dt)}\n"
                f"📅 Added to your Google Calendar!"
            )
        else:
            # Calendar creation failed, but task was created
            return (
                f"✓ Task '{task}' added with reminder for {format_datetime_for_display(parsed_dt)}\n"
                f"⚠️ Couldn't add to Google Calendar. Check your calendar setup."
            )

    except FileNotFoundError as e:
        # Google Calendar credentials not set up
        return (
            f"✓ Task '{task}' added locally.\n"
            f"⚠️ Google Calendar not configured. See docs/GOOGLE_CALENDAR_SETUP.md"
        )
    except Exception as e:
        return f"❌ Error creating reminder: {str(e)}"


def add_task(task: str, user_id: str) -> str:
    """
    Add a new task to the to-do list.

    For simple tasks without a specific time.
    If the task includes a date/time, the agent should use create_reminder() instead.

    Args:
        task: The task description to add
        user_id: The ID of the user adding the task

    Returns:
        Confirmation message with the task ID
    """
    try:
        task_id = task_repo.create_task(user_id, task)
        return f"✓ Added task #{task_id}: '{task}'"
    except Exception as e:
        return f"❌ Error adding task: {str(e)}"


def list_tasks(user_id: str) -> str:
    """
    List all current (incomplete) tasks for the user.

    Args:
        user_id: The ID of the user

    Returns:
        String representation of all incomplete tasks
    """
    try:
        tasks = task_repo.get_user_tasks(user_id, done=False)

        if not tasks:
            return "You have no tasks! 🎉"

        task_list = "Your tasks:\n"
        for i, task in enumerate(tasks, 1):
            task_id, description, done, created_at, due_date, calendar_event_id, timezone = task
            # Show due date if available
            if due_date:
                task_list += f"{i}. {description} (Due: {due_date})\n"
            else:
                task_list += f"{i}. {description}\n"

        return task_list.strip()
    except Exception as e:
        return f"❌ Error listing tasks: {str(e)}"


def mark_task_done(task_number: int, user_id: str) -> str:
    """
    Mark a task as completed.

    Also deletes the associated Google Calendar event if one exists.

    Args:
        task_number: The number of the task to mark as done (1-indexed, from list_tasks)
        user_id: The ID of the user

    Returns:
        Confirmation message
    """
    try:
        # Get current tasks to find the actual task ID
        tasks = task_repo.get_user_tasks(user_id, done=False)

        if not tasks:
            return "❌ You have no tasks to mark as done."

        if task_number < 1 or task_number > len(tasks):
            return f"❌ Invalid task number. You have {len(tasks)} task(s). Please choose a number between 1 and {len(tasks)}."

        # Unpack all fields (7 fields: id, description, done, created_at, due_date, calendar_event_id, timezone)
        task_id = tasks[task_number - 1][0]
        task_description = tasks[task_number - 1][1]
        calendar_event_id = tasks[task_number - 1][5]  # Index 5 is calendar_event_id

        # Mark it as done in database
        success = task_repo.mark_task_done(task_id, user_id)

        if not success:
            return "❌ Failed to mark task as done."

        # If task has a calendar event, delete it
        calendar_deleted = False
        if calendar_event_id:
            try:
                calendar_deleted = delete_calendar_event(calendar_event_id)
            except Exception:
                # Calendar deletion failed, but task is marked done - that's OK
                pass

        # Build response message
        message = f"✓ Marked task #{task_number} as done: '{task_description}'"
        if calendar_deleted:
            message += "\n📅 Removed from Google Calendar"

        return message

    except Exception as e:
        return f"❌ Error marking task as done: {str(e)}"


def clear_all_tasks(user_id: str) -> str:
    """
    Clear all tasks for the user.

    Args:
        user_id: The ID of the user

    Returns:
        Confirmation message with count of deleted tasks
    """
    try:
        count = task_repo.clear_all_tasks(user_id)

        if count == 0:
            return "You had no tasks to clear."
        elif count == 1:
            return "✓ Cleared 1 task!"
        else:
            return f"✓ Cleared {count} tasks!"
    except Exception as e:
        return f"❌ Error clearing tasks: {str(e)}"
