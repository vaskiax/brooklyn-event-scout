# SYSTEM_DESIGN.md: System Architecture

#### **Strategic Introduction**
The system is designed as a modular, event-driven architecture that separates data acquisition from processing and delivery. This ensures high availability and resilience against changes in source website structures or API rate limits.

#### **General Architecture**
*   **Upper Level:** NYC Event Intelligence System (NEIS).
*   **Core Components:**
    *   **Data Acquisition Layer (DAL):** Responsible for fetching data from diverse sources (Scrapers, API clients).
    *   **Intelligence Processor (IP):** Cleanses data and calculates the "Impact Score" based on event type, size, and location.
    *   **Distribution Gateway (DG):** Serves the dashboard UI and manages notification delivery.
*   **Fundamental Mechanisms:** Persistent storage (PostgreSQL/SQLite), Cron-based scheduling, and Playwright for anti-bot scraping.

#### **Key Component Analysis**
*   **ProspectParkScraper:** Uses `Playwright` with `stealth` plugins to bypass Cloudflare challenges. It monitors `prospectpark.org/events/list/`.
*   **NYRRDirectFeed:** A specialized client that queries the Hakuapp widget API directly, bypassing the need for complex DOM parsing of the race calendar.
*   **Impact Scoring Engine:** A logic module that assigns weights to events (e.g., a 10K race has a higher impact score than a bird-watching tour).

#### **Mandatory Design Patterns**
*   **Scraper Pattern:** All data collectors must implement a common interface for easy expansion to new sources.
*   **Observer Pattern:** The system notifies the Distribution Gateway whenever a high-impact alert is generated.
