# Variables
PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./setup_gcp.sh PROJECT_ID"
    exit 1
fi

echo "=== Starting GCP Infrastructure Setup for Project: $PROJECT_ID ==="

# 0. Create Project if it doesn't exist
if ! gcloud projects describe $PROJECT_ID > /dev/null 2>&1; then
    echo "[0/5] Creating Project $PROJECT_ID..."
    gcloud projects create $PROJECT_ID --name="Event Driven Alerts"
    
    # Billing Account Link
    echo "--- Billing Account Selection ---"
    gcloud billing accounts list
    echo "Please enter the BILLING_ACCOUNT_ID to link to this project:"
    read BILLING_ACCOUNT_ID
    
    if [ ! -z "$BILLING_ACCOUNT_ID" ]; then
        echo "Linking $PROJECT_ID to $BILLING_ACCOUNT_ID..."
        gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
    else
        echo "Warning: No billing account provided. Some services may not be enabled."
    fi
else
    echo "[0/5] Project $PROJECT_ID already exists."
fi

# 1. Enable Necessary APIs
echo "[1/5] Enabling APIs..."
gcloud services enable \
    cloudfunctions.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID

# 2. Create Service Account
echo "[2/5] Creating Service Account..."
SA_NAME="event-alerts-sa"
gcloud iam service-accounts create $SA_NAME \
    --description="Service account for automated event ingestion" \
    --display-name="Event Alerts SA" \
    --project=$PROJECT_ID

# 3. Setup Secret Manager (for SMTP password)
echo "[3/5] Initializing Secret Manager..."
echo "Please enter your SMTP App Password (will be hidden):"
read -s SMTP_PASS
echo -n "$SMTP_PASS" | gcloud secrets create SMTP_PASSWORD --data-file=- --project=$PROJECT_ID
gcloud secrets add-iam-policy-binding SMTP_PASSWORD \
    --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

# 4. Create Pub/Sub Topic for Trigger
echo "[4/5] Creating Pub/Sub Topic..."
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID

# 5. Create Cloud Scheduler Job
echo "[5/6] Creating Cloud Scheduler Job (Weekly on Mondays at 8AM)..."
gcloud scheduler jobs create pubsub weekly-ingestion-job \
    --schedule="0 8 * * 1" \
    --topic=$TOPIC_NAME \
    --message-body="Run Ingestion" \
    --time-zone="America/New_York" \
    --project=$PROJECT_ID

# 6. Deploy Code to Cloud Functions
echo "[6/6] Deploying code to Cloud Functions..."
gcloud functions deploy event-ingestion-engine \
    --project=$PROJECT_ID \
    --runtime=python310 \
    --trigger-topic=$TOPIC_NAME \
    --entry-point=cloud_function_entry \
    --service-account=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --region=us-central1 \
    --source=. \
    --quiet

echo "=== Setup & Deployment Complete! ==="
echo "The system is now live in project: $PROJECT_ID"
echo "You can monitor logs at: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
