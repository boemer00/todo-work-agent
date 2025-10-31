"""Unit tests for WhatsApp message handler service."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from api.services import message_handler


def test_process_whatsapp_message_first_interaction(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_agent_sync(message: str, user_id: str, user_phone: str) -> Dict[str, Any]:
        assert message == "Hello"
        assert user_phone == "whatsapp:+123"
        assert len(user_id) == 16
        return {
            "messages": [
                SimpleNamespace(role="user", content=message),
                SimpleNamespace(role="assistant", content="Response body"),
            ]
        }

    monkeypatch.setattr(message_handler, "_run_agent_sync", fake_run_agent_sync)

    response = asyncio.run(message_handler.process_whatsapp_message("Hello", "whatsapp:+123"))

    assert response.startswith("👋 Hi! I'm your task assistant.")
    assert "Response body" in response


def test_process_whatsapp_message_subsequent_interaction(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_agent_sync(message: str, user_id: str, user_phone: str) -> Dict[str, Any]:
        return {
            "messages": [
                SimpleNamespace(role="user", content=message),
                SimpleNamespace(role="assistant", content="Previous"),
                SimpleNamespace(role="user", content="Follow up"),
                SimpleNamespace(role="assistant", content="1. Task A\n2. Task B"),
            ]
        }

    monkeypatch.setattr(message_handler, "_run_agent_sync", fake_run_agent_sync)

    response = asyncio.run(message_handler.process_whatsapp_message("Hello", "whatsapp:+999"))

    assert not response.startswith("👋")
    assert response.count("*1.*") == 1
    assert "Task B" in response


def test_process_whatsapp_message_handles_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_run_agent_sync(message: str, user_id: str, user_phone: str) -> Dict[str, Any]:
        raise RuntimeError("boom")

    monkeypatch.setattr(message_handler, "_run_agent_sync", failing_run_agent_sync)

    response = asyncio.run(message_handler.process_whatsapp_message("Hello", "whatsapp:+000"))

    assert "Something went wrong" in response


def test_format_for_whatsapp_applies_number_formatting() -> None:
    source = "1. First task\n\n2. Second task\n\nAdditional text"
    expected = "*1.* First task\n\n*2.* Second task\n\nAdditional text"

    assert message_handler.format_for_whatsapp(source) == expected
