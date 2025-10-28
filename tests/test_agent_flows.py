"""
Integration tests for agent flows.

Tests end-to-end behavior of the agent with mocked LLM responses.
"""

import pytest
from unittest.mock import Mock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.graph import create_graph
from agent.nodes import should_continue
from agent.state import State


@pytest.mark.integration
class TestAgentFlows:
    """Test suite for agent conversation flows."""

    def test_agent_routing_to_tools(self, sample_state):
        """Test that agent correctly routes to tools node."""
        # Create a state where last message has tool calls
        mock_ai_message = Mock(spec=AIMessage)
        mock_ai_message.content = ""
        mock_ai_message.tool_calls = [
            {"name": "add_task", "args": {"task": "buy milk"}, "id": "call_1"}
        ]

        state = State(
            messages=[HumanMessage(content="add buy milk"), mock_ai_message],
            user_id="test_user"
        )

        # Test routing decision
        next_node = should_continue(state)
        assert next_node == "tools"

    def test_agent_routing_to_end(self, sample_state):
        """Test that agent correctly routes to END."""
        # Create a state where last message has no tool calls
        mock_ai_message = Mock(spec=AIMessage)
        mock_ai_message.content = "Task added successfully!"
        mock_ai_message.tool_calls = []

        state = State(
            messages=[HumanMessage(content="thanks"), mock_ai_message],
            user_id="test_user"
        )

        # Test routing decision
        next_node = should_continue(state)
        assert next_node == "end"

    def test_agent_add_task_flow(self, task_repo, test_user_id, mocker):
        """Test tool execution flow for adding a task."""
        # Patch the task repository
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Import and directly call the add_task tool (simulating what agent would do)
        from tools.tasks import add_task

        result = add_task(task="buy groceries", user_id=test_user_id)

        # Verify task was created
        assert "✓" in result or "Added" in result
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1
        assert tasks[0][1] == "buy groceries"

    def test_agent_list_tasks_flow(self, task_repo, test_user_id, mocker):
        """Test tool execution flow for listing tasks."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Pre-create some tasks
        task_repo.create_task(test_user_id, "Task 1")
        task_repo.create_task(test_user_id, "Task 2")

        # Import and directly call the list_tasks tool
        from tools.tasks import list_tasks

        result = list_tasks(user_id=test_user_id)

        # Verify both tasks appear in result
        assert "Task 1" in result
        assert "Task 2" in result

    def test_agent_multi_turn_conversation(self, task_repo, test_user_id, mocker):
        """Test multi-turn workflow: add task then mark it done."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        from tools.tasks import add_task, mark_task_done

        # Turn 1: Add a task
        result1 = add_task(task="buy milk", user_id=test_user_id)
        assert "✓" in result1

        # Verify task was created
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1

        # Turn 2: Mark it done
        result2 = mark_task_done(task_number=1, user_id=test_user_id)
        assert "✓" in result2

        # Verify task was marked done
        incomplete_tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(incomplete_tasks) == 0

        completed_tasks = task_repo.get_user_tasks(test_user_id, done=True)
        assert len(completed_tasks) == 1

    def test_agent_handles_no_tool_needed(self):
        """Test routing logic when no tools are called."""
        # Create a state where the agent responds without tool calls
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "Hello! I'm here to help you manage your tasks."
        mock_response.tool_calls = []

        state = State(
            messages=[HumanMessage(content="hello"), mock_response],
            user_id="test_user"
        )

        # Test that should_continue routes to "end" when no tool calls
        next_node = should_continue(state)
        assert next_node == "end"

    def test_agent_state_contains_user_id(self, sample_state):
        """Test that state always contains user_id."""
        assert "user_id" in sample_state
        assert sample_state["user_id"] is not None
        assert isinstance(sample_state["user_id"], str)

    def test_agent_preserves_message_history(self, test_user_id):
        """Test that state preserves conversation history."""
        # Create a state with message history
        state = State(
            messages=[
                HumanMessage(content="First message"),
                AIMessage(content="First response"),
                HumanMessage(content="Second message")
            ],
            user_id=test_user_id
        )

        # Verify all messages are preserved
        assert len(state["messages"]) == 3
        assert state["messages"][0].content == "First message"
        assert state["messages"][1].content == "First response"
        assert state["messages"][2].content == "Second message"
