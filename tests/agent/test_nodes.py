"""Tests for `agent.nodes` behaviors."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent import nodes


def test_should_continue_routes_tool_calls() -> None:
    state = {
        "messages": [
            AIMessage(content="hi", tool_calls=[{"id": "call-1", "name": "tool", "args": {}}])
        ],
        "user_id": "user",
    }

    assert nodes.should_continue(state) == "tools"


def test_should_continue_routes_to_end_without_tool_calls() -> None:
    state = {"messages": [AIMessage(content="hi", tool_calls=[])]}

    assert nodes.should_continue(state) == "end"


def test_agent_node_success_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_messages = {}

    class FakeLLM:
        def invoke(self, messages):
            captured_messages["sent"] = messages
            return AIMessage(content="Done")

    monkeypatch.setattr(nodes, "get_llm_with_tools", lambda: FakeLLM())

    state = {"messages": [HumanMessage(content="Hello")], "user_id": "user"}
    result = nodes.agent_node(state)

    assert isinstance(result["messages"][0], AIMessage)
    assert captured_messages["sent"][0].__class__ is SystemMessage


def test_agent_node_transient_errors_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeRateLimitError(Exception):
        pass

    class FakeLLM:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            raise FakeRateLimitError("rate limit")

    llm = FakeLLM()
    monkeypatch.setattr(nodes, "get_llm_with_tools", lambda: llm)
    monkeypatch.setattr(nodes, "RateLimitError", FakeRateLimitError)
    monkeypatch.setattr(nodes.time, "sleep", lambda _seconds: None)

    state = {"messages": [HumanMessage(content="Hi")], "user_id": "user"}
    result = nodes.agent_node(state)

    assert llm.calls == 3
    assert "trouble connecting to my brain" in result["messages"][0].content


def test_agent_node_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAuthError(Exception):
        pass

    class FakeLLM:
        def invoke(self, messages):
            raise FakeAuthError("bad key")

    monkeypatch.setattr(nodes, "get_llm_with_tools", lambda: FakeLLM())
    monkeypatch.setattr(nodes, "AuthenticationError", FakeAuthError)

    state = {"messages": [HumanMessage(content="Hi")], "user_id": "user"}
    result = nodes.agent_node(state)

    assert "authentication issue" in result["messages"][0].content


def test_agent_node_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLLM:
        def invoke(self, messages):
            raise ValueError("boom")

    monkeypatch.setattr(nodes, "get_llm_with_tools", lambda: FakeLLM())

    state = {"messages": [HumanMessage(content="Hi")], "user_id": "user"}
    result = nodes.agent_node(state)

    assert "unexpected error" in result["messages"][0].content
