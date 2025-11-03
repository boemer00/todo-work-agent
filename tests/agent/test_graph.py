"""Tests for `agent.graph` construction."""

from __future__ import annotations

from typing import Any

import pytest
import sqlite3

from agent import graph


def test_create_graph_compiles_with_checkpointing(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_conn_queries: list[str] = []

    class DummyConnection:
        def execute(self, sql: str) -> None:
            dummy_conn_queries.append(sql)

    class DummySaver:
        def __init__(self, conn: Any) -> None:
            self.conn = conn

    class DummyBuilder:
        def __init__(self, state_cls: Any) -> None:
            self.state_cls = state_cls
            self.nodes: dict[str, Any] = {}
            self.edges: list[tuple[Any, Any]] = []
            self.conditionals: list[tuple[str, Any, dict[str, Any]]] = []  # Store all conditionals
            self.compiled_with: Any = None

        def add_node(self, name: str, func: Any) -> None:
            self.nodes[name] = func

        def add_edge(self, src: Any, dest: Any) -> None:
            self.edges.append((src, dest))

        def add_conditional_edges(self, name: str, condition: Any, mapping: dict[str, Any]) -> None:
            self.conditionals.append((name, condition, mapping))

        def compile(self, checkpointer: Any) -> str:
            self.compiled_with = checkpointer
            return "compiled-graph"

    builder_holder: dict[str, DummyBuilder] = {}

    def fake_state_graph(state_cls: Any) -> DummyBuilder:
        builder = DummyBuilder(state_cls)
        builder_holder["builder"] = builder
        return builder

    monkeypatch.setattr(graph, "StateGraph", fake_state_graph)
    monkeypatch.setattr(graph, "SqliteSaver", DummySaver)
    monkeypatch.setattr(graph, "tool_node_with_state_injection", "TOOL")
    monkeypatch.setattr(graph, "get_db_path", lambda db_name: f"/tmp/{db_name}")

    dummy_connection = DummyConnection()
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: dummy_connection)

    compiled = graph.create_graph()
    builder = builder_holder["builder"]

    assert compiled == "compiled-graph"
    assert dummy_conn_queries[-1] == "PRAGMA journal_mode=WAL"

    # Check all nodes exist (including new planning nodes)
    assert builder.nodes["agent"] is graph.agent_node
    assert builder.nodes["tools"] == "TOOL"
    assert "planner" in builder.nodes
    assert "reflection" in builder.nodes

    # Check edges (now includes planner → agent and reflection → agent)
    assert any(dest == "agent" for _src, dest in builder.edges)
    assert ("planner", "agent") in builder.edges
    assert ("reflection", "agent") in builder.edges

    # The old direct "tools → agent" edge is now conditional through should_reflect
    # So we don't check for it anymore

    # Check that we have multiple conditional edges (START, agent, tools)
    assert len(builder.conditionals) >= 3
    conditional_nodes = [cond[0] for cond in builder.conditionals]
    assert "agent" in conditional_nodes  # Agent decides tools/end
    assert "tools" in conditional_nodes  # Tools route to reflection/agent

    # Check that agent conditional uses should_continue
    agent_conditionals = [cond for cond in builder.conditionals if cond[0] == "agent"]
    assert len(agent_conditionals) > 0
    assert agent_conditionals[0][1] is graph.should_continue

    assert builder.compiled_with.conn is dummy_connection
