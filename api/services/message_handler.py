"""Message handler service for processing WhatsApp messages."""

import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
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

        # Format response for WhatsApp
        return format_for_whatsapp(last_message.content)

    except Exception as e:
        # Return user-friendly error message
        return f"❌ Oops! Something went wrong: {str(e)}\n\nPlease try again or type 'help' for assistance."


def _run_agent_sync(message: str, user_id: str, user_phone: str) -> dict:
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
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id
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
    """
    # WhatsApp supports:
    # *bold* for bold text
    # _italic_ for italic text
    # ~strikethrough~ for strikethrough
    # ```code``` for monospace

    # For now, return as-is
    # Can enhance later with emojis and formatting
    return text
