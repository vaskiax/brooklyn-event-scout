import httpx
from typing import List
from ..models.event import Event
from ..utils.normalization import normalize_iso_format
from datetime import datetime

class WeatherConnector:
    # NYC Zone ID for NWS (e.g., NYZ072 for New York County)
    NWS_ALERTS_API = "https://api.weather.gov/alerts/active?area=NY"

    async def fetch_active_alerts(self) -> List[Event]:
        async with httpx.AsyncClient() as client:
            headers = {"User-Agent": "Event-Driven-Alerts/1.0 (contact@example.com)"}
            try:
                response = await client.get(self.NWS_ALERTS_API, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                events = []
                features = data.get("features", [])
                for feature in features:
                    props = feature.get("properties", {})
                    
                    # Convert Weather Alert to Event for reporting compatibility
                    events.append(Event(
                        title=props.get("headline", "Weather Alert"),
                        description=props.get("description", ""),
                        venue=props.get("areaDesc", "NYC Area"),
                        source="NWS Weather",
                        start_time=normalize_iso_format(props.get("effective")),
                        impact_score=4 if props.get("severity") in ["Extreme", "Severe"] else 3,
                        raw_data={"severity": props.get("severity")}
                    ))
                return events
            except Exception as e:
                print(f"[Weather] Error: {e}")
                return []
