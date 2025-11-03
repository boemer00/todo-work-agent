"""Tests for `tools.schemas` validation logic."""

import pytest

from tools import schemas


def test_create_reminder_input_strips_and_validates_fields() -> None:
    payload = schemas.CreateReminderInput(
        task="  call mom  ",
        when="  tomorrow at 9am  ",
    )

    assert payload.task == "call mom"
    assert payload.when == "tomorrow at 9am"
    assert payload.timezone == "UTC"


@pytest.mark.parametrize("field,value", [("task", ""), ("when", "   ")])
def test_create_reminder_input_rejects_empty_fields(field: str, value: str) -> None:
    data = {"task": "call", "when": "tomorrow"}
    data[field] = value

    with pytest.raises(ValueError):
        schemas.CreateReminderInput(**data)


def test_add_task_input_validation() -> None:
    payload = schemas.AddTaskInput(task="  buy milk  ")
    assert payload.task == "buy milk"

    with pytest.raises(ValueError):
        schemas.AddTaskInput(task="   ")


def test_mark_task_done_requires_positive_index() -> None:
    payload = schemas.MarkTaskDoneInput(task_number=2)
    assert payload.task_number == 2

    with pytest.raises(ValueError):
        schemas.MarkTaskDoneInput(task_number=0)


def test_list_tasks_input_no_required_fields() -> None:
    """ListTasksInput requires no fields - user_id is injected from state."""
    payload = schemas.ListTasksInput()
    assert payload is not None


def test_clear_all_tasks_input_no_required_fields() -> None:
    """ClearAllTasksInput requires no fields - user_id is injected from state."""
    payload = schemas.ClearAllTasksInput()
    assert payload is not None
