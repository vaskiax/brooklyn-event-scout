import httpx
from typing import List
from ..models.event import Alert
from ..utils.normalization import normalize_iso_format
from datetime import datetime

class WeatherConnector:
    # NYC Zone ID for NWS (e.g., NYZ072 for New York County)
    NWS_ALERTS_API = "https://api.weather.gov/alerts/active?area=NY"

    async def fetch_active_alerts(self) -> List[Alert]:
        async with httpx.AsyncClient() as client:
            # NWS requires a User-Agent
            headers = {"User-Agent": "Event-Driven-Alerts/1.0 (contact@example.com)"}
            response = await client.get(self.NWS_ALERTS_API, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            features = data.get("features", [])
            for feature in features:
                props = feature.get("properties", {})
                
                alerts.append(Alert(
                    category="Weather",
                    severity=props.get("severity", "Unknown"),
                    headline=props.get("headline", "Weather Alert"),
                    description=props.get("description", ""),
                    source="NWS",
                    start_time=normalize_iso_format(props.get("effective")),
                    end_time=normalize_iso_format(props.get("ends")) if props.get("ends") else None,
                    affected_areas=[props.get("areaDesc", "")]
                ))
            return alerts
