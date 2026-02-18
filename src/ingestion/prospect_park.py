import logging
import asyncio
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup

# Use SeleniumBase for Cloudflare bypass
try:
    from seleniumbase import SB
except ImportError:
    logging.warning("SeleniumBase not installed. Prospect Park collector will fail.")

from src.ingestion.base import EventCollector
from src.models.event import Event

class ProspectParkCollector(EventCollector):
    def __init__(self):
        # The Alliance events events/calendar page
        self.url = "https://www.prospectpark.org/events/list/"
        self.calendar_url = "https://www.prospectpark.org/calendar/"

    async def fetch_events(self) -> List[Event]:
        """
        Prospect Park scraper using SeleniumBase UC Mode to bypass Cloudflare.
        """
        events = []
        loop = asyncio.get_event_loop()
        
        # Run blocking SeleniumBase code in a separate thread to avoid blocking the async loop
        try:
            events = await loop.run_in_executor(None, self._scrape_sync)
        except Exception as e:
            print(f"[{self.__class__.__name__}] SB execution failed: {e}")
            
        if not events:
            print(f"[{self.__class__.__name__}] ✗ No events found via SeleniumBase.")
        return events

    def _scrape_sync(self) -> List[Event]:
        """Synchronous SeleniumBase logic."""
        events = []
        print(f"[{self.__class__.__name__}] Launching SeleniumBase (UC Mode)...")
        
        # Context Manager: SB(uc=True, headless=True)
        # headless2 is often better for UC mode 
        with SB(uc=True, test=True, headless2=True) as sb: 
            # Try primary URL
            try:
                print(f"[{self.__class__.__name__}] Navigate to {self.url}...")
                sb.open(self.url)
                
                # Check for Cloudflare title
                if "Just a moment" in sb.get_title():
                    print(f"[{self.__class__.__name__}] Cloudflare challenge detected. Attempting bypass...")
                    # UC mode handles some automatically. 
                    # If specific iframe:
                    if sb.is_element_visible('iframe[src*="cloudflare"]'):
                        sb.uc_gui_click_captcha()
                
                sb.sleep(5) # Wait for load
                
                # Check for calendar items
                if not sb.is_element_visible(".tribe-events-calendar-list") and \
                   not sb.is_element_visible(".result-item"):
                       pass

                # Debug: Save what we actually see
                sb.save_page_source("pp_debug.html")

                content = sb.get_page_source()
                parsed = self._parse_html(content, self.url)
                if parsed:
                    events.extend(parsed)
                    print(f"[{self.__class__.__name__}] ✓ Extracted {len(parsed)} events from primary URL.")
                    return events

            except Exception as e:
                print(f"[{self.__class__.__name__}] Error on {self.url}: {e}")

            # Try secondary URL if empty
            if not events:
                try:
                    print(f"[{self.__class__.__name__}] Trying secondary {self.calendar_url}...")
                    sb.open(self.calendar_url)
                    sb.sleep(5)
                    content = sb.get_page_source()
                    parsed = self._parse_html(content, self.calendar_url)
                    if parsed:
                        events.extend(parsed)
                        print(f"[{self.__class__.__name__}] ✓ Extracted {len(parsed)} events from calendar URL.")
                except Exception as e:
                    print(f"[{self.__class__.__name__}] Error on {self.calendar_url}: {e}")

        return events

    def _parse_html(self, content: str, base_url: str) -> List[Event]:
        """Parse HTML content using BeautifulSoup (reused logic)."""
        events: List[Event] = []
        soup = BeautifulSoup(content, "html.parser")
        
        cards = soup.select(
            ".tribe-events-calendar-list__event, "
            ".tribe-events-list .type-tribe_events, "
            ".result-item, "
            "article.type-tribe_events, "
            ".tribe-common-g-row"
        )
        
        if not cards:
            cards = soup.select("div[class*='event'], article[class*='event']")

        for card in cards:
            title_el = (
                card.select_one(".tribe-events-calendar-list__event-title a")
                or card.select_one("h3 a, h2 a, .tribe-events-list-event-title a")
                or card.select_one("h3, h4, .title")
            )
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", base_url)
            if not link.startswith("http"):
                link = "https://www.prospectpark.org" + link

            # Date
            start_time = datetime.now()
            date_el = card.select_one(
                ".tribe-events-calendar-list__event-datetime, "
                "time[datetime], "
                ".tribe-event-schedule-details, "
                ".date"
            )
            if date_el:
                dt_attr = date_el.get("datetime")
                if dt_attr:
                    try:
                        start_time = datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
                    except:
                        pass
                else:
                    date_text = date_el.get_text(strip=True)
                    try:
                        parts = date_text.split()
                        if len(parts) >= 2:
                            month = parts[0]
                            day = parts[1].replace(",", "")
                            year = datetime.now().year
                            dt = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
                            if dt < datetime.now():
                                dt = dt.replace(year=year + 1)
                            start_time = dt
                    except:
                        pass

            events.append(Event(
                source="Prospect Park",
                title=title,
                description="Live scraped via SeleniumBase",
                start_time=start_time,
                venue="Prospect Park, Brooklyn",
                raw_data={"url": link},
            ))
            
        return events
