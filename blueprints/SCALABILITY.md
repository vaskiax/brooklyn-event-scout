# SCALABILITY.md: Scalability and Growth Guide

#### **Strategic Introduction**
The NEIS must be built to handle an increasing number of data sources (more parks, more sports organizations) and a growing user base without degrading performance.

#### **Efficiency Strategies**
*   **Asynchronous Processing:** Use `FastAPI`'s async capabilities and `httpx` to handle multiple API requests and scraper instances in parallel.
*   **Distributed Scraping:** If source volume increases, scrapers should be containerized (Docker) to run on separate nodes, potentially using a queue system like Redis.
*   **Incremental Updates:** Scrapers should focus on new or updated events rather than full calendar re-scans.

#### **Growth Trajectory**
1.  **Phase 1 (MVP):** Focus on Prospect Park and NYRR for NYC.
2.  **Phase 2 (Regional):** Expand to other NYC boroughs and major parks (Central Park, Flushing Meadows).
3.  **Phase 3 (National):** Adapt the framework for other major US cities with similar event densities.
