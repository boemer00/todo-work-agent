# Google Calendar Integration Setup Guide

This guide walks you through setting up Google Calendar API credentials for the to-do agent.

## Prerequisites

- Google account
- Python environment with dependencies installed

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `todo-agent` (or your preferred name)
4. Click "Create"

### 2. Enable Google Calendar API

1. In your project dashboard, click "APIs & Services" → "Library"
2. Search for "Google Calendar API"
3. Click on "Google Calendar API"
4. Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `To-Do Agent`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip (click "Save and Continue")
   - Test users: Add your email
   - Click "Save and Continue"

4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: `To-Do Agent Desktop`
   - Click "Create"

5. Download credentials:
   - Click the download icon (⬇️) next to your newly created OAuth client
   - Save the file as `credentials.json` in your project root directory

### 4. Project Structure

Your project should now have:

```
my-agent/
├── credentials.json          # ← Download from Google Cloud Console
├── .env                      # Your environment variables
├── app.py
├── requirements.txt
└── ...
```

**IMPORTANT:**
- `credentials.json` is in `.gitignore` - **NEVER commit this file!**
- `token.json` will be auto-generated on first run - also in `.gitignore`

### 5. First-Time Authentication

When you first run a task with a due date, the agent will:

1. Open your default web browser
2. Ask you to sign in to your Google account
3. Request permission to access your Google Calendar
4. Click "Allow"
5. Browser will show "Authentication successful" - you can close it

The agent will save the token to `token.json` for future use.

## Testing the Integration

Try these commands with the agent:

```bash
python app.py
```

```
You: remind me to call Gabi tomorrow at 10am

🤖 Agent: I've added "call Gabi" to your task list and created a calendar reminder for tomorrow at 10:00 AM!
```

Check your Google Calendar - you should see the event!

## Troubleshooting

### "credentials.json not found"

- Make sure you downloaded the credentials file from Google Cloud Console
- Rename it to exactly `credentials.json`
- Place it in the project root directory (same level as `app.py`)

### "Access blocked: This app is not verified"

- In Google Cloud Console, make sure your app is in "Testing" mode
- Add your email to "Test users" in the OAuth consent screen

### "Insufficient permissions"

- Delete `token.json` and re-run the authentication flow
- Make sure you granted all requested permissions

### Rate Limits

- Google Calendar API has a quota of 1,000,000 queries/day
- For a personal to-do agent, you'll never hit this limit
- In production, implement exponential backoff for rate limit errors

## Security Best Practices

✅ **DO:**
- Keep `credentials.json` and `token.json` in `.gitignore`
- Use environment variables for sensitive config
- Only grant minimum required scopes (`calendar.events`)
- Regularly review authorized apps in your Google Account settings

❌ **DON'T:**
- Commit credentials to git (even private repos)
- Share credentials with others
- Use production credentials for development
- Grant full calendar access if you only need events

## Production Deployment

For production use (e.g., deployed as a service):

1. **Service Account Auth** (instead of OAuth)
   - Create a service account in Google Cloud Console
   - Download service account key JSON
   - Use `google.oauth2.service_account.Credentials`
   - No browser-based OAuth flow needed

2. **Secret Management**
   - Use cloud secret managers (AWS Secrets Manager, Google Secret Manager)
   - Never store credentials in code or environment variables in cloud platforms
   - Rotate credentials regularly

3. **Scope Down Permissions**
   - Use `calendar.events.readonly` if only reading
   - Use specific calendar IDs instead of 'primary'
   - Implement least-privilege access

## Interview Talking Points

When discussing this integration:

1. **OAuth 2.0 Flow**: "I implemented the authorization code flow for desktop apps, which opens a browser for first-time auth and uses refresh tokens for subsequent access."

2. **Security**: "Credentials are gitignored and tokens are stored locally. In production, I'd use a service account with secret management."

3. **Error Handling**: "The code handles token expiration with automatic refresh, and gracefully fails if the API is unavailable."

4. **Scope Limitation**: "I only request `calendar.events` scope, not full calendar access - principle of least privilege."

5. **Rate Limiting**: "Google Calendar has generous quotas, but I'd implement exponential backoff and circuit breakers for production."

6. **Testing Strategy**: "For testing, I'd use the Google Calendar API test environment and mock the API calls in unit tests."

---

**Happy Scheduling! 📅**
