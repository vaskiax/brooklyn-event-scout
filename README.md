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

Run the following from the root directory:

```powershell
./scripts/setup_gcp.ps1 -ProjectId your-project-id
```

The script will:

- Enable all necessary APIs.
- Create Service Accounts with least-privilege IAM roles.
- Securely prompt for and store your SMTP password.
- Deploy the Cloud Function and configure the Weekly Scheduler.

## 📊 Operating Costs

The architecture is optimized for the **GCP Free Tier**.

- **Execution Cost**: $0.00/month.
- **Security Cost**: $0.06/month (Secret Manager).
- **Total**: **~$0.06 USD per month**.

---

*Developed for Advanced Event-Driven Intelligence.*
