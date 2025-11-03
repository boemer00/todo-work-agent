"""
Pydantic schemas for tool input validation.

These schemas provide structured outputs for tool calling, ensuring type safety
and better LLM understanding of tool parameters.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreateReminderInput(BaseModel):
    """
    Input schema for creating a reminder with specific date/time.

    This tool should be used when the user specifies a date/time for their task.
    """
    task: str = Field(
        description="The task description to be reminded about (e.g., 'call mom', 'submit report')"
    )
    when: str = Field(
        description="Natural language date/time expression (e.g., 'tomorrow at 10am', 'next Friday 2pm')"
    )
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for the reminder (e.g., 'UTC', 'America/New_York')"
    )

    @field_validator('task')
    def task_not_empty(cls, v):
        """Ensure task description is not empty."""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()

    @field_validator('when')
    def when_not_empty(cls, v):
        """Ensure date/time is provided."""
        if not v or not v.strip():
            raise ValueError("Date/time cannot be empty")
        return v.strip()


class AddTaskInput(BaseModel):
    """
    Input schema for adding a simple task without specific time.

    Use this for quick tasks that don't need scheduling.
    """
    task: str = Field(
        description="The task description to add (e.g., 'buy milk', 'review code')"
    )
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )

    @field_validator('task')
    def task_not_empty(cls, v):
        """Ensure task description is not empty."""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()


class ListTasksInput(BaseModel):
    """
    Input schema for listing all incomplete tasks for a user.
    """
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )


class MarkTaskDoneInput(BaseModel):
    """
    Input schema for marking a task as completed.

    The task_number corresponds to the number shown in the task list.
    """
    task_number: int = Field(
        ge=1,
        description="The task number to mark as done (1-indexed, from list_tasks output)"
    )
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )

    @field_validator('task_number')
    def task_number_positive(cls, v):
        """Ensure task number is positive."""
        if v < 1:
            raise ValueError("Task number must be 1 or greater")
        return v


class ClearAllTasksInput(BaseModel):
    """
    Input schema for clearing all tasks for a user.

    Warning: This operation cannot be undone.
    """
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )


class ListCalendarEventsInput(BaseModel):
    """
    Input schema for listing Google Calendar events in a date range.

    Use this when the user asks about their schedule, calendar, or upcoming events.
    """
    time_min: str = Field(
        description="Start date in natural language (e.g., 'today', 'monday', 'this week')",
        examples=["today", "monday", "this week", "tomorrow"]
    )
    time_max: str = Field(
        description="End date in natural language (e.g., 'end of week', 'friday', 'next monday')",
        examples=["end of week", "friday", "sunday", "next monday"]
    )
    user_id: str = Field(
        description="User identifier (will be auto-injected from context)"
    )
    timezone: str = Field(
        default="UTC",
        description="User's timezone (e.g., 'America/New_York', 'Europe/London')"
    )
