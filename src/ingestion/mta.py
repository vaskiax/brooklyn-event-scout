import httpx
from typing import List
from ..models.event import Alert
from ..utils.normalization import normalize_iso_format
from datetime import datetime

class MTAConnector:
    SUBWAY_JSON = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json"
    BUS_JSON = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fbus-alerts.json"

    async def fetch_alerts(self, endpoint: str) -> List[Alert]:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            entities = data.get("entity", [])
            for entity in entities:
                alert_data = entity.get("alert")
                if not alert_data:
                    continue
                
                # Extracting headline and description
                header_text = alert_data.get("header_text", {}).get("translation", [{}])[0].get("text", "No Headline")
                description_text = alert_data.get("description_text", {}).get("translation", [{}])[0].get("text", "No Description")
                
                # Active periods
                active_periods = alert_data.get("active_period", [])
                start_time = datetime.fromtimestamp(active_periods[0].get("start", 0)) if active_periods else datetime.now()
                end_time = datetime.fromtimestamp(active_periods[0].get("end", 0)) if active_periods and active_periods[0].get("end") else None

                alerts.append(Alert(
                    category="Transit",
                    severity="Med", # Default for now
                    headline=header_text,
                    description=description_text,
                    source="MTA",
                    start_time=start_time,
                    end_time=end_time,
                    affected_areas=[] # Could parse from header_text or alert_data
                ))
            return alerts

    async def get_all_transit_alerts(self) -> List[Alert]:
        subway = await self.fetch_alerts(self.SUBWAY_JSON)
        bus = await self.fetch_alerts(self.BUS_JSON)
        return subway + bus
