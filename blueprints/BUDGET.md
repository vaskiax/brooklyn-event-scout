# BUDGET.md: Project Economic Limits

#### **Strategic Introduction**
The project aims for a lean, cost-effective infrastructure that utilizes free-tier APIs and open-source tools where possible.

#### **Cost Optimization Criteria**
*   **Infrastructure:** Host the initial MVP on a low-cost VPS or serverless platform (e.g., Railway, Render) to minimize fixed costs.
*   **API Usage:** Prioritize free government APIs (MTA, NWS). Monitor usage to stay within free tiers if applicable.
*   **Headless Browser Overhead:** Optimize Playwright scripts to run efficiently (e.g., blocking images/videos during scraping) to reduce CPU and memory consumption.
*   **Database:** Start with SQLite for zero-cost storage; migrate to a managed PostgreSQL instance only when traffic justifies the cost.
