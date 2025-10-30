"""WhatsApp webhook endpoints."""

import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from api.services.message_handler import process_whatsapp_message

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_twilio_signature(request: Request, form_data: dict) -> bool:
    """
    Verify Twilio webhook signature for security.

    Prevents unauthorized requests from triggering the webhook.
    Uses Twilio's official RequestValidator to verify HMAC-SHA1 signature.

    Args:
        request: FastAPI request object containing headers and URL
        form_data: Dictionary of form parameters sent by Twilio

    Returns:
        True if signature is valid or verification is skipped (dev mode)
        False if signature is invalid or auth token is missing
    """
    # Allow bypassing in local development (must be explicitly enabled)
    if os.getenv("SKIP_WEBHOOK_VERIFICATION", "false").lower() == "true":
        logger.warning("⚠️  Webhook verification SKIPPED (development mode)")
        return True

    # Get auth token from environment
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token:
        logger.error("TWILIO_AUTH_TOKEN not set - cannot verify webhook")
        return False

    # Get signature from header
    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Missing X-Twilio-Signature header")
        return False

    # Get full URL (Twilio signs the complete URL)
    url = str(request.url)

    # Verify using Twilio's official validator
    validator = RequestValidator(auth_token)
    is_valid = validator.validate(url, form_data, signature)

    if not is_valid:
        logger.warning(f"Invalid Twilio signature for URL: {url}")

    return is_valid


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Receives messages from Twilio WhatsApp.

    Security: Verifies Twilio signature to prevent unauthorized access.

    Args:
        request: FastAPI request containing form data from Twilio

    Returns:
        Response: TwiML XML response for Twilio

    Raises:
        HTTPException: 403 if Twilio signature verification fails
    """
    # Parse form data from Twilio
    form_data = await request.form()
    form_dict = dict(form_data)  # Convert to dict for validator

    # Verify Twilio signature for security
    if not verify_twilio_signature(request, form_dict):
        logger.error("Webhook request rejected: invalid signature")
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing Twilio signature"
        )

    # Extract message data
    incoming_msg = str(form_data.get("Body", ""))
    from_number = str(form_data.get("From", ""))

    logger.info(f"Processing message from {from_number}")

    # Process message through agent
    response_text = await process_whatsapp_message(
        message=incoming_msg,
        user_phone=from_number
    )

    # Create Twilio response
    resp = MessagingResponse()
    resp.message(response_text)

    return Response(content=str(resp), media_type="application/xml")


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint.

    Used by Twilio to verify the webhook URL is accessible.

    Returns:
        dict: Verification status
    """
    return {
        "status": "webhook verified",
        "service": "ai-task-agent"
    }
