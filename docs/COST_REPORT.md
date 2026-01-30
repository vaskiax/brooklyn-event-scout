# Cost Report: Event-Driven Alerts (GCP Gen 2)

This document provides a definitive breakdown of the monthly operating costs for the production environment on Google Cloud Platform.

## 1. Cost Summary

| Service | Category | Monthly Cost (Est.) | Status |
| :--- | :--- | :--- | :--- |
| **Cloud Functions (Gen 2)** | Compute & Execution | $0.00 | **Free Tier** |
| **Cloud Scheduler** | Automation Trigger | $0.00 | **Free Tier** |
| **Secret Manager** | Security & Credentials | $0.06 | Managed |
| **Artifact Registry** | Container Storage | $0.00 | **Free Tier** |
| **Cloud Build** | Deployment & Updates | $0.00 | **Free Tier** |
| **Cloud Logging** | Observability | $0.00 | **Free Tier** |
| **TOTAL** | | **$0.06 / Month** | |

---

## 2. Detailed Service Analysis

### Cloud Functions (Gen 2)
- **Architecture**: Serverless execution on Cloud Run.
- **Usage**: 4 runs/month (Weekly schedule).
- **Free Tier Eligibility**: Includes 2 million requests and significant compute time (400,000 GB-seconds). Our usage (totaling ~120 seconds/month) is well within this limit.

### Cloud Scheduler
- **Config**: 1 active job (`weekly-ingestion`).
- **Policy**: Google provides **3 free jobs** per project per month. 

### Secret Manager
- **Usage**: 1 secret (`SMTP_PASSWORD`) with 1 active version.
- **Cost**: $0.06 per active version/month. This is the only recurring fixed cost.

### Artifact Registry & Cloud Build
- **Storage**: The container image for the function is approximately 150MB. Google provides **0.5 GB free storage**.
- **Builds**: Cloud Build provides **2,500 build-minutes free** per month. Each redeploy takes ~3 minutes.

---

## 3. Scalability Impact
If the report frequency is increased to **Daily**:
- **Cloud Functions**: Still $0.00 (30 requests < 2,000,000).
- **Scheduler**: Still $0.00.
- **Secret Manager**: $0.06.
- **Total**: Still **$0.06 / Month**.

## 4. Conclusion
The infrastructure has been optimized for "Near-Zero Cost." The project maintains maximum reliability and security (AES-256 secret encryption) for less than **$1.00 per year**.
