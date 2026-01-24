# DATA_ENGINEERING.md: Data Pipeline & Processing

#### **Strategic Introduction**
The data engineering layer is the heartbeat of the NEIS. It ensures that heterogeneous data from web scrapers and municipal APIs are transformed into a unified, actionable format.

#### **Data Sourcing & Ingestion**
*   **Web Scrapers (Unstructured):** `ProspectParkScraper` targets the Events Calendar plugin on `prospectpark.org`. Extracted data includes title, date range, timing, and venue.
*   **API Connectors (Structured):**
    *   `NYRR_API`: Uses the Hakuapp widget endpoint.
    *   **MTA_GTFS:** Consumes real-time Protocol Buffer (PB) feeds for service status.
    *   **NWS_API:** Fetches JSON-LD weather alerts for NYC.

#### **Data Transformation (ETL)**
1.  **Normalization:** Converting disparate date formats (e.g., "Sunday, Jan 25" vs "01 FEB SUN") into ISO 8601 UTC timestamps.
2.  **Deduplication:** Merging overlapping events from different sources (e.g., a race tagged in both NYRR and a general park calendar).
3.  **Enrichment:** Adding geocoordinates (lat/long) to venues for proximity-based alerting.

#### **Storage & Persistence**
*   **Event Store:** Relational tables for historical and upcoming events.
*   **Alert Buffer:** A cache for active disruptions (Weather, Transit) to prevent notification fatigue.
