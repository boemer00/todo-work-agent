# GitHub Secrets Setup for CI/CD Pipeline

## Quick Setup (5-10 minutes)

Follow these steps to configure GitHub Secrets for automated deployment to Google Cloud Run.

---

## 1. Create GCP Service Account

```bash
# Set your project ID
export PROJECT_ID="todo-agent-476415"

# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD" \
  --project=${PROJECT_ID}

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

echo "✅ Service account key saved to: github-actions-key.json"
```

---

## 2. Create Artifact Registry Repository (for Docker images)

```bash
# Create repository if it doesn't exist
gcloud artifacts repositories create ai-task-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for AI Task Agent" \
  --project=${PROJECT_ID}

echo "✅ Artifact Registry repository created"
```

---

## 3. Add Secrets to GitHub

Go to your GitHub repository:
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Required Secrets (7 total)

#### 1. **GCP_SA_KEY**
```bash
# Copy the entire contents of github-actions-key.json
cat github-actions-key.json
```
- Paste the entire JSON content (including `{` and `}`)

#### 2. **GCP_PROJECT_ID**
```
project-id-...
```

#### 3. **GCS_BUCKET**
```
buckect-name-...
```

#### 4. **OPENAI_API_KEY**
```
sk-proj-...
```

#### 5. **LANGSMITH_API_KEY**
```
lsv2_pt_...
```

#### 6. **TWILIO_ACCOUNT_SID**
```
AC_SID...
```

#### 7. **TWILIO_AUTH_TOKEN**
```
TOKEN...
```

#### 8. **TWILIO_WHATSAPP_NUMBER**
```
whatsapp:+...
```

#### 9. **REDIS_URL**
```
redis://default:PASSWORD@...
```

---

## 4. Verify Setup

After adding all secrets, your GitHub Actions workflow will automatically:

1. ✅ Run tests on every push
2. ✅ Build Docker image on push to `main`
3. ✅ Deploy to Cloud Run on push to `main`
4. ✅ Run health checks after deployment

---

## 5. Test the Pipeline

```bash
# Make a small change and push to main
git checkout main
echo "# CI/CD is live!" >> README.md
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

Watch the pipeline run at:
https://github.com/boemer00/my-agent/actions

---

## 6. Security Notes

- ✅ Service account key is stored securely in GitHub Secrets
- ✅ Never commit `github-actions-key.json` to git
- ✅ Delete the local key file after adding to GitHub:
  ```bash
  rm github-actions-key.json
  ```

---

## 7. Troubleshooting

### Pipeline fails with "Permission denied"
- Verify service account has all 4 roles (run.admin, storage.admin, iam.serviceAccountUser, artifactregistry.admin)

### Docker push fails with "Repository not found"
- Run: `gcloud artifacts repositories create ai-task-agent --repository-format=docker --location=us-central1`

### Deployment fails with "Service account does not exist"
- Check that service account email matches: `github-actions@todo-agent-476415.iam.gserviceaccount.com`

---

## 8. What Happens on Each Push

### On Feature Branches:
- ✅ Run tests
- ✅ Report coverage
- ❌ No deployment

### On Main Branch:
- ✅ Run tests
- ✅ Build Docker image
- ✅ Push to Artifact Registry
- ✅ Deploy to Cloud Run
- ✅ Health check production
- ✅ Post deployment URL

---

**Time to complete**: ~10 minutes
**One-time setup**: Yes (secrets persist across all future runs)

Once configured, every push to `main` automatically deploys to production! 🚀
