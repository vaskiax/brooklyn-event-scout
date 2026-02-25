# PowerShell automation for Event-Driven Alerts
# Deploys the ingestion engine as a Cloud Run Job and schedules it weekly.

# Helpers -------------------------------------------------------------------
function Get-EnvValue($key) {
    if (Test-Path ".env") {
        $line = Get-Content ".env" | Select-String -Pattern "^$key="
        if ($line) {
            return $line.ToString().Split("=")[1].Trim()
        }
    }
    return $null
}

# gather configuration ------------------------------------------------------
# read from .env; allow either GCP_PROJECT_ID or old PROJECT_ID name
$projectId = Get-EnvValue "GCP_PROJECT_ID"
if (-not $projectId) {
    $projectId = Get-EnvValue "PROJECT_ID"  # legacy variable name
}
if (-not $projectId) {
    # final fallback -- prompt only if nothing set in file
    $projectId = Read-Host "Enter your Google Cloud Project ID"
}

$billingAccountId = Get-EnvValue "GCP_BILLING_ACCOUNT_ID"
if (-not $billingAccountId) {
    $billingAccountId = Get-EnvValue "BILLING_ACCOUNT_ID"  # alternate key
}
if (-not $billingAccountId) {
    $billingAccountId = Read-Host "Enter your Billing Account ID (e.g. 01A2B3-4C5D6E-7F8G9H)"
}

$region = Get-EnvValue "GCP_REGION"
if (-not $region) { $region = "us-central1" }

$serviceName = "event-ingestion-engine"
$repoName    = "event-alerts"
$jobName     = "weekly-ingestion"

Write-Host "Using Project ID: $projectId" -ForegroundColor Yellow
Write-Host "Using Billing Account ID: $billingAccountId" -ForegroundColor Yellow
Write-Host "Region: $region" -ForegroundColor Yellow

Write-Host "--- Authentication ---" -ForegroundColor Cyan
# Prefer service account key for unattended deployments if GOOGLE_APPLICATION_CREDENTIALS is set
$svcKey = Get-EnvValue "GOOGLE_APPLICATION_CREDENTIALS"
if ($svcKey -and (Test-Path $svcKey)) {
    Write-Host "Using service account key for authentication ("$svcKey")." -ForegroundColor Cyan
    gcloud auth activate-service-account --key-file=$svcKey --project=$projectId
} else {
    Write-Host "No service account key found; performing interactive login." -ForegroundColor Yellow
    gcloud auth login
    gcloud config set project $projectId
}

# link billing --------------------------------------------------------------
Write-Host "Linking billing account..."
gcloud billing projects link $projectId --billing-account $billingAccountId

# enable APIs ---------------------------------------------------------------
Write-Host "Enabling required APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudscheduler.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com logging.googleapis.com --project $projectId

Start-Sleep -Seconds 5

# create artifact registry -------------------------------------------------
Write-Host "Creating Artifact Registry repo (ignore if exists)..."
gcloud artifacts repositories create $repoName --repository-format=docker --location=$region --project $projectId 2>$null

# build & push container ---------------------------------------------------
Write-Host "Building and pushing container via Cloud Build..."
gcloud builds submit --tag "$region-docker.pkg.dev/$projectId/$repoName/engine:latest" --project $projectId

# prepare environment variable string -------------------------------------
$envVars = @()
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $envVars += $line
        }
    }
}
$envVarsString = $envVars -join ","

# ensure SMTP_PASSWORD secret ------------------------------------------------
$smtpSecretExists = gcloud secrets list --filter="name=SMTP_PASSWORD" --project $projectId --format="value(name)"
if (-not $smtpSecretExists) {
    Write-Host "Creating SMTP_PASSWORD secret in Secret Manager..."
    $smtp = Read-Host "Enter your SMTP App Password (will be hidden)" -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtp))
    $b | gcloud secrets create SMTP_PASSWORD --data-file=- --project $projectId
}

# create or update Cloud Run job -------------------------------------------
$jobExists = gcloud run jobs list --filter="name:$jobName" --format="value(name)" --region $region --project $projectId
if ($jobExists) {
    Write-Host "Job exists, updating image/env vars..."
    gcloud run jobs update $jobName `
        --image "$region-docker.pkg.dev/$projectId/$repoName/engine:latest" `
        --region $region `
        --set-env-vars "$envVarsString" `
        --project $projectId
} else {
    Write-Host "Creating new Cloud Run job..."
    gcloud run jobs create $jobName `
        --image "$region-docker.pkg.dev/$projectId/$repoName/engine:latest" `
        --region $region `
        --set-env-vars "$envVarsString" `
        --project $projectId
}

# schedule the job ---------------------------------------------------------
Write-Host "Creating Cloud Scheduler trigger (weekly on Monday 8 AM)..."
# delete existing to avoid duplicates
gcloud scheduler jobs delete "${jobName}-trigger" --location=$region --project=$projectId --quiet 2>$null

$uri = "https://$region-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$projectId/jobs/$jobName:run"

gcloud scheduler jobs create http "${jobName}-trigger" `
    --schedule="0 8 * * 1" `
    --uri="$uri" `
    --http-method=POST `
    --oauth-service-account-email="$projectId@appspot.gserviceaccount.com" `
    --location=$region `
    --project $projectId

Write-Host "--- Deployment Complete ---" -ForegroundColor Green
Write-Host "- Your .env variables have been injected into the Cloud Run job."
Write-Host "- Check the Cloud Scheduler console if the job doesn't appear immediately."
Write-Host "- Configure any OAuth consent screens manually if you use Gmail API."