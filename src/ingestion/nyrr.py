import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from src.ingestion.base import EventCollector
from src.models.event import Event


class NYRRCollector(EventCollector):
    def __init__(self):
        self.url = "https://www.nyrr.org/run/race-calendar"

    async def fetch_events(self) -> List[Event]:
        """
        Dual-strategy NYRR scraper:
          1. PRIMARY — Network Interception: capture the Haku API JSON response
             that contains the raw event data.
          2. FALLBACK — DOM Scraping: parse the fully-rendered HTML using the
             known CSS selectors (div.upcoming-event, .upcoming-race-title, etc.).
        """
        events: List[Event] = []
        captured_json: list = []

        try:
            print(f"[{self.__class__.__name__}] Launching Playwright (network-interception mode)...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                page = await context.new_page()

                # ---- Strategy 1: Intercept network responses ----
                async def _on_response(response):
                    """Capture any JSON that looks like the Haku event feed."""
                    try:
                        url = response.url
                        ct = response.headers.get("content-type", "")
                        # The Haku widget fetches event data from various endpoints.
                        # We look for JSON responses that contain race/event data.
                        if "json" in ct or url.endswith(".json"):
                            body = await response.text()
                            if any(kw in body[:2000] for kw in [
                                "event_name", "race_name", "upcoming",
                                "start_date", "event_lists", "races"
                            ]):
                                try:
                                    data = json.loads(body)
                                    captured_json.append(data)
                                    print(f"[{self.__class__.__name__}] Captured JSON from {url[:80]}...")
                                except json.JSONDecodeError:
                                    pass
                    except Exception:
                        pass  # Some responses may not be readable

                page.on("response", _on_response)

                try:
                    await page.goto(self.url, timeout=60000, wait_until="domcontentloaded")
                    print(f"[{self.__class__.__name__}] Page loaded. Waiting for Haku widget data...")

                    # Give the Haku widget time to fetch its data
                    try:
                        await page.wait_for_selector("div.upcoming-event", timeout=25000)
                        print(f"[{self.__class__.__name__}] DOM events appeared.")
                    except Exception:
                        print(f"[{self.__class__.__name__}] Selector timeout — will rely on intercepted JSON or raw HTML.")

                    # Small extra wait for any trailing XHR
                    await page.wait_for_timeout(3000)

                    # ---------------------------------------------------
                    # Try strategy 1 first: parse intercepted JSON
                    # ---------------------------------------------------
                    if captured_json:
                        events = self._parse_json_feed(captured_json)
                        if events:
                            print(f"[{self.__class__.__name__}] ✓ Extracted {len(events)} events via JSON interception.")

                    # ---------------------------------------------------
                    # Fallback strategy 2: DOM scraping
                    # ---------------------------------------------------
                    if not events:
                        print(f"[{self.__class__.__name__}] JSON empty — falling back to DOM scraping.")
                        content = await page.content()
                        events = self._parse_html(content)
                        if events:
                            print(f"[{self.__class__.__name__}] ✓ Extracted {len(events)} events via DOM scraping.")

                except Exception as e:
                    print(f"[{self.__class__.__name__}] Playwright page error: {e}")
                finally:
                    await browser.close()

        except Exception as e:
            print(f"[{self.__class__.__name__}] Failed to run Playwright: {e}")

        if not events:
            print(f"[{self.__class__.__name__}] ✗ No events found from any strategy.")
        return events

    # ------------------------------------------------------------------
    # JSON feed parser (Strategy 1)
    # ------------------------------------------------------------------
    def _parse_json_feed(self, payloads: list) -> List[Event]:
        """Walk through captured JSON payloads and extract Event objects."""
        events: List[Event] = []
        for payload in payloads:
            items = self._find_event_list(payload)
            for item in items:
                try:
                    title = (
                        item.get("event_name")
                        or item.get("race_name")
                        or item.get("name")
                        or item.get("title")
                    )
                    if not title:
                        continue

                    # Date
                    raw_date = (
                        item.get("start_date")
                        or item.get("date")
                        or item.get("event_date")
                    )
                    start_time = datetime.now()
                    if raw_date:
                        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y"):
                            try:
                                start_time = datetime.strptime(raw_date[:10], fmt)
                                break
                            except ValueError:
                                continue

                    # URL
                    url = item.get("url") or item.get("link") or item.get("slug", "")
                    if url and not url.startswith("http"):
                        url = f"https://events.nyrr.org/{url.lstrip('/')}"
                    if not url:
                        url = self.url

                    # Location
                    location = (
                        item.get("location")
                        or item.get("venue")
                        or item.get("city")
                        or "New York, NY"
                    )

                    events.append(Event(
                        source="NYRR",
                        title=title,
                        description="Scraped via Haku API interception",
                        start_time=start_time,
                        venue=location,
                        raw_data={"url": url},
                    ))
                except Exception as e:
                    print(f"[{self.__class__.__name__}] JSON item parse error: {e}")
        return events

    @staticmethod
    def _find_event_list(obj, depth=0):
        """Recursively search a JSON structure for lists of event-like dicts."""
        if depth > 8:
            return []
        if isinstance(obj, list):
            # Check if this list contains event-like dicts
            if obj and isinstance(obj[0], dict) and any(
                k in obj[0] for k in ("event_name", "race_name", "name", "title", "start_date")
            ):
                return obj
            # Otherwise recurse into list items
            for item in obj:
                result = NYRRCollector._find_event_list(item, depth + 1)
                if result:
                    return result
        elif isinstance(obj, dict):
            for value in obj.values():
                result = NYRRCollector._find_event_list(value, depth + 1)
                if result:
                    return result
        return []

    # ------------------------------------------------------------------
    # DOM scraper (Strategy 2 — known-good selectors from HTML dump)
    # ------------------------------------------------------------------
    def _parse_html(self, content: str) -> List[Event]:
        """Parse fully-rendered HTML using the confirmed CSS selectors."""
        events: List[Event] = []
        soup = BeautifulSoup(content, "html.parser")

        event_containers = soup.select("div.upcoming-event")
        if not event_containers:
            event_containers = soup.select("article.upcoming-race")

        for container in event_containers:
            start_date_str = container.get("data-start-date")
            location = container.get("data-location", "New York, NY")

            article = container.find("article", class_="upcoming-race") or container

            title_el = article.select_one(".upcoming-race-title")
            title = title_el.get_text(strip=True) if title_el else None

            link_el = article.select_one("a.learn-more-btn")
            link = link_el["href"] if link_el else None

            if title and link:
                if not link.startswith("http"):
                    link = "https://www.nyrr.org" + link

                start_time = datetime.now()
                if start_date_str:
                    try:
                        start_time = datetime.strptime(start_date_str, "%Y/%m/%d")
                        time_el = article.select_one(".upcoming-race-time")
                        if time_el:
                            time_str = time_el.get_text(strip=True)
                            try:
                                time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                                start_time = datetime.combine(start_time.date(), time_obj)
                            except ValueError:
                                pass
                    except ValueError as e:
                        print(f"[NYRRCollector] Date parse error: {e}")

                events.append(Event(
                    source="NYRR",
                    title=title,
                    description="Live scraped via Playwright",
                    start_time=start_time,
                    venue=location,
                    raw_data={"url": link},
                ))
        return events
