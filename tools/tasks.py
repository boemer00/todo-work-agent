"""
Task management tools for the LangGraph agent.

These are the functions the LLM can call to manage tasks.
All tools interact with the database through the TaskRepository.
"""

from database.models import TaskRepository

# Initialize the task repository (shared across all tool calls)
task_repo = TaskRepository()


def add_task(task: str, user_id: str) -> str:
    """
    Add a new task to the to-do list.

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
            task_id, description, done, created_at = task
            task_list += f"{i}. {description}\n"

        return task_list.strip()
    except Exception as e:
        return f"❌ Error listing tasks: {str(e)}"


def mark_task_done(task_number: int, user_id: str) -> str:
    """
    Mark a task as completed.

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

        # Get the actual task ID (0-indexed in list)
        task_id = tasks[task_number - 1][0]
        task_description = tasks[task_number - 1][1]

        # Mark it as done
        success = task_repo.mark_task_done(task_id, user_id)

        if success:
            return f"✓ Marked task #{task_number} as done: '{task_description}'"
        else:
            return "❌ Failed to mark task as done."
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
