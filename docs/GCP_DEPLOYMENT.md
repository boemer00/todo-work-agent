# Google Cloud Run Deployment Guide

Complete guide for deploying the AI Task Agent to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**
   - Sign up at [cloud.google.com](https://cloud.google.com)
   - Free tier: $300 credit for 90 days
   - Credit card required (but won't be charged without upgrade)

2. **gcloud CLI installed**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

3. **Docker installed**
   ```bash
   # macOS
   brew install docker

   # Or download Docker Desktop: https://www.docker.com/products/docker-desktop
   ```

4. **Environment variables configured**
   - Copy `.env.example` to `.env`
   - Add your `OPENAI_API_KEY`
   - Add other required keys

---

## Quick Deploy (Automated)

The easiest way to deploy:

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Deploy (will use your default GCP project)
./deploy.sh

# Or specify project and region
./deploy.sh my-project-123 us-central1
```

The script will:
1. ✅ Enable required GCP APIs
2. ✅ Create Cloud Storage bucket
3. ✅ Create service account with permissions
4. ✅ Build Docker image
5. ✅ Push to Container Registry
6. ✅ Deploy to Cloud Run
7. ✅ Output your service URL

**That's it!** Your agent is now live.

---

## Manual Deploy (Step-by-Step)

If you prefer manual control or want to understand each step:

### Step 1: Set Up GCP Project

```bash
# Login to GCP
gcloud auth login

# Create new project (or use existing)
gcloud projects create my-agent-project --name="AI Task Agent"

# Set as default project
gcloud config set project my-agent-project

# Enable billing (required for Cloud Run)
# Do this in Cloud Console: https://console.cloud.google.com/billing
```

### Step 2: Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Step 3: Create Cloud Storage Bucket

```bash
# Create bucket for database storage
PROJECT_ID=$(gcloud config get-value project)
BUCKET_NAME="${PROJECT_ID}-task-agent-db"

gsutil mb -l us-central1 gs://$BUCKET_NAME

# Verify bucket created
gsutil ls
```

### Step 4: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create task-agent-sa \
  --display-name="Task Agent Service Account"

# Get service account email
SA_EMAIL="task-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Storage Admin permission
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"
```

### Step 5: Build Docker Image

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Build image
docker build -t gcr.io/$PROJECT_ID/ai-task-agent:latest .

# Verify image built
docker images | grep ai-task-agent
```

### Step 6: Push to Container Registry

```bash
# Push image
docker push gcr.io/$PROJECT_ID/ai-task-agent:latest

# Verify push succeeded
gcloud container images list
```

### Step 7: Deploy to Cloud Run

```bash
# Get your environment variables
source .env

# Deploy
gcloud run deploy ai-task-agent \
  --image gcr.io/$PROJECT_ID/ai-task-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY}" \
  --set-env-vars "GOOGLE_CLOUD_STORAGE_BUCKET=${BUCKET_NAME}" \
  --set-env-vars "CLOUD_RUN=true" \
  --service-account task-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### Step 8: Get Service URL

```bash
# Get URL
gcloud run services describe ai-task-agent \
  --platform managed \
  --region us-central1 \
  --format "value(status.url)"

# Example output: https://ai-task-agent-abc123-uc.a.run.app
```

### Step 9: Test Deployment

```bash
# Test health endpoint
curl https://YOUR-SERVICE-URL/health/

# Expected output:
# {"status":"healthy","database":"accessible","service":"ai-task-agent"}

# Test root endpoint
curl https://YOUR-SERVICE-URL/

# Expected output:
# {"status":"running","message":"AI Task Agent API","version":"1.0.0","environment":"cloud"}
```

---

## Configure Twilio Webhook

Now connect Twilio to your Cloud Run deployment:

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Settings** → **WhatsApp Sandbox**
3. Under "WHEN A MESSAGE COMES IN":
   - URL: `https://YOUR-SERVICE-URL/whatsapp/webhook`
   - Method: `POST`
4. Click **Save**

Test by sending a WhatsApp message to your Twilio sandbox number!

---

## Monitoring & Logs

### View Logs

```bash
# Tail logs in real-time
gcloud run logs tail ai-task-agent --project $PROJECT_ID

# View recent logs
gcloud run logs read ai-task-agent --limit 50
```

### View Metrics

```bash
# Get service details
gcloud run services describe ai-task-agent --region us-central1

# View in Cloud Console
# https://console.cloud.google.com/run
```

### Common Log Messages

**Successful startup**:
```
INFO - Starting application...
INFO - Running in cloud environment, downloading databases...
INFO - Task database ready at: /tmp/tasks.db
INFO - Application started successfully
```

**Successful request**:
```
INFO - POST /whatsapp/webhook
INFO - 200 OK
```

**Database sync**:
```
INFO - Uploading tasks.db to Cloud Storage bucket...
INFO - Successfully uploaded database to Cloud Storage
```

---

## Updating Your Deployment

### Update Code

```bash
# Make your code changes, then:
./deploy.sh

# Or manually:
docker build -t gcr.io/$PROJECT_ID/ai-task-agent:latest .
docker push gcr.io/$PROJECT_ID/ai-task-agent:latest
gcloud run deploy ai-task-agent \
  --image gcr.io/$PROJECT_ID/ai-task-agent:latest \
  --region us-central1
```

### Update Environment Variables

```bash
gcloud run services update ai-task-agent \
  --region us-central1 \
  --set-env-vars "NEW_VAR=value"
```

### Update Resources

```bash
# Increase memory
gcloud run services update ai-task-agent \
  --region us-central1 \
  --memory 2Gi

# Increase CPU
gcloud run services update ai-task-agent \
  --region us-central1 \
  --cpu 2

# Set minimum instances (reduces cold starts)
gcloud run services update ai-task-agent \
  --region us-central1 \
  --min-instances 1
```

---

## Troubleshooting

### Issue: "Permission denied" when accessing Cloud Storage

**Solution**:
```bash
# Verify service account has permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:task-agent-sa*"

# Re-grant permissions if needed
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:task-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### Issue: Container fails to start

**Solution**:
```bash
# Check logs
gcloud run logs read ai-task-agent --limit 100

# Common causes:
# - Missing environment variable (OPENAI_API_KEY)
# - Invalid Docker image
# - Port mismatch (must use $PORT env var)
```

### Issue: "Service Unavailable" or 503 errors

**Solution**:
```bash
# Check if service is running
gcloud run services describe ai-task-agent --region us-central1

# Check container logs for startup errors
gcloud run logs read ai-task-agent

# Increase timeout if agent is slow
gcloud run services update ai-task-agent \
  --timeout 600 \
  --region us-central1
```

### Issue: Cold starts are slow

**Solution**:
```bash
# Keep 1 instance warm (costs ~$10-15/month)
gcloud run services update ai-task-agent \
  --min-instances 1 \
  --region us-central1

# Or optimize Docker image:
# - Use multi-stage build (already done)
# - Minimize dependencies
# - Use lighter base image
```

### Issue: Database not persisting

**Solution**:
```bash
# Verify bucket exists
gsutil ls gs://${PROJECT_ID}-task-agent-db/

# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID | grep task-agent-sa

# Check logs for upload errors
gcloud run logs read ai-task-agent | grep "upload"
```

---

## Cost Optimization

### Free Tier Limits (always free)

- **Cloud Run**: 2 million requests/month
- **Cloud Storage**: 5 GB storage
- **Container Registry**: 5 GB storage

### Estimated Monthly Costs

**Low usage (1,000 WhatsApp messages/month)**:
- Cloud Run: $0 (within free tier)
- Cloud Storage: $0 (< 1 MB database)
- **Total**: ~$0/month 🎉

**Medium usage (10,000 WhatsApp messages/month)**:
- Cloud Run: $0 (within free tier)
- Cloud Storage: $0 (< 1 MB database)
- **Total**: ~$0/month 🎉

**High usage (100,000 messages/month)**:
- Cloud Run: ~$5 (CPU/memory time)
- Cloud Storage: $0 (< 1 MB database)
- **Total**: ~$5/month

**With min-instances=1 (no cold starts)**:
- Cloud Run: ~$10-15/month (always-on instance)
- Cloud Storage: $0
- **Total**: ~$10-15/month

### Cost Monitoring

```bash
# View current month costs
gcloud billing accounts list
gcloud alpha billing budgets list

# Set up budget alert in Cloud Console:
# https://console.cloud.google.com/billing/budgets
```

---

## Security Best Practices

### 1. Use Secret Manager (Instead of Environment Variables)

```bash
# Create secret
echo -n "your-openai-key" | gcloud secrets create openai-api-key --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:task-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update Cloud Run to use secret
gcloud run services update ai-task-agent \
  --update-secrets=OPENAI_API_KEY=openai-api-key:latest \
  --region us-central1
```

### 2. Restrict Service Access

```bash
# Remove unauthenticated access
gcloud run services update ai-task-agent \
  --no-allow-unauthenticated \
  --region us-central1

# Only allow Twilio to call your webhook (implement signature validation)
```

### 3. Enable VPC Connector (for private resources)

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create my-connector \
  --region us-central1 \
  --range 10.8.0.0/28

# Use connector in Cloud Run
gcloud run services update ai-task-agent \
  --vpc-connector my-connector \
  --region us-central1
```

---

## Production Checklist

Before going live:

- [ ] Set up billing alerts
- [ ] Configure Secret Manager for API keys
- [ ] Enable Cloud Logging & Monitoring
- [ ] Set up error alerting (email/Slack)
- [ ] Implement Twilio signature validation
- [ ] Set max-instances limit (prevent runaway costs)
- [ ] Test database backup/restore
- [ ] Document rollback procedure
- [ ] Set up staging environment
- [ ] Load test your endpoints

---

## Advanced: CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - id: auth
      uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY }}

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1

    - name: Build and Push
      run: |
        gcloud builds submit --tag gcr.io/$PROJECT_ID/ai-task-agent

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy ai-task-agent \
          --image gcr.io/$PROJECT_ID/ai-task-agent \
          --region us-central1
```

---

## Support & Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting)

---

**Your AI Task Agent is now running in production on Google Cloud! 🚀**
