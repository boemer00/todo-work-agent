"""WhatsApp webhook endpoints."""

from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse

from api.services.message_handler import process_whatsapp_message

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Receives messages from Twilio WhatsApp.

    Args:
        request: FastAPI request containing form data from Twilio

    Returns:
        Response: TwiML XML response for Twilio
    """
    # Parse form data from Twilio
    form_data = await request.form()

    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")

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
