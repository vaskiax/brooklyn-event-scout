# FLOW.md: System Logical Flow

#### **Strategic Introduction**
The flow within NEIS moves from external unstructured data to internally structured alerts, terminating in user-facing dashboards and notifications.

#### **Data Processing Flow**
1.  **Trigger:** Scheduled cron jobs (e.g., every 6 hours) activate the Data Acquisition Layer.
2.  **Acquisition:**
    *   `ProspectParkScraper` performs browser-based extraction.
    *   `NYRRCollector` executes API requests.
    *   `WeatherConnector` and `MTAConnector` fetch real-time JSON/PB feeds.
3.  **Transformation:** The IP layer normalizes timestamps and deduplicates entries.
4.  **Analysis:** The "Impact Engine" runs logic to determine the severity based on current and upcoming data.
5.  **Storage:** Clean data is persisted to the database.

#### **Alert/Interaction Flow**
1.  **Monitor:** The DG layer watches for high-impact scores or critical weather/transit alerts.
2.  **Deliver:** Alerts are pushed to the frontend dashboard and dispatched via configured channels (e.g., email service).
3.  **Acknowledge:** Users view the dashboard to understand the day's traffic outlook.
