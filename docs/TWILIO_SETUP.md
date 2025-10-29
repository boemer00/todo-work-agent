# Twilio WhatsApp Integration Setup Guide

This guide walks you through setting up Twilio WhatsApp integration for your AI Task Agent.

## Prerequisites

- A Twilio account (free trial available with $15 credit)
- Your FastAPI server running (locally or on Cloud Run)

---

## Step 1: Create Twilio Account

1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a free account
3. Verify your email and phone number
4. You'll receive $15 in free credit (enough for ~3,000 WhatsApp messages)

---

## Step 2: Access WhatsApp Sandbox

The WhatsApp Sandbox lets you test WhatsApp messaging without business verification.

1. Log in to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. You'll see the WhatsApp Sandbox page

### Join the Sandbox

1. On the Sandbox page, you'll see:
   - A phone number (e.g., `+1 415 123 4567`)
   - A join code (e.g., `join abc-xyz`)

2. On your phone:
   - Open WhatsApp
   - Send a message to the Twilio number
   - Message content: `join abc-xyz` (use YOUR specific code)

3. You'll receive a confirmation message from Twilio

**Note**: The sandbox is free but has limitations:
- Messages expire after 24 hours of inactivity
- Users must join with the code phrase
- "From Twilio Sandbox" appears in messages

---

## Step 3: Get Twilio Credentials

1. In Twilio Console, go to **Account** → **API keys & tokens**
2. Find your credentials:
   - **Account SID**: Starts with `AC...`
   - **Auth Token**: Click "Show" to reveal

3. Add to your `.env` file:
```bash
# Twilio credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+14151234567  # The sandbox number
```

---

## Step 4: Configure Webhook URL

### For Local Testing (using ngrok)

1. **Install ngrok**:
   ```bash
   # macOS
   brew install ngrok

   # Or download from https://ngrok.com/download
   ```

2. **Start your FastAPI server**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8080
   ```

3. **Start ngrok tunnel** (in a new terminal):
   ```bash
   ngrok http 8080
   ```

4. **Copy the ngrok URL**:
   ```
   Forwarding: https://abc123.ngrok.io -> http://localhost:8080
   ```

5. **Configure Twilio webhook**:
   - In Twilio Console → Messaging → Settings → WhatsApp Sandbox
   - Under "WHEN A MESSAGE COMES IN":
     - URL: `https://abc123.ngrok.io/whatsapp/webhook`
     - Method: `POST`
   - Click **Save**

### For Cloud Run Deployment

1. **Deploy to Cloud Run** (see Phase 7)

2. **Get Cloud Run URL**:
   ```bash
   gcloud run services describe ai-task-agent \
     --region us-central1 \
     --format "value(status.url)"
   ```
   Example: `https://ai-task-agent-abc123-uc.a.run.app`

3. **Configure Twilio webhook**:
   - URL: `https://YOUR-CLOUD-RUN-URL/whatsapp/webhook`
   - Method: `POST`
   - Click **Save**

---

## Step 5: Test the Integration

### Test via WhatsApp

1. Open WhatsApp on your phone
2. Send a message to the Twilio sandbox number
3. Try these commands:
   ```
   list tasks
   add task buy groceries
   add reminder call Gabi tomorrow at 3pm
   mark task 1 done
   help
   ```

### Test via curl (for debugging)

```bash
# Test the webhook endpoint
curl -X POST http://localhost:8080/whatsapp/webhook \
  -d "Body=list tasks" \
  -d "From=whatsapp:+1234567890"

# You should get back TwiML XML with the agent's response
```

---

## Step 6: Monitor & Debug

### View Twilio Logs

1. Go to Twilio Console → **Monitor** → **Logs** → **WhatsApp**
2. See all incoming/outgoing messages
3. Check for webhook errors

### View Your Application Logs

**Local**:
- Check terminal where uvicorn is running

**Cloud Run**:
```bash
gcloud run logs tail ai-task-agent --project YOUR_PROJECT_ID
```

---

## Troubleshooting

### Issue: "Unable to reach webhook URL"

**Solution**:
- Check that your server is running
- Verify ngrok tunnel is active
- Ensure webhook URL is correct in Twilio console
- Check firewall settings

### Issue: "Messages not being received"

**Solution**:
- Verify you joined the sandbox with the correct code
- Check that webhook URL has `/whatsapp/webhook` path
- Look at Twilio logs for errors

### Issue: "Agent not responding correctly"

**Solution**:
- Check `OPENAI_API_KEY` is set in `.env`
- Verify database is initialized (`data/tasks.db` exists)
- Look at application logs for Python errors

---

## Upgrading to Production WhatsApp

The sandbox is great for testing, but for production you need:

1. **Meta Business Verification**:
   - Create Meta Business Account
   - Verify your business (1-2 days)
   - Submit WhatsApp Business Profile

2. **Get Production Access**:
   - Apply for WhatsApp Business API access
   - Provide business documentation
   - Approval takes 1-7 days

3. **Switch to Meta Cloud API** (FREE):
   - 1,000 conversations/month free
   - No Twilio fees
   - Official Meta integration

4. **Or Continue with Twilio** (PAID):
   - $0.005 per message
   - Easier setup than Meta
   - Better support

**Recommendation**: Start with Twilio Sandbox, upgrade to Meta Cloud API when ready for production.

---

## Cost Estimates

### Twilio Pricing
- **Free Trial**: $15 credit (~3,000 messages)
- **After Trial**:
  - WhatsApp messages: $0.005 per message
  - For 1,000 messages/month = $5/month
  - For 10,000 messages/month = $50/month

### Meta Cloud API (Production)
- **Free Tier**: 1,000 conversations/month
- **After Free Tier**: ~$0.01-0.05 per conversation
- **Conversation** = 24-hour window of messages

---

## Security Best Practices

1. **Validate Webhook Signatures**:
   ```python
   from twilio.request_validator import RequestValidator

   validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))
   is_valid = validator.validate(url, post_data, signature)
   ```

2. **Use HTTPS Only**:
   - Twilio requires HTTPS for webhooks
   - ngrok provides HTTPS by default
   - Cloud Run provides HTTPS by default

3. **Rate Limiting**:
   - Implement rate limiting to prevent abuse
   - Twilio has built-in rate limits

4. **Keep Credentials Secret**:
   - Never commit `TWILIO_AUTH_TOKEN` to git
   - Use environment variables or secret managers

---

## Next Steps

Once Twilio is working:
1. ✅ Test all agent commands via WhatsApp
2. ✅ Verify conversation memory works (agent remembers context)
3. ✅ Test Google Calendar integration
4. ✅ Monitor for errors and performance
5. 🚀 Deploy to Cloud Run for 24/7 availability

---

## Useful Links

- [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- [Twilio Console](https://console.twilio.com/)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [WhatsApp Formatting](https://faq.whatsapp.com/539178204879377/)
- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)

---

**Status**: Ready to test with Twilio WhatsApp Sandbox! 🎉
