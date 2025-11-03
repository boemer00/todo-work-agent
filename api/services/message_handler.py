"""Message handler service for processing WhatsApp messages."""

import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from agent.graph import create_graph

# Thread pool for running sync agent code
executor = ThreadPoolExecutor(max_workers=4)


async def process_whatsapp_message(message: str, user_phone: str) -> str:
    """
    Process incoming WhatsApp message through LangGraph agent.

    Args:
        message: The text message from the user
        user_phone: The user's phone number (e.g., "whatsapp:+1234567890")

    Returns:
        str: Response message to send back to user
    """
    try:
        # Generate consistent user_id from phone number
        # Hash the phone number to create a unique but consistent ID
        user_id = hashlib.sha256(user_phone.encode()).hexdigest()[:16]

        # Run the synchronous graph in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            _run_agent_sync,
            message,
            user_id,
            user_phone
        )

        # Extract response from last message
        last_message = result["messages"][-1]
        response = last_message.content

        # Check if this is the very first interaction by checking message history length
        # If there are only 2 messages (user input + agent response), it's the first message ever
        is_first_message = len(result["messages"]) <= 2

        # Prepend welcome message ONLY on the very first interaction
        if is_first_message:
            welcome = (
                "👋 Hi! I'm your task assistant.\n\n"
                "I can help you:\n"
                "• Add tasks with natural dates (\"remind me tomorrow at 10am to call John\")\n"
                "• Show your tasks (\"show my tasks\")\n"
                "• Mark tasks as done (\"mark task 1 as done\")\n\n"
            )
            response = welcome + response

        # Format response for WhatsApp
        return format_for_whatsapp(response)

    except Exception as e:
        # Log the full error for debugging (will appear in Cloud Run logs)
        import logging
        logging.error(f"Error processing message from {user_phone}: {str(e)}", exc_info=True)

        # Return sanitized user-friendly error message (never expose exceptions)
        return "❌ Something went wrong. Please try again or rephrase your message."


def _run_agent_sync(message: str, user_id: str, user_phone: str) -> Dict[str, Any]:
    """
    Run the agent synchronously in a thread pool.

    This is a helper function that wraps the sync graph invocation
    so it can be run via run_in_executor.

    Args:
        message: The user's message
        user_id: The hashed user ID
        user_phone: The user's phone number for thread_id

    Returns:
        dict: The agent's result state
    """
    # Create agent graph
    graph = create_graph()

    # Prepare input state
    state = {
        "messages": [HumanMessage(content=message)],
        "user_id": user_id,
        "plan_step": 0
    }

    # Configure with thread_id for conversation memory
    config = {"configurable": {"thread_id": user_phone}}

    # Run agent (synchronously)
    result = graph.invoke(state, config)

    return result


def format_for_whatsapp(text: str) -> str:
    """
    Format text for WhatsApp with rich formatting.

    Args:
        text: Plain text response

    Returns:
        str: Formatted text with WhatsApp markdown

    Note: WhatsApp formatting is very strict:
    - Needs whitespace or newlines before/after markers
    - Breaks with adjacent punctuation
    - We keep formatting minimal to avoid rendering issues
    """
    import re

    # WhatsApp supports:
    # *bold* for bold text
    # _italic_ for italic text
    # ~strikethrough~ for strikethrough
    # ```code``` for monospace

    # KEEP IT SIMPLE: Only format task numbers at start of line
    # This is safe because we control the whitespace
    # Pattern: "1. Task name" -> "*1.* Task name"
    text = re.sub(r'^(\d+)\.\s', r'*\1.* ', text, flags=re.MULTILINE)

    # Don't format "Due:" dates - too fragile with parentheses and punctuation
    # The relative dates (Today, Tomorrow) are already human-readable

    # Ensure clean line breaks (remove excessive whitespace but preserve structure)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
