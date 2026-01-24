# DEPLOYMENT.md: Production Deployment Guidelines

#### **Strategic Introduction**
Deployment for NEIS emphasizes the "Always-On" nature of the scraping and alerting pipeline.

#### **Deployment Environments**
*   **Development (Local):** Python venv, SQLite, local FastAPI server for logic testing.
*   **Staging:** Identical to production but with limited notification channels for final validation.
*   **Production:** Hosted on a resilient cloud platform (e.g., Railway, Render, or AWS) with automated health checks.

#### **CI/CD Pipeline**
1.  **Build:** Install dependencies (`pip install -r requirements.txt`).
2.  **Test:** Run Scraper Validation and API Integration tests.
3.  **Deploy:** Automatic deployment to production upon successful merge to the `main` branch.

#### **Rollback Strategy**
*   **Database Snapshots:** Daily backups of the event store.
*   **Version Pinning:** All dependencies and scraper logic must be versioned to allow rapid rollback to a stable state if a source site change breaks the parser.
