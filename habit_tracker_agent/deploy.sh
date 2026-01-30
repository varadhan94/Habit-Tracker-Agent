#!/bin/bash
# Deployment script for all Cloud Functions
# Copies shared code into each function directory, deploys, then cleans up

set -e

PROJECT_ID="habit-tracker-agent-varadha"
REGION="asia-south1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploying Habit Tracker Agent ==="
echo ""

# Check for required environment variables or prompt
if [ -z "$SHEET_ID" ]; then
    read -p "Enter your Google Sheet ID: " SHEET_ID
fi

if [ -z "$USER_PHONE_NUMBER" ]; then
    read -p "Enter your WhatsApp number (with country code, no +): " USER_PHONE_NUMBER
fi

# Function to prepare a function directory with shared code
prepare_function() {
    local func_dir="$1"
    echo "  Preparing $func_dir..."

    # Copy shared modules and config into the function directory
    cp -r "$SCRIPT_DIR/shared" "$func_dir/shared"
    cp "$SCRIPT_DIR/config.py" "$func_dir/config.py"
    cp "$SCRIPT_DIR/requirements.txt" "$func_dir/requirements.txt"
}

# Function to clean up copied files after deployment
cleanup_function() {
    local func_dir="$1"
    rm -rf "$func_dir/shared"
    rm -f "$func_dir/config.py"
    rm -f "$func_dir/requirements.txt"
}

# Common environment variables for all functions
COMMON_ENV_VARS="GCP_PROJECT_ID=$PROJECT_ID,SHEET_ID=$SHEET_ID,SHEET_NAME=Habits Tracker,USER_PHONE_NUMBER=$USER_PHONE_NUMBER"

# Common secrets
COMMON_SECRETS="META_ACCESS_TOKEN=meta-access-token:latest,META_APP_SECRET=meta-app-secret:latest,META_PHONE_NUMBER_ID=meta-phone-number-id:latest,GEMINI_API_KEY=gemini-api-key:latest,WHATSAPP_VERIFY_TOKEN=whatsapp-verify-token:latest,GOOGLE_SHEETS_CREDENTIALS_JSON=sheets-credentials:latest"

# --- Deploy sendDailyPrompt ---
echo ""
echo "1/3: Deploying sendDailyPrompt..."
FUNC_DIR="$SCRIPT_DIR/functions/send_daily_prompt"
prepare_function "$FUNC_DIR"

gcloud functions deploy sendDailyPrompt \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source="$FUNC_DIR" \
    --entry-point=send_daily_prompt \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="$COMMON_ENV_VARS" \
    --set-secrets="$COMMON_SECRETS" \
    --memory=256Mi \
    --timeout=60s

cleanup_function "$FUNC_DIR"
echo "sendDailyPrompt deployed successfully."

# --- Deploy handleWhatsAppReply ---
echo ""
echo "2/3: Deploying handleWhatsAppReply..."
FUNC_DIR="$SCRIPT_DIR/functions/handle_whatsapp_reply"
prepare_function "$FUNC_DIR"

gcloud functions deploy handleWhatsAppReply \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source="$FUNC_DIR" \
    --entry-point=handle_whatsapp_reply \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars="$COMMON_ENV_VARS" \
    --set-secrets="$COMMON_SECRETS" \
    --memory=256Mi \
    --timeout=120s

cleanup_function "$FUNC_DIR"
echo "handleWhatsAppReply deployed successfully."

# Get the webhook URL for Meta configuration
WEBHOOK_URL=$(gcloud functions describe handleWhatsAppReply --region="$REGION" --format='value(serviceConfig.uri)')
echo ""
echo "  WEBHOOK URL (set this in Meta App Dashboard):"
echo "  $WEBHOOK_URL"

# --- Deploy sendWeeklyReport ---
echo ""
echo "3/3: Deploying sendWeeklyReport..."
FUNC_DIR="$SCRIPT_DIR/functions/send_weekly_report"
prepare_function "$FUNC_DIR"

gcloud functions deploy sendWeeklyReport \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source="$FUNC_DIR" \
    --entry-point=send_weekly_report \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="$COMMON_ENV_VARS" \
    --set-secrets="$COMMON_SECRETS" \
    --memory=256Mi \
    --timeout=120s

cleanup_function "$FUNC_DIR"
echo "sendWeeklyReport deployed successfully."

echo ""
echo "=== All Functions Deployed ==="
echo ""
echo "Next steps:"
echo "  1. Set the webhook URL in Meta App Dashboard: $WEBHOOK_URL"
echo "  2. Run: bash scripts/setup_scheduler.sh"
echo "  3. Test: gcloud scheduler jobs run daily-habit-prompt --location=$REGION"
