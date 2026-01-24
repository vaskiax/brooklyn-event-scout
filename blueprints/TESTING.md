# TESTING.md: Testing Strategy

#### **Strategic Introduction**
Testing in NEIS ensures that changes in website UI or API schemas do not break the critical alerting pipeline.

#### **Test Categories**
*   **Scraper Validation:** Automated unit tests that run scrapers against saved HTML snapshots to ensure parsing logic is still valid.
*   **Data Integrity:** Checks that normalized timestamps are correct and attendance estimates fall within expected ranges.
*   **End-to-End Alerting:** Simulation of a "High Impact" event to verify that the scoring engine and notification gateway trigger correctly.
*   **Integration Tests:** Verifying authentication and response handling for MTA and NWS APIs.

#### **Acceptance Criteria**
*   **Parsing Accuracy:** >98% success rate in extracting event titles and dates from source sites.
*   **Alert Latency:** High-priority alerts must be processed and visible on the dashboard within 5 minutes of data ingestion.
*   **Resilience:** System must gracefully handle 403/Forbidden errors by retrying with different headers or alerting the administrator.
