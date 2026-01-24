import asyncio
import csv
from datetime import datetime
from .ingestion.mta import MTAConnector
from .ingestion.weather import WeatherConnector
from .ingestion.nyrr import NYRRCollector
from .ingestion.prospect_park import ProspectParkCollector

async def run_demo():
    print("=== Starting Event-Driven Alerts Ingestion Demo ===\n")
    
    all_events = []
    
    # 1. MTA Alerts
    print("[MTA] Fetching alerts...")
    mta = MTAConnector()
    mta_alerts = await mta.get_all_transit_alerts()
    print(f"Found {len(mta_alerts)} transit alerts.")
    for a in mta_alerts[:3]:
        print(f" - {a.severity}: {a.headline[:100]}...")

    # 2. Weather Alerts
    print("\n[Weather] Fetching active alerts...")
    weather = WeatherConnector()
    weather_alerts = await weather.fetch_active_alerts()
    print(f"Found {len(weather_alerts)} weather alerts.")
    for a in weather_alerts[:3]:
        print(f" - {a.severity}: {a.headline[:100]}...")

    # 3. NYRR Races
    print("\n[NYRR] Fetching upcoming races (API-based)...")
    nyrr = NYRRCollector()
    races = await nyrr.fetch_upcoming_races()
    print(f"Found {len(races)} upcoming races.")
    for r in races[:3]:
        # Handle if start_time is a string or datetime
        time_str = r.start_time.strftime("%Y-%m-%d") if isinstance(r.start_time, datetime) else str(r.start_time)
        print(f" - {time_str}: {r.title}")
    all_events.extend(races)

    # 4. Prospect Park (NYC Open Data API)
    print("\n[ProspectPark] Fetching events from Official NYC Parks API...")
    pp = ProspectParkCollector()
    pp_events = await pp.fetch_events()
    print(f"Found {len(pp_events)} events.")
    for e in pp_events[:3]:
        time_str = e.start_time.strftime("%Y-%m-%d") if isinstance(e.start_time, datetime) else str(e.start_time)
        print(f" - {time_str}: {e.title}")
    all_events.extend(pp_events)

    # Export to CSV as requested
    if all_events:
        csv_file = "extracted_events.csv"
        print(f"\n[Export] Saving {len(all_events)} events to {csv_file}...")
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Start Time", "Venue", "Impact Score"])
            for event in all_events:
                time_str = event.start_time.strftime("%Y-%m-%d %H:%M") if isinstance(event.start_time, datetime) else str(event.start_time)
                writer.writerow([event.source, event.title, time_str, event.venue, event.impact_score])
        print("Export complete.")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(run_demo())
