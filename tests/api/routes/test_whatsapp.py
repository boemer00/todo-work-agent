"""Integration tests for WhatsApp webhook routes."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from slowapi import errors as slowapi_errors
from starlette.requests import Request

from api.routes import whatsapp


def _make_request(headers: List[Tuple[bytes, bytes]] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/whatsapp/webhook",
        "headers": headers or [],
        "query_string": b"",
        "client": ("test", 0),
        "server": ("test", 80),
        "scheme": "http",
    }

    async def receive() -> Dict[str, Any]:  # pragma: no cover - helper shim
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive=receive)


def test_verify_twilio_signature_skips_in_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_WEBHOOK_VERIFICATION", "true")
    request = _make_request()

    assert whatsapp.verify_twilio_signature(request, {"foo": "bar"}) is True


def test_verify_twilio_signature_requires_valid_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_WEBHOOK_VERIFICATION", "false")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret")

    # Missing signature header -> should reject
    request_missing = _make_request()
    assert whatsapp.verify_twilio_signature(request_missing, {}) is False

    # Invalid signature even when header is present -> still reject
    headers = [(b"x-twilio-signature", b"invalid")]
    request_invalid = _make_request(headers=headers)

    class DummyValidator:  # pragma: no cover - simple stub
        def __init__(self, token: str) -> None:
            self.token = token

        def validate(self, url: str, form: Dict[str, Any], signature: str) -> bool:
            assert signature == "invalid"
            return False

    monkeypatch.setattr(whatsapp, "RequestValidator", DummyValidator)

    assert whatsapp.verify_twilio_signature(request_invalid, {"Body": "hello"}) is False


def test_whatsapp_webhook_with_twilio_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_WEBHOOK_VERIFICATION", "false")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+987654321")

    async def fake_process_whatsapp_message(message: str, user_phone: str) -> str:
        assert message == "Hi"
        assert user_phone == "whatsapp:+1111111"
        return "Processed response"

    class DummyRedis:
        def __init__(self) -> None:
            self.expire_calls: list[tuple[str, int]] = []
            self.count = 0

        def incr(self, key: str) -> int:
            self.count += 1
            return self.count

        def expire(self, key: str, ttl: int) -> None:
            self.expire_calls.append((key, ttl))

    class DummyMessages:
        def __init__(self) -> None:
            self.calls: list[Dict[str, str]] = []

        def create(self, **kwargs: str) -> None:
            self.calls.append(kwargs)

    class DummyTwilio:
        def __init__(self) -> None:
            self.messages = DummyMessages()

    app = FastAPI()
    app.include_router(whatsapp.router, prefix="/whatsapp")
    app.state.redis_client = DummyRedis()
    app.state.twilio_client = DummyTwilio()

    monkeypatch.setattr(whatsapp, "verify_twilio_signature", lambda request, form: True)
    monkeypatch.setattr(whatsapp, "process_whatsapp_message", fake_process_whatsapp_message)

    async def _call_webhook() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/whatsapp/webhook",
                data={"From": "whatsapp:+1111111", "Body": "Hi"},
                headers={"X-Twilio-Signature": "valid"},
            )

    response = asyncio.run(_call_webhook())

    assert response.status_code == 200
    assert response.text == "OK"

    message_calls = app.state.twilio_client.messages.calls
    assert len(message_calls) == 2
    assert message_calls[0]["body"] == "Working on it."
    assert message_calls[1]["body"] == "Processed response"


def test_whatsapp_webhook_twiml_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_WEBHOOK_VERIFICATION", "false")

    async def fake_process_whatsapp_message(message: str, user_phone: str) -> str:
        return "Fallback response"

    app = FastAPI()
    app.include_router(whatsapp.router, prefix="/whatsapp")
    app.state.redis_client = None
    app.state.twilio_client = None

    monkeypatch.setattr(whatsapp, "verify_twilio_signature", lambda request, form: True)
    monkeypatch.setattr(whatsapp, "process_whatsapp_message", fake_process_whatsapp_message)

    async def _call_webhook() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/whatsapp/webhook",
                data={"From": "whatsapp:+2222222", "Body": "Hi"},
                headers={"X-Twilio-Signature": "valid"},
            )

    response = asyncio.run(_call_webhook())

    assert response.status_code == 200
    assert "<Response>" in response.text
    assert "Fallback response" in response.text


def test_whatsapp_webhook_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_WEBHOOK_VERIFICATION", "false")

    class RateLimitRedis:
        def incr(self, key: str) -> int:
            return 11

        def expire(self, key: str, ttl: int) -> None:  # pragma: no cover - no-op
            return None

    app = FastAPI()
    app.include_router(whatsapp.router, prefix="/whatsapp")
    app.state.redis_client = RateLimitRedis()
    app.state.twilio_client = None

    monkeypatch.setattr(whatsapp, "verify_twilio_signature", lambda request, form: True)
    monkeypatch.setattr(whatsapp, "process_whatsapp_message", AsyncMock(return_value="ignored"))

    class DummyRateLimitExceeded(whatsapp.HTTPException):
        def __init__(self, detail: str) -> None:
            super().__init__(status_code=429, detail=detail)

    monkeypatch.setattr(slowapi_errors, "RateLimitExceeded", DummyRateLimitExceeded)

    async def _call_webhook() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/whatsapp/webhook",
                data={"From": "whatsapp:+3333333", "Body": "Hi"},
                headers={"X-Twilio-Signature": "valid"},
            )

    response = asyncio.run(_call_webhook())

    assert response.status_code == 429


def test_verify_webhook_returns_status() -> None:
    app = FastAPI()
    app.include_router(whatsapp.router, prefix="/whatsapp")

    async def _call_verify() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/whatsapp/webhook")

    response = asyncio.run(_call_verify())

    assert response.status_code == 200
    assert response.json() == {
        "status": "webhook verified",
        "service": "ai-task-agent",
    }
