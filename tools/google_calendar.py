"""
Google Calendar integration for the to-do agent.

Handles OAuth 2.0 authentication and calendar event creation.

Setup Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as 'credentials.json' in project root
6. Run the agent - it will open browser for first-time auth
7. Token saved to 'token.json' (auto-refresh handled)

Security:
- credentials.json and token.json are in .gitignore
- Tokens stored locally, never committed to git
- OAuth 2.0 with refresh tokens for long-term access
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API scopes
# Using calendar.events scope for read/write access to events
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Paths for credentials and token
CREDENTIALS_PATH = 'credentials.json'
TOKEN_PATH = 'token.json'


def get_calendar_service() -> Any:
    """
    Get authenticated Google Calendar service.

    Handles the complete OAuth 2.0 flow:
    1. Check if token.json exists (previous auth)
    2. If exists and valid, use it
    3. If expired, refresh it
    4. If no token, run OAuth flow (opens browser)
    5. Save token for future use

    Returns:
        Authenticated Google Calendar service object

    Raises:
        FileNotFoundError: If credentials.json not found
        Exception: If authentication fails

    Interview Notes:
    - OAuth 2.0 authorization code flow for desktop apps
    - Token persistence prevents re-auth on every run
    - Automatic token refresh using refresh_token
    - Scope limitation (calendar.events only, not full calendar access)
    """
    creds = None

    # Check if we have a saved token from previous auth
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expired but we have refresh token - refresh it
            creds.refresh(Request())
        else:
            # No valid creds - run OAuth flow (opens browser)
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"\n❌ {CREDENTIALS_PATH} not found!\n\n"
                    "Setup Instructions:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create project & enable Google Calendar API\n"
                    "3. Create OAuth 2.0 credentials (Desktop app)\n"
                    "4. Download as 'credentials.json' in project root\n"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            # Run local server for OAuth callback
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    # Build and return the service
    service = build('calendar', 'v3', credentials=creds)
    return service


def create_calendar_event(
    summary: str,
    start_datetime: datetime,
    duration_minutes: int = 30,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> Optional[str]:
    """
    Create a Google Calendar event.

    Args:
        summary: Event title (e.g., "Call Gabi")
        start_datetime: When the event starts (timezone-aware datetime)
        duration_minutes: How long the event lasts (default: 30 minutes)
        description: Optional event description
        location: Optional event location

    Returns:
        Google Calendar event ID on success, None on failure

    Interview Notes:
    - Uses RFC3339 format for datetime (ISO 8601 compliant)
    - Handles timezone-aware datetimes correctly
    - Idempotency: returns event ID to prevent duplicates
    - Error handling: catches HttpError for API failures
    - Rate limiting: Google Calendar has 1M queries/day quota
    """
    try:
        service = get_calendar_service()

        # Calculate end time
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        # Get timezone name (handle both pytz and zoneinfo)
        def get_timezone_name(dt: datetime) -> str:
            """Extract timezone name from datetime object."""
            if dt.tzinfo is None:
                return 'UTC'
            # Try to get zone attribute (works for some timezone objects)
            if hasattr(dt.tzinfo, 'zone'):
                return dt.tzinfo.zone
            # Fallback: use tzname() method (works for pytz StaticTzInfo)
            tzname = dt.tzinfo.tzname(dt)
            if tzname:
                return tzname
            # Last resort
            return 'UTC'

        # Build event object (Google Calendar API format)
        event = {
            'summary': summary,
            'description': description or f'Reminder: {summary}',
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': get_timezone_name(start_datetime),
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': get_timezone_name(end_datetime),
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},  # 10 min before popup
                ],
            },
        }

        # Add location if provided
        if location:
            event['location'] = location

        # Create the event (using 'primary' calendar)
        result = service.events().insert(calendarId='primary', body=event).execute()

        # Return the event ID (for tracking/syncing)
        return result.get('id')

    except FileNotFoundError as e:
        # Credentials not set up
        raise e

    except HttpError as e:
        # Google API error (rate limit, network, etc.)
        error_msg = f"Google Calendar API error: {e}"
        print(f"❌ {error_msg}")
        return None

    except Exception as e:
        # Other errors (serialization, network, etc.)
        print(f"❌ Error creating calendar event: {str(e)}")
        return None


def delete_calendar_event(event_id: str) -> bool:
    """
    Delete a Google Calendar event by ID.

    Args:
        event_id: The Google Calendar event ID

    Returns:
        True if deleted successfully, False otherwise

    Interview Notes:
    - Used for syncing when task is marked done or deleted
    - Idempotent: deleting already-deleted event returns success
    - Graceful failure: doesn't crash if event not found
    """
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True

    except HttpError as e:
        if e.resp.status == 404:
            # Event already deleted or doesn't exist
            return True
        print(f"❌ Error deleting calendar event: {e}")
        return False

    except Exception as e:
        print(f"❌ Error deleting calendar event: {str(e)}")
        return False


def update_calendar_event(
    event_id: str,
    summary: Optional[str] = None,
    start_datetime: Optional[datetime] = None,
    description: Optional[str] = None
) -> bool:
    """
    Update an existing Google Calendar event.

    Args:
        event_id: The Google Calendar event ID
        summary: New title (optional)
        start_datetime: New start time (optional)
        description: New description (optional)

    Returns:
        True if updated successfully, False otherwise

    Interview Notes:
    - Partial updates: only update provided fields
    - Fetch-modify-update pattern to preserve other fields
    - Used when task description or time changes
    """
    def get_timezone_name(dt: datetime) -> str:
        """Extract timezone name from datetime object."""
        if dt.tzinfo is None:
            return 'UTC'
        if hasattr(dt.tzinfo, 'zone'):
            return dt.tzinfo.zone
        tzname = dt.tzinfo.tzname(dt)
        if tzname:
            return tzname
        return 'UTC'

    try:
        service = get_calendar_service()

        # First, get the current event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update only the provided fields
        if summary:
            event['summary'] = summary
        if description:
            event['description'] = description
        if start_datetime:
            end_datetime = start_datetime + timedelta(minutes=30)
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': get_timezone_name(start_datetime),
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': get_timezone_name(end_datetime),
            }

        # Update the event
        service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return True

    except HttpError as e:
        print(f"❌ Error updating calendar event: {e}")
        return False

    except Exception as e:
        print(f"❌ Error updating calendar event: {str(e)}")
        return False
