#!/bin/bash
# Setup script for Google Cloud Project
# Run this once to set up the GCP infrastructure

set -e

PROJECT_ID="habit-tracker-agent-varadha"
REGION="asia-south1"
SERVICE_ACCOUNT_NAME="habit-sheets-sa"

echo "=== Habit Tracker Agent - GCP Setup ==="
echo ""

# Step 1: Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Install it first:"
    echo "  brew install google-cloud-sdk"
    exit 1
fi

# Step 2: Authenticate
echo "Step 1: Authenticating with Google Cloud..."
gcloud auth login

# Step 3: Create project
echo ""
echo "Step 2: Creating project '$PROJECT_ID'..."
gcloud projects create "$PROJECT_ID" --name="Habit Tracker Agent" 2>/dev/null || \
    echo "Project already exists, continuing..."

# Step 4: Set active project
gcloud config set project "$PROJECT_ID"

# Step 5: Prompt for billing
echo ""
echo "Step 3: Please enable billing for the project."
echo "  Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo ""
read -p "Press Enter after enabling billing..."

# Step 6: Enable APIs
echo ""
echo "Step 4: Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable generativelanguage.googleapis.com
echo "APIs enabled successfully."

# Step 7: Create service account for Sheets access
echo ""
echo "Step 5: Creating service account for Google Sheets..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Habit Tracker Sheets Service Account" 2>/dev/null || \
    echo "Service account already exists, continuing..."

SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Service account email: $SA_EMAIL"

# Step 8: Download service account key
echo ""
echo "Step 6: Downloading service account credentials..."
CREDS_FILE="$(dirname "$0")/../credentials.json"
gcloud iam service-accounts keys create "$CREDS_FILE" \
    --iam-account="$SA_EMAIL"
echo "Credentials saved to: $CREDS_FILE"

# Step 9: Get project number for secret access
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Step 10: Store secrets
echo ""
echo "Step 7: Storing secrets in Secret Manager..."
echo "  You'll be prompted to enter each secret value."
echo ""

read -sp "Enter your Meta WhatsApp Access Token: " META_TOKEN
echo ""
printf "%s" "$META_TOKEN" | gcloud secrets create meta-access-token --data-file=- 2>/dev/null || \
    printf "%s" "$META_TOKEN" | gcloud secrets versions add meta-access-token --data-file=-

read -sp "Enter your Meta App Secret: " META_SECRET
echo ""
printf "%s" "$META_SECRET" | gcloud secrets create meta-app-secret --data-file=- 2>/dev/null || \
    printf "%s" "$META_SECRET" | gcloud secrets versions add meta-app-secret --data-file=-

read -p "Enter your Meta Phone Number ID: " META_PHONE_ID
printf "%s" "$META_PHONE_ID" | gcloud secrets create meta-phone-number-id --data-file=- 2>/dev/null || \
    printf "%s" "$META_PHONE_ID" | gcloud secrets versions add meta-phone-number-id --data-file=-

read -sp "Enter your Gemini API Key: " GEMINI_KEY
echo ""
printf "%s" "$GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=- 2>/dev/null || \
    printf "%s" "$GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

read -p "Enter a custom webhook verify token (any random string): " VERIFY_TOKEN
printf "%s" "$VERIFY_TOKEN" | gcloud secrets create whatsapp-verify-token --data-file=- 2>/dev/null || \
    printf "%s" "$VERIFY_TOKEN" | gcloud secrets versions add whatsapp-verify-token --data-file=-

# Store sheets credentials as a secret too
gcloud secrets create sheets-credentials --data-file="$CREDS_FILE" 2>/dev/null || \
    gcloud secrets versions add sheets-credentials --data-file="$CREDS_FILE"

# Step 11: Grant Cloud Functions access to secrets
echo ""
echo "Step 8: Granting secret access to Cloud Functions..."
for SECRET in meta-access-token meta-app-secret meta-phone-number-id gemini-api-key whatsapp-verify-token sheets-credentials; do
    gcloud secrets add-iam-policy-binding "$SECRET" \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet
done
echo "Secret access granted."

echo ""
echo "=== GCP Setup Complete ==="
echo ""
echo "IMPORTANT: Share your Google Sheet with this email (Editor access):"
echo "  $SA_EMAIL"
echo ""
echo "Next steps:"
echo "  1. Share your Google Sheet with the service account email above"
echo "  2. Set up Meta WhatsApp Business (see scripts/setup_meta.sh)"
echo "  3. Run deploy.sh to deploy the Cloud Functions"
echo "  4. Run scripts/setup_scheduler.sh to create scheduled jobs"
