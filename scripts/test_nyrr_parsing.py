from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

def test_parsing():
    file_path = "nyrr_playwright_dump.html"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    events = []
    
    # Logic from nyrr.py
    event_containers = soup.select("div.upcoming-event")
    print(f"Found {len(event_containers)} containers with div.upcoming-event")
    
    if not event_containers:
        event_containers = soup.select(".upcoming-race")
        print(f"Fallback found {len(event_containers)} containers with .upcoming-race")

    for container in event_containers:
        start_date_str = container.get("data-start-date")
        title = None
        link = None
        location = container.get("data-location", "New York, NY")
        
        article = container.find("article", class_="upcoming-race")
        if not article:
            article = container

        title_el = article.select_one(".upcoming-race-title")
        if title_el:
            title = title_el.get_text(strip=True)
        
        link_el = article.select_one("a.learn-more-btn")
        if link_el:
            link = link_el["href"]

        if title and link:
            start_time = None
            if start_date_str:
                try:
                    start_time = datetime.strptime(start_date_str, "%Y/%m/%d")
                    time_el = article.select_one(".upcoming-race-time")
                    if time_el:
                        time_str = time_el.get_text(strip=True)
                        try:
                            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                            start_time = datetime.combine(start_time.date(), time_obj)
                        except:
                            pass
                except Exception as e:
                    print(f"Date error: {e}")
            
            print(f"Event: {title} | {start_time} | {location}")
            events.append(title)

    print(f"Total parsed events: {len(events)}")

if __name__ == "__main__":
    test_parsing()
