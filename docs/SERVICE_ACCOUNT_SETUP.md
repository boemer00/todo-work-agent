# Google Calendar Service Account Setup

This guide shows you how to set up a service account for Google Calendar integration on Cloud Run.

## What is a Service Account?

A service account is like a robot user that your app uses to access Google Calendar. Unlike OAuth (which requires a browser), service accounts work in Cloud Run's headless environment.

**Trade-off**: All users will share ONE calendar. For per-user calendars, you'd need per-user OAuth (more complex).

---

## Step 1: Create Service Account

1. Go to [GCP Console - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your project: `todo-agent-476415`
3. Click **"+ CREATE SERVICE ACCOUNT"**
4. Fill in:
   - **Name**: `calendar-agent`
   - **Description**: `Service account for AI task agent calendar integration`
5. Click **"CREATE AND CONTINUE"**
6. Skip roles (not needed for Calendar API)
7. Click **"DONE"**

---

## Step 2: Download Service Account Key

1. Find your new service account in the list
2. Click on it to open details
3. Go to **"KEYS"** tab
4. Click **"ADD KEY"** → **"Create new key"**
5. Select **JSON** format
6. Click **"CREATE"**
7. A JSON file will download (e.g., `todo-agent-476415-abc123.json`)
8. **Rename it** to `service-account-key.json` (easier to remember)

**Important**: This file contains credentials. Never commit it to git!

---

## Step 3: Enable Google Calendar API

1. Go to [API Library](https://console.cloud.google.com/apis/library)
2. Search for **"Google Calendar API"**
3. Click on it
4. Click **"ENABLE"** (if not already enabled)

---

## Step 4: Share Calendar with Service Account

This is the magic step that gives the service account access to your calendar!

1. Open [Google Calendar](https://calendar.google.com/)
2. Find your calendar in the left sidebar (usually "My calendars")
3. Hover over the calendar name and click the **three dots** (⋮)
4. Click **"Settings and sharing"**
5. Scroll down to **"Share with specific people"**
6. Click **"+ Add people"**
7. Enter the service account email:
   - **Format**: `calendar-agent@todo-agent-476415.iam.gserviceaccount.com`
   - **Find it in**: Your downloaded JSON file, look for `"client_email"` field
8. Set permission: **"Make changes to events"**
9. Click **"Send"**

Your service account can now read/write to this calendar!

---

## Step 5: Upload Key to Secret Manager

Now we securely store the key in Google Cloud Secret Manager:

```bash
# Navigate to your project directory
cd /Users/renatoboemer/code/courses/my-agent

# Enable Secret Manager API (if not already enabled)
gcloud services enable secretmanager.googleapis.com --project=todo-agent-476415

# Create the secret and upload the key
gcloud secrets create calendar-service-account \
    --data-file=service-account-key.json \
    --project=todo-agent-476415

# Verify it was created
gcloud secrets list --project=todo-agent-476415
```

You should see `calendar-service-account` in the list!

---

## Step 6: Grant Cloud Run Access to Secret

```bash
# Get your Cloud Run service account email
# (Usually: PROJECT_NUMBER-compute@developer.gserviceaccount.com)
gcloud projects describe todo-agent-476415 --format="value(projectNumber)"

# Grant access (replace PROJECT_NUMBER with the actual number from above)
gcloud secrets add-iam-policy-binding calendar-service-account \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=todo-agent-476415
```

Alternatively, when you deploy to Cloud Run, add this flag:
```bash
--set-secrets=CALENDAR_SERVICE_ACCOUNT_SECRET=calendar-service-account:latest
```

---

## Step 7: Update Your .env

Your `.env` file should already have:
```bash
GOOGLE_CLOUD_PROJECT=todo-agent-476415
CALENDAR_SERVICE_ACCOUNT_SECRET=calendar-service-account
CLOUD_RUN=true
```

**For local testing with service account** (optional):
- Set `CLOUD_RUN=true` in your `.env`
- Run the app - it will use the service account from Secret Manager

**For local development with OAuth** (default):
- Set `CLOUD_RUN=false` or remove the variable
- Run the app - it will use your personal `credentials.json` and `token.json`

---

## Testing

### Test Locally with Service Account
```bash
# Set environment variable temporarily
export CLOUD_RUN=true

# Run the agent
python main.py

# Test adding a task with a date
# It should create an event in your shared calendar
```

### Test on Cloud Run
After deployment, send a WhatsApp message:
```
Add task: Team meeting tomorrow at 2pm
```

Check your Google Calendar - the event should appear!

---

## Troubleshooting

### "Secret not found" error
- Run: `gcloud secrets list --project=todo-agent-476415`
- Make sure `calendar-service-account` exists
- Check the secret name matches your `.env` file

### "Permission denied" error
- Make sure you shared the calendar with the service account email
- Verify the email matches the `client_email` in your JSON file

### "Calendar event not created"
- Check Cloud Run logs: `gcloud run logs tail ai-task-agent --project=todo-agent-476415`
- Look for Google Calendar API errors

### "Invalid JSON" error
- Verify your `service-account-key.json` is valid JSON
- Re-download the key from GCP Console if needed

---

## Security Notes

- **Never commit** `service-account-key.json` to git (it's in `.gitignore`)
- **Never share** the service account key publicly
- **Use Secret Manager** for production (not environment variables)
- **Rotate keys** periodically (every 90 days recommended)

---

## Next Steps

Once set up, your calendar integration will:
- ✓ Work in Cloud Run (no browser needed)
- ✓ Sync tasks with dates to Google Calendar
- ✓ Delete events when tasks are marked done
- ✓ All users share one calendar (acceptable for MVP)

**Future enhancement**: Implement per-user OAuth for individual calendars. This requires:
- OAuth callback endpoint in FastAPI
- Token storage in Cloud Storage (per user_id)
- Send auth link via WhatsApp for each user

---

## Resources

- [GCP Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
