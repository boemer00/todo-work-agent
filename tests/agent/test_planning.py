"""Integration tests for plan-execute pattern."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent.nodes import planner_node, reflection_node, should_plan, should_reflect
from agent.state import State


class TestPlannerNode:
    """Tests for the planner_node function."""

    def test_planner_creates_plan_for_complex_request(self, monkeypatch):
        """Test that planner creates a plan for complex requests."""
        # Mock LLM response with a plan
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """Plan:
1. List all current tasks
2. Check which tasks have due dates
3. Prioritize tasks by deadline
4. Suggest a schedule"""
        mock_llm.invoke.return_value = mock_response

        def mock_get_llm_with_tools():
            return mock_llm

        monkeypatch.setattr("agent.nodes.get_llm_with_tools", mock_get_llm_with_tools)

        # Create state with complex request
        state: State = {
            "messages": [HumanMessage(content="organize my week")],
            "user_id": "test_user",
            "plan": None,
            "plan_step": 0
        }

        result = planner_node(state)

        # Should create a plan
        assert result["plan"] is not None
        assert "1." in result["plan"]
        assert "2." in result["plan"]
        assert result["plan_step"] == 0

        # Should add plan message
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], SystemMessage)
        assert "📋 Plan:" in result["messages"][0].content

    def test_planner_skips_simple_request(self, monkeypatch):
        """Test that planner returns NO_PLAN_NEEDED for simple requests."""
        # Mock LLM response indicating no plan needed
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "NO_PLAN_NEEDED"
        mock_llm.invoke.return_value = mock_response

        def mock_get_llm_with_tools():
            return mock_llm

        monkeypatch.setattr("agent.nodes.get_llm_with_tools", mock_get_llm_with_tools)

        # Create state with simple request
        state: State = {
            "messages": [HumanMessage(content="add milk")],
            "user_id": "test_user",
            "plan": None,
            "plan_step": 0
        }

        result = planner_node(state)

        # Should not create a plan
        assert result["plan"] is None
        assert result["plan_step"] == 0

    def test_planner_handles_errors_gracefully(self, monkeypatch):
        """Test that planner handles LLM errors without crashing."""
        # Mock LLM to raise an error
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("API Error")

        def mock_get_llm_with_tools():
            return mock_llm

        monkeypatch.setattr("agent.nodes.get_llm_with_tools", mock_get_llm_with_tools)

        state: State = {
            "messages": [HumanMessage(content="organize tasks")],
            "user_id": "test_user",
            "plan": None,
            "plan_step": 0
        }

        result = planner_node(state)

        # Should fallback to no plan
        assert result["plan"] is None
        assert result["plan_step"] == 0


class TestReflectionNode:
    """Tests for the reflection_node function."""

    def test_reflection_increments_step_after_tool_execution(self):
        """Test that reflection increments plan_step after tool execution."""
        from langchain_core.messages import ToolMessage

        state: State = {
            "messages": [
                HumanMessage(content="organize my week"),
                SystemMessage(content="Plan: 1. List tasks\n2. Prioritize\n3. Schedule"),
                ToolMessage(content="Task list here", tool_call_id="123")
            ],
            "user_id": "test_user",
            "plan": "Plan: 1. List tasks\n2. Prioritize\n3. Schedule",
            "plan_step": 0
        }

        result = reflection_node(state)

        # Should increment to next step
        assert result["plan_step"] == 1
        assert "Step 1 complete" in result["messages"][0].content

    def test_reflection_completes_plan_at_final_step(self):
        """Test that reflection marks plan complete at final step."""
        from langchain_core.messages import ToolMessage

        state: State = {
            "messages": [
                HumanMessage(content="organize tasks"),
                SystemMessage(content="Plan: 1. List\n2. Done"),
                ToolMessage(content="All done", tool_call_id="456")
            ],
            "user_id": "test_user",
            "plan": "Plan: 1. List\n2. Done",
            "plan_step": 1  # Already at step 1 (0-indexed), step 2 would be final
        }

        result = reflection_node(state)

        # Should clear plan
        assert result["plan"] is None
        assert result["plan_step"] == 0
        assert "Plan completed" in result["messages"][0].content

    def test_reflection_skips_if_no_plan(self):
        """Test that reflection does nothing if there's no plan."""
        state: State = {
            "messages": [HumanMessage(content="add task")],
            "user_id": "test_user",
            "plan": None,
            "plan_step": 0
        }

        result = reflection_node(state)

        # Should return empty dict (no updates)
        assert result == {}


class TestRoutingFunctions:
    """Tests for routing functions (should_plan, should_reflect)."""

    def test_should_plan_detects_complex_requests(self):
        """Test that should_plan routes complex requests to planner."""
        complex_keywords = [
            "organize my week",
            "plan tomorrow",
            "help me prepare for the meeting",
            "what should I do today",
            "prioritize my tasks"
        ]

        for message in complex_keywords:
            state: State = {
                "messages": [HumanMessage(content=message)],
                "user_id": "test_user",
                "plan": None,
                "plan_step": 0
            }

            result = should_plan(state)
            assert result == "planner", f"Failed for: {message}"

    def test_should_plan_bypasses_simple_requests(self):
        """Test that should_plan routes simple requests directly to agent."""
        simple_requests = [
            "add milk",
            "list tasks",
            "mark 1 done",
            "show my tasks",
            "delete all tasks"
        ]

        for message in simple_requests:
            state: State = {
                "messages": [HumanMessage(content=message)],
                "user_id": "test_user",
                "plan": None,
                "plan_step": 0
            }

            result = should_plan(state)
            assert result == "agent", f"Failed for: {message}"

    def test_should_reflect_routes_to_reflection_when_plan_active(self):
        """Test that should_reflect routes to reflection when following a plan."""
        state: State = {
            "messages": [HumanMessage(content="organize")],
            "user_id": "test_user",
            "plan": "1. Do this\n2. Do that",
            "plan_step": 0
        }

        result = should_reflect(state)
        assert result == "reflection"

    def test_should_reflect_routes_to_agent_when_no_plan(self):
        """Test that should_reflect routes to agent when not following a plan."""
        state: State = {
            "messages": [HumanMessage(content="add task")],
            "user_id": "test_user",
            "plan": None,
            "plan_step": 0
        }

        result = should_reflect(state)
        assert result == "agent"
