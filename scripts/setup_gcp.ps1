# PowerShell RECOVERY Script: HTTP TRIGGER Edition

param (
    [Parameter(Mandatory = $true)]
    [string]$ProjectId
)

$Region = "us-central1"
$ServiceName = "event-ingestion-engine"
$SaName = "event-alerts-sa"
$FullSaEmail = "$SaName@$ProjectId.iam.gserviceaccount.com"

Write-Host "=== FINAL HTTP RECOVERY: $ProjectId ===" -ForegroundColor Cyan

# Force local gcloud configuration
gcloud config set project $ProjectId --quiet

# 1. Enable APIs
Write-Host "[1/4] Enabling APIs..." -ForegroundColor Yellow
gcloud services enable `
    cloudfunctions.googleapis.com `
    cloudscheduler.googleapis.com `
    secretmanager.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    logging.googleapis.com `
    --project=$ProjectId --quiet

# 2. Setup Service Account Roles
Write-Host "[2/4] Configuring Permissions..." -ForegroundColor Yellow
$roles = @("roles/secretmanager.secretAccessor", "roles/run.invoker", "roles/cloudfunctions.invoker", "roles/logging.logWriter")
foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$FullSaEmail" --role=$role --quiet | Out-Null
}

# 3. Setup Secret & SMTP (Fast Path)
Write-Host "[3/4] Configuring Secrets..." -ForegroundColor Yellow
$smtpPass = gcloud secrets versions access latest --secret=SMTP_PASSWORD --project=$ProjectId --quiet 2>$null
if (-not $smtpPass) {
    $smtpPass = Read-Host "Error: SMTP Secret missing. Enter App Password"
    Write-Output $smtpPass | gcloud secrets create SMTP_PASSWORD --data-file=- --project=$ProjectId --quiet
}

$smtpUser = "jorgeandreyg@gmail.com" # Sticking to what worked in context
$stakeholderEmail = $smtpUser

# 4. Deploy HTTP Function
Write-Host "[4/4] Deploying HTTP Function (Gen 2)..." -ForegroundColor Yellow
gcloud functions deploy $ServiceName `
    --project=$ProjectId --gen2 --runtime=python310 --region=$Region `
    --trigger-http --allow-unauthenticated --entry-point=cloud_function_entry `
    --service-account=$FullSaEmail --source=. `
    --set-env-vars="SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,SMTP_USER=$smtpUser,SENDER_EMAIL=$smtpUser,STAKEHOLDER_EMAIL=$stakeholderEmail,NOTIFICATIONS_ENABLED=true" `
    --set-secrets="SMTP_PASSWORD=SMTP_PASSWORD:latest" --quiet

# Verification
$functionUrl = gcloud functions describe $ServiceName --project=$ProjectId --region=$Region --gen2 --format="value(serviceConfig.uri)"

Write-Host "`n--- FINAL TEST ---" -ForegroundColor Cyan
Write-Host "Triggering the Function via HTTP POST NOW..." -ForegroundColor Yellow
try {
    # Using POST to be 100% sure the framework accepts it
    $response = Invoke-RestMethod -Uri $functionUrl -Method Post -ContentType "application/json" -Body '{}'
    Write-Host "Cloud Success: $response" -ForegroundColor Green
    Write-Host "`nSUCCESS! Check your email ($stakeholderEmail) NOW. It should be there in seconds." -ForegroundColor Green
} catch {
    Write-Host "Error triggering: $_" -ForegroundColor Red
    Write-Host "Check logs: gcloud functions logs read $ServiceName --project=$ProjectId --gen2 --limit=20" -ForegroundColor Gray
}

# Create Scheduler (Ensures future runs)
gcloud scheduler jobs delete "weekly-ingestion-job" --location=$Region --project=$ProjectId --quiet 2>$null
gcloud scheduler jobs create http "weekly-ingestion-job" `
    --schedule="0 8 * * 1" --uri=$functionUrl --http-method=POST --location=$Region --project=$ProjectId `
    --time-zone="America/New_York" --oidc-service-account-email=$FullSaEmail --quiet
