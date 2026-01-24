# SEQUENTIAL_PLAN.md: Sequential Execution Plan

#### **Strategic Introduction**
The project will follow a data-first approach, ensuring reliable source ingestion before building the intelligence and delivery layers.

#### **Project Phases**
1.  **Phase 1: Ingestion Engine:**
    *   Develop `ProspectParkScraper` (Playwright-Stealth).
    *   Develop `NYRRCollector` (Direct Hakuapp API).
    *   Integrate Weather (NWS) and MTA APIs.
2.  **Phase 2: Analytics & Storage:**
    *   Implement database schema for events and alerts.
    *   Develop the "Impact Scoring" logic.
    *   Create daily data reconciliation tasks.
3.  **Phase 3: Dashboard & Alerts:**
    *   Build the FastAPI backend.
    *   Develop the frontend dashboard.
    *   Implement the notification dispatcher (Email/Mock alerts).

#### **Priorities**
*   **Robustness:** Automated retries and failure detection for scrapers.
*   **Resilience:** Handling Cloudflare challenges and API rate limits gracefully.
*   **Actionability:** Ensuring every alert provides clear, non-redundant value to the business.
