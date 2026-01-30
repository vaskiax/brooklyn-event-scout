import httpx
from typing import List
from bs4 import BeautifulSoup
from ..models.event import Event
from datetime import datetime
import re

class ProspectParkCollector:
    # Use the Official NYC Parks RSS feed for Prospect Park - 100% serverless friendly
    RSS_URL = "https://www.nycgovparks.org/parks/prospect-park/events/rss"

    async def fetch_events(self) -> List[Event]:
        events = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            print(f"[ProspectPark] Fetching RSS feed: {self.RSS_URL}")
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
                response = await client.get(self.RSS_URL)
                
                if response.status_code != 200:
                    print(f"[ProspectPark] Failed to fetch RSS. Status: {response.status_code}")
                    return []

                # Parse XML
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")
                print(f"[ProspectPark] Found {len(items)} events in RSS feed.")

                for item in items:
                    title = item.find("title").get_text(strip=True) if item.find("title") else "Unknown Event"
                    link = item.find("link").get_text(strip=True) if item.find("link") else ""
                    desc = item.find("description").get_text(strip=True) if item.find("description") else ""
                    
                    # Date parsing from RSS (usually in <pubDate> or description)
                    # NYC Parks RSS often has dates in the description or a custom field
                    start_time = datetime.now()
                    
                    events.append(Event(
                        title=title,
                        description=desc,
                        venue="Prospect Park",
                        source="NYC Parks RSS",
                        start_time=start_time,
                        raw_data={"url": link},
                        impact_score=3
                    ))

        except Exception as e:
            print(f"[ProspectPark] RSS Error: {e}")

        return events
