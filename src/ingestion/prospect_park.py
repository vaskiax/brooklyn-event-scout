import time
import re
from typing import List
from datetime import datetime
from seleniumbase import Driver
from bs4 import BeautifulSoup
from ..models.event import Event
from ..utils.normalization import normalize_iso_format, strip_html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProspectParkCollector:
    URL = "https://www.prospectpark.org/events/"

    async def fetch_events(self) -> List[Event]:
        events = []
        driver = None
        try:
            print("[ProspectPark] Initializing SeleniumBase Driver (UC Mode)...")
            # Headless mode can sometimes be detected more easily, but UC mode handles it well usually.
            # Using headless=True for background execution.
            driver = Driver(uc=True, headless=True)
            
            print(f"[ProspectPark] Navigating to {self.URL}")
            # uc_open_with_reconnect helps with stability
            driver.uc_open_with_reconnect(self.URL, reconnect_time=6)
            
            # Smart CAPTCHA handling - specifically looking for Turnstile
            print("[ProspectPark] Checking for Turnstile (Cloudflare)...")
            try:
                driver.uc_gui_click_captcha()
                print("[ProspectPark] Captcha check completed.")
            except Exception:
                print("[ProspectPark] No interactive captcha found or click failed (might not be present).")
            
            print("[ProspectPark] Waiting for event list...")
            try:
                # Wait for the main event container
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tribe-events-calendar-list"))
                )
            except Exception:
                print("[ProspectPark] Timeout waiting for calendar list. Dumping page source for debug.")
                # If we fail, maybe we are blocked.
                debug_html = driver.get_page_source()
                with open("prospect_park_sb_debug.html", "w", encoding="utf-8") as f:
                    f.write(debug_html)
                return []

            # Scroll to load more if lazy loaded (good practice)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) 
            
            # Take screenshot of the full event list
            print("[ProspectPark] Saving screenshot of event list...")
            driver.save_screenshot("prospect_park_live_verification.png")
            
            html = driver.get_page_source()
            soup = BeautifulSoup(html, "html.parser")
            
            # Parse events
            # Selector based on standard Tribe Events Calendar structure
            event_items = soup.select(".tribe-events-calendar-list__event-row")
            print(f"[ProspectPark] Found {len(event_items)} event rows.")
            
            for item in event_items:
                try:
                    # Title
                    title_elem = item.select_one(".tribe-events-calendar-list__event-title h3 a")
                    # Fallback selectors
                    if not title_elem:
                         title_elem = item.select_one(".tribe-events-calendar-list__event-title a")
                    
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Event"
                    link = title_elem['href'] if title_elem else ""
                    
                    # Date/Time
                    # Usually inside .tribe-event-date-start or similar
                    time_elem = item.select_one(".tribe-event-date-start")
                    time_text = time_elem.get_text(strip=True) if time_elem else ""
                    
                    # Parsing date - Tribe usually has format like "January 24 @ 8:00 am - 5:00 pm"
                    start_time = datetime.now() # Fallback
                    if time_text:
                        # Simple Regex try for Month DD
                        date_match = re.search(r'([A-Z][a-z]+ \d{1,2})', time_text)
                        if date_match:
                            # We need to add year, assuming current or next year based on current month
                            current_year = datetime.now().year
                            date_str = f"{date_match.group(1)} {current_year}"
                            try:
                                parsed_date = datetime.strptime(date_str, "%B %d %Y")
                                # Logic to handle year rollover could go here
                                start_time = parsed_date
                            except:
                                pass

                    # Description
                    desc_elem = item.select_one(".tribe-events-calendar-list__event-description")
                    desc = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    events.append(Event(
                        title=title,
                        description=desc,
                        venue="Prospect Park",
                        source="ProspectPark.org (SeleniumBase)",
                        start_time=start_time,
                        raw_data={"url": link, "time_text": time_text},
                        impact_score=3
                    ))
                except Exception as e:
                    print(f"[ProspectPark] Error parsing item: {e}")
                    
        except Exception as e:
            print(f"[ProspectPark] SeleniumBase Error: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return events
