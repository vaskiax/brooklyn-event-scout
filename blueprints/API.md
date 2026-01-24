# API.md: NEIS API Documentation

#### **Overview**
The NEIS API provides access to real-time events, weather alerts, and transit status for New York City businesses. It follows RESTful principles and returns JSON payloads.

#### **Endpoints**
*   `GET /v1/alerts`
    *   **Description:** Returns active weather and transit alerts.
    *   **Parameters:** `location` (neighborhood name), `severity` (low|med|high).
    *   **Response:** List of alert objects with source, description, and impact level.

*   `GET /v1/events/upcoming`
    *   **Description:** Lists events in the next 7 days.
    *   **Parameters:** `venue` (ProspectPark|NYRR), `min_impact` (integer 1-5).
    *   **Response:** Event details including timestamp, venue, and attendance estimates.

*   `GET /v1/impact/today`
    *   **Description:** Provides a summary "Foot Traffic Impact Score" for the current day.
    *   **Response:** `{ "date": "2026-01-25", "total_score": 42, "summary": "High impact due to NYRR Race and snow alert." }`

#### **Usage Examples**
```python
import httpx
response = httpx.get("http://localhost:8000/v1/alerts?location=ProspectPark")
print(response.json())
```
