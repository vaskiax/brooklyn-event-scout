# SECURITY.md: Security Guidelines

#### **Strategic Introduction**
Security in NEIS focuses on the integrity of the data being reported and the protection of the system's endpoints and API keys.

#### **Threat Analysis**
*   **Data Injection:** Risks of malicious actors injecting fake events into source calendars if not verified.
*   **API Key Exposure:** Theft of MTA or NWS credentials if stored insecurely.
*   **Scraper Detection:** Being identified and banned by targets (Prospect Park / Cloudflare).

#### **Mitigation Guidelines**
*   **Environment Variables:** All API keys and sensitive credentials must be stored in `.env` files and never committed to version control.
*   **Rate Limiting:** Implement rate limiting on the NEIS API to prevent DDoS and scraping of own data.
*   **Validation Layer:** Cross-reference event data from multiple sources when possible to verify authenticity.
*   **Headless Stealth:** Use `Playwright-Stealth` and randomized user agents to minimize scraper fingerprinting.
