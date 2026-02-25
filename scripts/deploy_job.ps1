# Automation Script for Google Cloud Project Deployment (Cloud Run Jobs)
# This script reads from .env, enables APIs, and deploys a Dockerized Cloud Run Job.

function Get-EnvValue($key) {
    if (Test-Path ".env") {
        $line = Get-Content ".env" | Select-String -Pattern "^$key="
        if ($line) {
            return $line.ToString().Split("=")[1].Trim()
        }
    }
    return $null
}

$projectId = Get-EnvValue "PROJECT_ID"
if (-not $projectId) { $projectId = Read-Host "Enter your Google Cloud Project ID" }

Write-Host "Using Project ID: $projectId (From .env)" -ForegroundColor Yellow

# Wait for local token generation if missing
if (-not (Test-Path "token.json")) {
    Write-Host "token.json not found! You must authenticate locally first for the calendar." -ForegroundColor Red
    Write-Host "Running the auth script now..."
    .\venv\Scripts\python scripts\init_calendar_auth.py
}

Write-Host "--- Initializing Deployment for GCP Project: $projectId (CLOUD RUN JOBS) ---" -ForegroundColor Cyan

$billingAccountId = Get-EnvValue "GCP_BILLING_ACCOUNT_ID"
if ($billingAccountId) {
    Write-Host "Linking billing account..."
    gcloud billing projects link $projectId --billing-account $billingAccountId --quiet 2>$null
}

# Enable APIs
Write-Host "Enabling APIs (Cloud Run, Cloud Scheduler, Secret Manager, Cloud Build, Artifact Registry)..."
gcloud services enable `
    run.googleapis.com `
    cloudscheduler.googleapis.com `
    secretmanager.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    logging.googleapis.com `
    --project=$projectId --quiet

# Create Service Account
$SaName = "event-alerts-sa"
$FullSaEmail = "$SaName@$projectId.iam.gserviceaccount.com"
$saExists = gcloud iam service-accounts list --filter="email:$FullSaEmail" --format="value(email)" --project=$projectId
if (-not $saExists) {
    Write-Host "Creating Service Account: $SaName..."
    gcloud iam service-accounts create $SaName --display-name="Event Alerts SA" --project=$projectId
}

# Assign Roles
Write-Host "Configuring Permissions..." -ForegroundColor Yellow
$roles = @("roles/secretmanager.secretAccessor", "roles/run.invoker", "roles/logging.logWriter")
foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $projectId --member="serviceAccount:$FullSaEmail" --role=$role --quiet | Out-Null
}

# Setup Secret
Write-Host "Configuring Secrets..." -ForegroundColor Yellow
$smtpVal = Get-EnvValue "SMTP_PASSWORD"
$secretExists = gcloud secrets versions access latest --secret=SMTP_PASSWORD --project=$projectId --quiet 2>$null
if (-not $secretExists) {
    if (-not $smtpVal) {
        $smtpVal = Read-Host "Error: SMTP_PASSWORD missing in .env. Enter App Password"
    }
    Write-Output $smtpVal | gcloud secrets create SMTP_PASSWORD --data-file=- --project=$projectId --quiet
    gcloud secrets add-iam-policy-binding SMTP_PASSWORD `
        --member="serviceAccount:$FullSaEmail" `
        --role="roles/secretmanager.secretAccessor" `
        --project=$projectId --quiet
}

# Gather env vars
$smtpUser = Get-EnvValue "SMTP_USER"
$senderEmail = Get-EnvValue "SENDER_EMAIL"
$stakeholderEmail = Get-EnvValue "STAKEHOLDER_EMAIL"
$notificationsEnabled = Get-EnvValue "NOTIFICATIONS_ENABLED"
# Deploy HTTP Function (Gen 2)
$ServiceName = "event-ingestion-engine"
$Region = "us-central1"
$JobName = "event-ingestion-job"
$DockerImage = "gcr.io/${projectId}/${JobName}:latest".ToLower()

# Build Image
Write-Host "Building Docker Image on Cloud Build... This will take a few minutes." -ForegroundColor Yellow
gcloud builds submit --tag $DockerImage --project=$projectId --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Container build failed." -ForegroundColor Red
    exit 1
}

# Create or Update Cloud Run Job
Write-Host "Deploying Cloud Run Job..." -ForegroundColor Yellow
$jobExists = gcloud run jobs describe $JobName --region=$Region --project=$projectId --quiet 2>$null
if ($jobExists) {
    gcloud run jobs update $JobName `
        --image=$DockerImage `
        --region=$Region `
        --project=$projectId `
        --service-account=$FullSaEmail `
        --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USER=$smtpUser,SENDER_EMAIL=$senderEmail,STAKEHOLDER_EMAIL=$stakeholderEmail,NOTIFICATIONS_ENABLED=$notificationsEnabled" `
        --set-secrets="SMTP_PASSWORD=SMTP_PASSWORD:latest" `
        --quiet
}
else {
    gcloud run jobs create $JobName `
        --image=$DockerImage `
        --region=$Region `
        --project=$projectId `
        --service-account=$FullSaEmail `
        --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USER=$smtpUser,SENDER_EMAIL=$senderEmail,STAKEHOLDER_EMAIL=$stakeholderEmail,NOTIFICATIONS_ENABLED=$notificationsEnabled" `
        --set-secrets="SMTP_PASSWORD=SMTP_PASSWORD:latest" `
        --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Job deployment failed." -ForegroundColor Red
    exit 1
}

Write-Host "Deployed Cloud Run Job successfully!" -ForegroundColor Green

# Create Scheduler Trigger
Write-Host "Updating Cloud Scheduler trigger to point to Cloud Run Job (Weekly on Mondays at 8AM)..."
gcloud scheduler jobs delete "weekly-ingestion-job" --location=$Region --project=$projectId --quiet 2>$null
# Triggers for Jobs use different API path
gcloud scheduler jobs create http "weekly-ingestion-job" `
    --schedule="0 8 * * 1" `
    --uri="https://${Region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${projectId}/jobs/${JobName}:run" `
    --http-method=POST `
    --location=$Region `
    --project=$projectId `
    --time-zone="America/New_York" `
    --oauth-service-account-email=$FullSaEmail --quiet

Write-Host "--- Deployment Complete ---" -ForegroundColor Green
Write-Host "To execute now: gcloud run jobs execute $JobName --region=$Region --project=$projectId" -ForegroundColor Cyan
