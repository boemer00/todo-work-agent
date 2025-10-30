#!/bin/bash
# Deployment script for Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
DEFAULT_REGION="us-central1"
DEFAULT_SERVICE_NAME="ai-task-agent"

# Parse arguments
PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION=${2:-$DEFAULT_REGION}
SERVICE_NAME=${3:-$DEFAULT_SERVICE_NAME}

# Validate PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID not provided and no default project set${NC}"
    echo "Usage: ./deploy.sh [PROJECT_ID] [REGION] [SERVICE_NAME]"
    echo "Example: ./deploy.sh my-project-123 us-central1 ai-task-agent"
    exit 1
fi

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Deploying AI Task Agent to Cloud Run${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with required environment variables"
    echo "See .env.example for reference"
    exit 1
fi

# Source .env file to get variables
export $(cat .env | grep -v '^#' | xargs)

# Validate required environment variables
REQUIRED_VARS=("OPENAI_API_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var not set in .env file${NC}"
        exit 1
    fi
done

# Step 1: Set project
echo -e "${YELLOW}Step 1: Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Step 3: Create Cloud Storage bucket (if not exists)
BUCKET_NAME="${PROJECT_ID}-task-agent-db"
echo -e "${YELLOW}Step 3: Creating Cloud Storage bucket...${NC}"
if ! gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo -e "${GREEN}Bucket created: gs://$BUCKET_NAME${NC}"
else
    echo "Bucket already exists: gs://$BUCKET_NAME"
fi

# Step 4: Create service account (if not exists)
SERVICE_ACCOUNT_NAME="task-agent-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo -e "${YELLOW}Step 4: Creating service account...${NC}"
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Task Agent Service Account"
    echo -e "${GREEN}Service account created${NC}"
else
    echo "Service account already exists"
fi

# Step 5: Grant permissions
echo -e "${YELLOW}Step 5: Granting permissions...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin" \
    --condition=None

# Step 6: Build Docker image
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
echo -e "${YELLOW}Step 6: Building Docker image for Cloud Run (amd64)...${NC}"
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Step 7: Push to Container Registry
echo -e "${YELLOW}Step 7: Pushing image to Container Registry...${NC}"
docker push $IMAGE_NAME

# Step 8: Deploy to Cloud Run
echo -e "${YELLOW}Step 8: Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY}" \
    --set-env-vars "GOOGLE_CLOUD_STORAGE_BUCKET=${BUCKET_NAME}" \
    --set-env-vars "CLOUD_RUN=true" \
    --set-env-vars "LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2:-false}" \
    --set-env-vars "LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY:-}" \
    --set-env-vars "LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-my-agent}" \
    --service-account $SERVICE_ACCOUNT_EMAIL

# Step 9: Get service URL
echo -e "${YELLOW}Step 9: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format "value(status.url)")

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"
echo ""
echo "Next steps:"
echo "1. Test health endpoint: curl ${SERVICE_URL}/health/"
echo "2. Configure Twilio webhook: ${SERVICE_URL}/whatsapp/webhook"
echo "3. Test WhatsApp integration"
echo ""
echo "View logs:"
echo "  gcloud run logs tail ${SERVICE_NAME} --project ${PROJECT_ID}"
echo ""
echo "Update deployment:"
echo "  ./deploy.sh ${PROJECT_ID} ${REGION}"
echo ""
