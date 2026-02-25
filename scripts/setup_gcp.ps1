# Automation Script for Google Cloud Project Deployment (Cloud Functions Gen 2)
# This script reads from .env, authenticates the user, enables APIs, and deploys the function.

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

Write-Host "--- Authentication ---" -ForegroundColor Cyan
Write-Host "Please login to your Google Cloud account in the browser window that will open."
gcloud auth login

Write-Host "Please authenticate Application Default Credentials. This allows local scripts/deployments to run properly."
gcloud auth application-default login

Write-Host "Setting project context to: $projectId"
gcloud config set project $projectId

Write-Host "--- Initializing Deployment for GCP Project: $projectId ---" -ForegroundColor Cyan

$billingAccountId = Get-EnvValue "GCP_BILLING_ACCOUNT_ID"
if (-not $billingAccountId) { $billingAccountId = Read-Host "Enter your Billing Account ID (e.g. 01A2B3-4C5D6E-7F8G9H)" }

Write-Host "Linking billing account..."
gcloud billing projects link $projectId --billing-account $billingAccountId

# Enable APIs
Write-Host "Enabling APIs (Cloud Functions, Cloud Scheduler, Secret Manager, Cloud Build, Cloud Run)..."
gcloud services enable `
    cloudfunctions.googleapis.com `
    cloudscheduler.googleapis.com `
    secretmanager.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    logging.googleapis.com `
    --project=$projectId --quiet

Write-Host "Waiting 15 seconds for API enablement to propagate in GCP..."
Start-Sleep -Seconds 15

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
$roles = @("roles/secretmanager.secretAccessor", "roles/run.invoker", "roles/cloudfunctions.invoker", "roles/logging.logWriter")
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
    else {
        Write-Host "Creating SMTP_PASSWORD secret from .env..."
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

Write-Host "Deploying Gen 2 Cloud Function... This will take a couple of minutes." -ForegroundColor Yellow
gcloud functions deploy $ServiceName `
    --project=$projectId --gen2 --runtime=python310 --region=$Region `
    --trigger-http --allow-unauthenticated --entry-point=cloud_function_entry `
    --service-account=$FullSaEmail --source=. `
    --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USER=$smtpUser,SENDER_EMAIL=$senderEmail,STAKEHOLDER_EMAIL=$stakeholderEmail,NOTIFICATIONS_ENABLED=$notificationsEnabled" `
    --set-secrets="SMTP_PASSWORD=SMTP_PASSWORD:latest" --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed. Check error above." -ForegroundColor Red
    exit 1
}

$functionUrl = gcloud functions describe $ServiceName --project=$projectId --region=$Region --gen2 --format="value(serviceConfig.uri)"
Write-Host "Deployed successfully! Function URL: $functionUrl" -ForegroundColor Green

# Create Scheduler Trigger
Write-Host "Creating Cloud Scheduler trigger (Weekly on Mondays at 8AM)..."
gcloud scheduler jobs delete "weekly-ingestion-job" --location=$Region --project=$projectId --quiet 2>$null
gcloud scheduler jobs create http "weekly-ingestion-job" `
    --schedule="0 8 * * 1" `
    --uri=$functionUrl `
    --http-method=POST `
    --location=$Region `
    --project=$projectId `
    --time-zone="America/New_York" `
    --oidc-service-account-email=$FullSaEmail --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "--- Deployment Complete ---" -ForegroundColor Green
}
else {
    Write-Host "Scheduler creation skipped or requires manual intervention." -ForegroundColor Yellow
}
