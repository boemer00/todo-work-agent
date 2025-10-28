"""Pydantic schemas for WhatsApp messages."""

from pydantic import BaseModel
from typing import Optional


class WhatsAppMessage(BaseModel):
    """WhatsApp message from Twilio."""
    Body: str
    From: str
    To: Optional[str] = None
    MessageSid: Optional[str] = None


class WhatsAppResponse(BaseModel):
    """Response to send back to WhatsApp user."""
    message: str
    status: str = "success"
