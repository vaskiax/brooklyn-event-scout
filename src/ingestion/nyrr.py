import asyncio
import json
from typing import List
from playwright.async_api import async_playwright, Response
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from ..models.event import Event
from ..utils.normalization import normalize_iso_format, strip_html
from datetime import datetime

class NYRRCollector:
    CALENDAR_URL = "https://www.nyrr.org/run/race-calendar"
    API_FILTER = "https://widget.hakuapp.com/v2/event_lists"

    async def fetch_upcoming_races(self) -> List[Event]:
        events = []
        captured_json = None
        captured_html = None

        async def handle_response(response: Response):
            nonlocal captured_json, captured_html
            if self.API_FILTER in response.url and response.status == 200:
                try:
                    # Attempt to get JSON
                    captured_json = await response.json()
                    print(f"[NYRR] Intercepted JSON response from {response.url[:50]}...")
                except Exception:
                    # If not JSON, try text/HTML
                    try:
                        captured_html = await response.text()
                        print(f"[NYRR] Intercepted HTML response from {response.url[:50]}...")
                    except Exception as e:
                        print(f"[NYRR] Failed to capture response body: {e}")

        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            page.on("response", handle_response)
            
            try:
                print(f"[NYRR] Navigating to {self.CALENDAR_URL}...")
                # Use 'domcontentloaded' to avoid waiting for every single tracker/image
                await page.goto(self.CALENDAR_URL, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for the Haku widget target to exist
                print("[NYRR] Waiting for widget container...")
                try:
                    await page.wait_for_selector(".haku-widget-target", timeout=20000)
                except Exception:
                    print("[NYRR] Widget container not found, scrolling to trigger...")
                
                # Scroll to ensure widget loads
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(5)
                
                if not (captured_json or captured_html):
                    # One more attempt at waiting for ANY haku request if not caught yet
                    print("[NYRR] Data still not captured, waiting a bit longer...")
                    await asyncio.sleep(10)

                if captured_json:
                    entries = captured_json if isinstance(captured_json, list) else captured_json.get("data", [])
                    for item in entries:
                        events.append(self._parse_json_event(item))
                elif captured_html:
                    events = self._parse_html_events(captured_html)
                else:
                    print("[NYRR] No data intercepted.")

            except Exception as e:
                print(f"[NYRR] Playwright error: {e}")
            finally:
                await browser.close()

        return events

    def _parse_json_event(self, item: dict) -> Event:
        return Event(
            title=item.get("name") or item.get("event_name"),
            description=strip_html(item.get("description", "")),
            start_time=normalize_iso_format(item.get("start_date") or item.get("date")),
            end_time=normalize_iso_format(item.get("end_date")),
            venue=item.get("venue_name") or "NYC / Central Park",
            source="NYRR",
            raw_data=item,
            impact_score=4
        )

    def _parse_html_events(self, html: str) -> List[Event]:
        events = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Specific selectors for NYRR Haku widget as identified by research
        items = soup.find_all(class_='upcoming-race')
        
        for item in items:
            title_elem = item.find(class_='upcoming-race-title')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Date extraction
            date_col = item.find(class_='upcoming-race-date')
            day = ""
            month = ""
            if date_col:
                day_elem = date_col.find(class_='upcoming-race-desktop-day')
                day = day_elem.get_text(strip=True) if day_elem else ""
                
                day_container = date_col.find(class_='upcoming-race-day')
                if day_container:
                    # Often the month is the first <p> in the day container
                    month_p = day_container.find('p')
                    if month_p:
                        # Extract "Jan" from "Jan 25" or "Jan25"
                        # Text might be "Jan25", so just take first 3 chars as month usually 3 letters.
                        raw_text = month_p.get_text(strip=True)
                        month = raw_text[:3] if len(raw_text) >= 3 else raw_text

            # Venue extraction
            venue_elem = item.find(class_='upcoming-race-location')
            venue = venue_elem.get_text(strip=True) if venue_elem else "NYC / Central Park"
            
            # Combine date (assume current or next year)
            current_year = datetime.now().year
            # Logic: If month is earlier than current month, assume next year
            # For simplicity in demo, just use Jan 2026 as per research snippet
            try:
                print(f"[DEBUG] Parsing date: Month='{month}', Day='{day}', Year='{current_year}'")
                date_str = f"{month} {day} {current_year}"
                parsed_date = datetime.strptime(date_str, "%b %d %Y")
            except Exception as e:
                print(f"[NYRR] Date parsing failed for '{date_str}': {e}, using fallback.")
                date_str = "Upcoming"
                parsed_date = datetime.now()

            events.append(Event(
                title=title,
                start_time=parsed_date,
                venue=venue,
                source="NYRR",
                raw_data={"html_snippet": str(item)[:200], "parsed_date": date_str},
                impact_score=4
            ))
        
        if not events and html:
            print("[NYRR] HTML captured but no events parsed. Snippet:", html[:200])
            
        return events
