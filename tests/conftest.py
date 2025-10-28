"""
Pytest configuration and shared fixtures for testing.

Provides reusable test fixtures for database, mocks, and test data.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from database.models import TaskRepository
from agent.state import State


@pytest.fixture
def test_user_id():
    """Provide a consistent test user ID."""
    return "test_user_123"


@pytest.fixture
def test_db_path():
    """Create a temporary database file for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    yield path

    # Cleanup after test
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def task_repo(test_db_path):
    """
    Provide a TaskRepository with an isolated test database.

    Uses a temporary SQLite database that's cleaned up after each test.
    """
    repo = TaskRepository(db_path=test_db_path)
    return repo


@pytest.fixture
def sample_tasks():
    """Provide sample task data for testing."""
    return [
        {"description": "Buy groceries", "user_id": "test_user_123"},
        {"description": "Call dentist", "user_id": "test_user_123"},
        {"description": "Finish report", "user_id": "test_user_123"},
    ]


@pytest.fixture
def mock_llm_response():
    """
    Provide a mock LLM response with tool calls.

    Useful for testing agent behavior without making real LLM calls.
    """
    def _create_response(tool_name: str, tool_args: dict):
        """Create a mock AIMessage with tool calls."""
        mock_msg = Mock(spec=AIMessage)
        mock_msg.content = ""
        mock_msg.tool_calls = [
            {
                "name": tool_name,
                "args": tool_args,
                "id": "test_call_123"
            }
        ]
        return mock_msg

    return _create_response


@pytest.fixture
def mock_google_calendar(mocker):
    """
    Mock Google Calendar API to avoid external API calls during tests.

    Returns a mock that simulates successful calendar event creation.
    """
    # Mock where the functions are USED, not where they're defined
    mock_create = mocker.patch('tools.tasks.create_calendar_event')
    mock_create.return_value = "mock_event_id_123"

    # Mock the delete_calendar_event function
    mock_delete = mocker.patch('tools.tasks.delete_calendar_event')
    mock_delete.return_value = True

    return {
        'create': mock_create,
        'delete': mock_delete
    }


@pytest.fixture
def sample_state(test_user_id):
    """
    Provide a sample State object for testing agent flows.

    Contains a basic conversation with user message.
    """
    return State(
        messages=[
            HumanMessage(content="add buy milk to my list")
        ],
        user_id=test_user_id
    )


@pytest.fixture
def mock_datetime():
    """
    Provide a consistent datetime for testing time-dependent functionality.

    Returns: datetime object for 2025-01-15 10:00:00 UTC
    """
    return datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test.

    Ensures tests don't interfere with each other via environment state.
    """
    # Store original env vars
    original_env = os.environ.copy()

    yield

    # Restore original env vars after test
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai_response(mocker):
    """
    Mock OpenAI API responses to avoid real API calls and costs.

    Returns a mock that can be configured per test.
    """
    mock_response = mocker.patch('langchain_openai.ChatOpenAI.invoke')

    # Default response (can be overridden in tests)
    default_message = Mock(spec=AIMessage)
    default_message.content = "Task added successfully!"
    default_message.tool_calls = []
    mock_response.return_value = default_message

    return mock_response
