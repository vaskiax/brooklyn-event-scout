import asyncio
import os
import csv
import functions_framework
import sys
from datetime import datetime

VERSION = "3.0.0-PRO-RESILIENT"

async def run_ingestion_pipeline():
    """Main orchestration logic with global imports and redundant fail-safes."""
    print(f"=== PIPELINE START (v{VERSION}) ===")
    
    # 1. Setup Environment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir) # Use insert(0) for priority
    
    all_events = []
    
    # Standard Imports (outside the loop for stability)
    try:
        from src.ingestion.nyrr import NYRRCollector
        from src.ingestion.prospect_park import ProspectParkCollector
        from src.ingestion.weather import WeatherConnector
        from src.models.event import Event
        from src.reporting.report_generator import ReportGenerator
        from src.reporting.notifier import Notifier
        print("[Pipeline] Module setup complete.")
    except Exception as e:
        print(f"[Pipeline] FATAL: Import failure: {e}")
        # Last resort fallback if imports fail entirely
        return []

    # 2. Collector Tasks
    print("[Pipeline] Initiating collectors...")
    tasks = [
        ("NYRR", NYRRCollector().fetch_upcoming_races()),
        ("ProspectPark", ProspectParkCollector().fetch_events()),
        ("Weather", WeatherConnector().fetch_active_alerts()),
    ]
    
    for name, coro in tasks:
        print(f"[Pipeline] Running {name}...")
        try:
            res = await coro
            count = len(res) if res else 0
            print(f"[Pipeline] {name} results: {count}")
            if res:
                all_events.extend(res)
        except Exception as e:
            print(f"[Pipeline] {name} crashed: {e}")

    # 3. Validation & Aggregation
    total = len(all_events)
    print(f"[Pipeline] Total Events Aggregated: {total}")
    
    if total == 0:
        print("[Pipeline] CRITICAL: 0 events found. This should not happen with fallbacks.")

    # --- BROOKLYN FILTER ---
    print(f"[Pipeline] Filtering {len(all_events)} items for Brooklyn/Prospect Park sector...")
    brooklyn_keywords = ["Brooklyn", "Prospect Park", "Kings", "696 Flatbush", "Grand Army", "Lakeside", "LeFrak", "Zoo", "Breeze Hill"]
    filtered_events = []
    for event in all_events:
        text = f"{event.title} {event.venue} {event.description or ''}".lower()
        if any(kw.lower() in text for kw in brooklyn_keywords):
            filtered_events.append(event)
    
    print(f"[Pipeline] Post-filter count: {len(filtered_events)}")
    all_events = filtered_events

    # 2. Export CSV
    csv_file = "/tmp/extracted_events.csv"
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Date", "Venue", "Impact"])
            for event in all_events:
                dt = event.start_time.strftime("%Y-%m-%d") if hasattr(event.start_time, "strftime") else str(event.start_time)
                writer.writerow([event.source, event.title, dt, event.venue, event.impact_score])
        print(f"[Pipeline] CSV generated at {csv_file}")
    except Exception as e:
        print(f"[Pipeline] CSV generation failed: {e}")
    
    # 3. Report & Notification
    try:
        from src.reporting.report_generator import ReportGenerator
        from src.reporting.notifier import Notifier
        
        print("[Pipeline] Rendering report...")
        report_html = ReportGenerator.generate_html_report(all_events)
        
        if os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true":
            recipient = os.getenv("STAKEHOLDER_EMAIL")
            if recipient:
                print(f"[Pipeline] Sending to {recipient}...")
                notifier = Notifier()
                success = await notifier.send_email(
                    recipient=recipient,
                    subject=f"Brooklyn Event Summary (696 Flatbush) - {datetime.now().strftime('%Y-%m-%d')}",
                    html_content=report_html,
                    attachment_path=csv_file
                )
                print(f"[Pipeline] Final Status: {'SENT' if success else 'SEND_FAILED'}")
            else:
                print("[Pipeline] Error: No STAKEHOLDER_EMAIL set.")
    except Exception as e:
        print(f"[Pipeline] Notification module failed: {e}")
    
    print("=== PIPELINE END ===")
    return all_events

@functions_framework.http
def cloud_function_entry(request):
    """Secure HTTP Trigger."""
    try:
        # Avoid async issues by creating a fresh event loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        events = loop.run_until_complete(run_ingestion_pipeline())
        loop.close()
        return f"SUCCESS: {len(events)} events processed (v{VERSION})", 200
    except Exception as e:
        print(f"[FATAL] Entry point crash: {e}")
        return f"ERROR: See logs. {e}", 500
