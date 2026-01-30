# Google Cloud Setup & Deployment Guide

This document explains how to use the automated scripts to deploy the Event-Driven Alerts engine to Google Cloud Platform (GCP).

## 1. Prerequisites
- **Google Cloud SDK**: Install and initialize the [gcloud CLI](https://cloud.google.com/sdk/docs/install).
- **Authentication**: Run `gcloud auth login` and `gcloud auth application-default login`.
- **Billing Account**: You must have a valid billing account set up in GCP.

---

## 2. One-Click Automated Deployment (IaC)
The script `scripts/setup_gcp.sh` handles everything from project creation to final code deployment.

### Steps to Run:
1.  Open your terminal.
2.  Run the following command:
    ```bash
    bash scripts/setup_gcp.sh [CHOOSE_A_NEW_PROJECT_ID]
    ```

> [!IMPORTANT]
> **Choosing a Project ID**:
> - The script will **create a new project** if the ID doesn't exist.
> - **Global Uniqueness**: The ID must be unique across *all* of Google Cloud. If someone else has used it, the script will show an error.
> - **Format**: Use lowercase letters, numbers, and hyphens (e.g., `events-alerts-client-2026`). No spaces.
> - **Check**: If the script says "Project Already Exists," it might be one you already own or a name someone else took. Try adding a random number at the end.
- **Project Creation**: Generates the new GCP project.
- **Billing**: Prompts you to select your existing billing account to activate the project.
- **Security**: Prompts for the SMTP App Password and saves it securely in Secret Manager.
- **Infrastructure**: Enables APIs, creates Service Accounts, and sets up the Scheduler & Pub/Sub.
- **Deployment**: Deploys the Python code directly to Google Cloud Functions.

---

## 3. Post-Deployment Verification
Once the script finishes:
1.  **Check Logs**: Go to Cloud Logging in the GCP Console to see the script execution.
2.  **Test Run**: You can manually trigger the Scheduler job to verify the first report is sent:
    ```bash
    gcloud scheduler jobs run weekly-ingestion-job --project=[PROJECT_ID] --location=us-central1
    ```

## 5. Cost Considerations
Refer to `docs/FINAL_REPORT.md` for a monthly cost breakdown. The system is designed to stay within or near the Free Tier boundaries.
