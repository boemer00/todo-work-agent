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

    def test_agent_add_task_flow(self, task_repo, test_user_id, mocker, mock_openai_response):
        """Test complete flow for adding a task."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Mock LLM to call add_task tool
        mock_tool_call_message = Mock(spec=AIMessage)
        mock_tool_call_message.content = ""
        mock_tool_call_message.tool_calls = [
            {
                "name": "add_task",
                "args": {"task": "buy groceries", "user_id": test_user_id},
                "id": "call_123"
            }
        ]

        # Mock final response after tool execution
        mock_final_response = Mock(spec=AIMessage)
        mock_final_response.content = "✓ Added task: 'buy groceries'"
        mock_final_response.tool_calls = []

        # Configure mock to return different responses on subsequent calls
        mock_openai_response.side_effect = [
            mock_tool_call_message,  # First call: decide to use tool
            mock_final_response       # Second call: final response
        ]

        # Create and run graph
        graph = create_graph()
        initial_state = State(
            messages=[HumanMessage(content="add buy groceries to my list")],
            user_id=test_user_id
        )

        config = {"configurable": {"thread_id": "test_thread"}}
        final_state = graph.invoke(initial_state, config)

        # Verify task was created
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1
        assert tasks[0][1] == "buy groceries"

    def test_agent_list_tasks_flow(self, task_repo, test_user_id, mocker, mock_openai_response):
        """Test complete flow for listing tasks."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Pre-create some tasks
        task_repo.create_task(test_user_id, "Task 1")
        task_repo.create_task(test_user_id, "Task 2")

        # Mock LLM to call list_tasks tool
        mock_tool_call_message = Mock(spec=AIMessage)
        mock_tool_call_message.content = ""
        mock_tool_call_message.tool_calls = [
            {
                "name": "list_tasks",
                "args": {"user_id": test_user_id},
                "id": "call_456"
            }
        ]

        mock_final_response = Mock(spec=AIMessage)
        mock_final_response.content = "Here are your tasks: 1. Task 1\n2. Task 2"
        mock_final_response.tool_calls = []

        mock_openai_response.side_effect = [
            mock_tool_call_message,
            mock_final_response
        ]

        graph = create_graph()
        initial_state = State(
            messages=[HumanMessage(content="show my tasks")],
            user_id=test_user_id
        )

        config = {"configurable": {"thread_id": "test_thread_2"}}
        final_state = graph.invoke(initial_state, config)

        # Verify we have messages in final state
        assert len(final_state["messages"]) > 1

    def test_agent_multi_turn_conversation(
        self, task_repo, test_user_id, mocker, mock_openai_response
    ):
        """Test multi-turn conversation with state persistence."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        graph = create_graph()
        config = {"configurable": {"thread_id": "test_thread_multi"}}

        # Turn 1: Add a task
        mock_add_tool_call = Mock(spec=AIMessage)
        mock_add_tool_call.content = ""
        mock_add_tool_call.tool_calls = [
            {
                "name": "add_task",
                "args": {"task": "buy milk", "user_id": test_user_id},
                "id": "call_1"
            }
        ]

        mock_add_response = Mock(spec=AIMessage)
        mock_add_response.content = "✓ Task added!"
        mock_add_response.tool_calls = []

        mock_openai_response.side_effect = [mock_add_tool_call, mock_add_response]

        state = State(
            messages=[HumanMessage(content="add buy milk")],
            user_id=test_user_id
        )

        # Invoke first turn
        state = graph.invoke(state, config)

        # Verify task was created
        tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(tasks) == 1

        # Turn 2: Mark it done
        mock_done_tool_call = Mock(spec=AIMessage)
        mock_done_tool_call.content = ""
        mock_done_tool_call.tool_calls = [
            {
                "name": "mark_task_done",
                "args": {"task_number": 1, "user_id": test_user_id},
                "id": "call_2"
            }
        ]

        mock_done_response = Mock(spec=AIMessage)
        mock_done_response.content = "✓ Task marked as done!"
        mock_done_response.tool_calls = []

        mock_openai_response.side_effect = [mock_done_tool_call, mock_done_response]

        state["messages"].append(HumanMessage(content="mark task 1 as done"))

        # Invoke second turn
        final_state = graph.invoke(state, config)

        # Verify task was marked done
        incomplete_tasks = task_repo.get_user_tasks(test_user_id, done=False)
        assert len(incomplete_tasks) == 0

        completed_tasks = task_repo.get_user_tasks(test_user_id, done=True)
        assert len(completed_tasks) == 1

    def test_agent_handles_no_tool_needed(self, mock_openai_response):
        """Test agent handling conversational messages without tool calls."""
        # Mock LLM response without tool calls
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "Hello! I'm here to help you manage your tasks."
        mock_response.tool_calls = []

        mock_openai_response.return_value = mock_response

        graph = create_graph()
        state = State(
            messages=[HumanMessage(content="hello")],
            user_id="test_user"
        )

        config = {"configurable": {"thread_id": "test_thread_hello"}}
        final_state = graph.invoke(state, config)

        # Verify no errors and response is present
        assert len(final_state["messages"]) >= 2
        last_message = final_state["messages"][-1]
        assert hasattr(last_message, "content")

    def test_agent_state_contains_user_id(self, sample_state):
        """Test that state always contains user_id."""
        assert "user_id" in sample_state
        assert sample_state["user_id"] is not None
        assert isinstance(sample_state["user_id"], str)

    def test_agent_preserves_message_history(
        self, task_repo, test_user_id, mocker, mock_openai_response
    ):
        """Test that agent preserves conversation history in state."""
        mocker.patch('tools.tasks.task_repo', task_repo)

        # Mock simple response
        mock_response = Mock(spec=AIMessage)
        mock_response.content = "I'll help with that."
        mock_response.tool_calls = []
        mock_openai_response.return_value = mock_response

        graph = create_graph()
        state = State(
            messages=[
                HumanMessage(content="First message"),
                AIMessage(content="First response"),
                HumanMessage(content="Second message")
            ],
            user_id=test_user_id
        )

        config = {"configurable": {"thread_id": "test_thread_history"}}
        final_state = graph.invoke(state, config)

        # Verify history is preserved and new message added
        assert len(final_state["messages"]) >= 4  # Original 3 + at least 1 new
