# TIPS.md: Development Tips and Best Practices

#### **Optimization**
*   **Playwright Wait Strategies:** Always use `wait_for_selector` or `wait_for_load_state` instead of fixed `sleep` to ensure speed and stability.
*   **API Caching:** Cache NWS and MTA responses for 5-10 minutes to stay within rate limits and improve dashboard response time.

#### **Common Pitfalls**
*   **Cloudflare Bans:** Avoid rapid, repetitive requests from the same IP without proper proxy or delay strategies.
*   **Missing Date Fields:** Always implement fallback logic for events with missing or malformed "Time" fields.

#### **Productivity Hacks**
*   **Snapshot Debugging:** Use Playwright's `page.screenshot()` frequently during scraper development to see what the agent is "seeing."
*   **FastAPI Docs:** Utilize the auto-generated Swagger UI at `/docs` for testing API endpoints manually.
