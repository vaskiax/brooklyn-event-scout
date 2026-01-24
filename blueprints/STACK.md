# STACK.md: Technology Stack Definition

#### **Strategic Introduction**
The stack is selected to prioritize resilience, rapid development, and efficient data handling. Python is chosen for its superior ecosystem in data engineering and web automation.

#### **Languages and Frameworks**

| Component | Allowed Technology/Model |
| --------- | ------------------------- |
| **Backend** | Python 3.11+, FastAPI |
| **Scraping** | Playwright with Playwright-Stealth |
| **Database** | SQLite (MVP) / PostgreSQL (Production) |
| **API Client** | HTTPX (Async HTTP) |
| **Frontend** | React / Tailwind CSS (Dashboard) |

#### **Mathematical Foundations**
*   **Weighted Scoring Logic:** Used for the "Impact Score" calculation (Event Type weight * Attendance factor).
*   **Geo-Spatial Proximity:** Simple Euclidean distance or Manhattan distance calculations for NYC grid relevance.
*   **Time-Series Analysis:** For detecting trends in historical foot traffic data (Phase 2).
