# Brooklyn Event Scout 

An automated, ultra-resilient data ingestion and notification system designed to monitor and report on sports events, community gatherings, and weather alerts specifically for the **Brooklyn / Prospect Park** area.

## 🚀 Objective

To provide stakeholders  with a local weekly intelligence report. The system overcomes advanced scraping protections to guarantee 100% notification reliability.

## 🛠️ Tech Stack

- **Core**: Python 3.10+
- **Infrastructure**: Google Cloud Platform (Serverless)
  - **Cloud Functions (Gen 2)**: Core logic execution via Cloud Run.
  - **Cloud Scheduler**: Weekly automation trigger.
  - **Secret Manager**: Secure AES-256 storage for SMTP credentials.
  - **Artifact Registry**: Containerized deployment management.
- **Libraries**: `httpx`, `BeautifulSoup4`, `functions-framework`, `aiosmtplib`, `pydantic`.

## 🧠 Key Features & Resilience

- **Resilient Orchestration**: Uses dynamic internal imports and direct event loop management to bypass deployment synchronization lag in serverless environments.
- **Scraping**:
  - **NYRR**: Pure HTTP/BeautifulSoup implementation to avoid browser overhead and bypass Haku widget security.
  - **Prospect Park**: Robust NYC Parks RSS parsing with multiple fallback strategies if feeds are blocked.
- **Guaranteed Population (Fail-Safe)**: Includes a baseline of high-quality, pre-verified recurring events (e.g., major NYRR races, Smorgasburg) to ensure the stakeholder never receives an empty report.
- **Calendar Integration with Reminders**: New events are automatically pushed to the configured Google Calendar. Each entry now includes two pop‑up reminders – one week (7 days) before the start and a second alert one hour prior. The week‑prior offset is configurable via the `CALENDAR_REMINDER_MINUTES` environment variable (default 10080 minutes).
- **Local Filter**: Strict location filtering targeting the Brooklyn sector, excluding non-relevant boroughs.
- **Smart Impact Scoring**: Automated priority assignment (1-5) based on event scale and potential traffic/security disruption.

## 📁 Project Structure

```text
.
├── main.py                 # Cloud Function Entry Point & Orchestration
├── src/
│   ├── ingestion/          # Data Collectors (NYRR, Prospect Park, Weather)
│   ├── models/             # Pydantic Data Models (Standardized Event model)
│   ├── reporting/          # HTML Report Generator & Email Notifier
│   └── utils/              # Data Normalization & Formatting Helpers
├── scripts/                # Infrastructure as Code (GCP Setup)
└── docs/                   # Detailed Service Reports & Guides
```

## ⚙️ Deployment (One-Click IaC)

The system is designed for automated deployment using Google Cloud's Infrastructure-as-Code principles.

### Prerequisites:

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated.
2. A valid GCP Project and Billing Account.

### Automation Script:

A new PowerShell helper lives under `deploy/setup_gcp.ps1`. It builds a container, pushes it to Artifact Registry and creates a Cloud Run Job that runs on a weekly schedule. Environment variables are loaded from your `.env` file and automatically injected into the Cloud Run job. Secrets such as `SMTP_PASSWORD` are stored in Secret Manager.

Run the helper from the project root ( PowerShell 7+ recommended ):

```powershell
# simple invocation – assumes your .env already contains the values below
./deploy/setup_gcp.ps1
```

> **Tip**: ensure `.env` defines either `GCP_PROJECT_ID` *or* the legacy
> `PROJECT_ID` entry, and similarly `GCP_BILLING_ACCOUNT_ID` (or
> `BILLING_ACCOUNT_ID`). The script will silently read those keys; if they are
> present it will **not** prompt for them.
>
> **Non-interactive authentication**
> If you supply a service account JSON file and set
> `GOOGLE_APPLICATION_CREDENTIALS` in `.env`, the script will use
> `gcloud auth activate-service-account` and perform the entire run without
> opening a browser. This makes the deployment fully automated for CI/CD.

The script will:

- Read configuration directly from `.env` (no interactive prompts unless values
  are missing).
- Authenticate with GCP and set the active project.
- Link the billing account (automatic when provided in `.env`).
- Enable required APIs (Cloud Run, Scheduler, Build, Artifact Registry, Secret
  Manager, Logging).
- Create an Artifact Registry repository and build/push the Docker image.
- Inject all variables from `.env` into the Cloud Run job’s environment.
- Create/update a weekly Cloud Scheduler trigger that executes the job.
- Create the `SMTP_PASSWORD` secret in Secret Manager if it doesn't already
  exist.

The older script in `scripts/setup_gcp.ps1` remains as a lightweight recovery tool for HTTP‑trigger deployments, but the new `deploy` helper is the recommended path going forward.

## 📊 Operating Costs

The architecture is optimized for the **GCP Free Tier**.

- **Execution Cost**: $0.00/month.
- **Security Cost**: $0.06/month (Secret Manager).
- **Total**: **~$0.06 USD per month**.

---

*Developed for Advanced Event-Driven Intelligence.*
