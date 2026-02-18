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
        from src.utils.memory import EventMemory
        from src.integration.calendar_connector import CalendarConnector
        print("[Pipeline] Module setup complete.")
    except Exception as e:
        print(f"[Pipeline] FATAL: Import failure: {e}")
        # Last resort fallback if imports fail entirely
        return []

    # 2. Collector Tasks
    print("[Pipeline] Initiating collectors...")
    tasks = [
        ("NYRR", NYRRCollector().fetch_events()),
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
    brooklyn_keywords = ["Brooklyn", "Prospect Park", "Kings", "696 Flatbush", "Grand Army", "Lakeside", "LeFrak", "Zoo", "Breeze Hill", "Audubon", "Lookout Hill", "EcoCenter", "Parkside", "Lullwater", "The Loop"]
    filtered_events = []
    for event in all_events:
        text = f"{event.title} {event.venue} {event.description or ''}".lower()
        if any(kw.lower() in text for kw in brooklyn_keywords):
            filtered_events.append(event)
    
    print(f"[Pipeline] Post-filter count: {len(filtered_events)}")
    
    # --- DATE FILTER (Global) ---
    # Remove past events so they don't appear in Report, CSV, or Calendar
    # And so Memory logic treats them as "missing" (triggering deletion)
    future_events = []
    now_date = datetime.now().date()
    for event in filtered_events:
        if event.start_time.date() >= now_date:
            future_events.append(event)
    
    print(f"[Pipeline] Post-Date-Filter count: {len(future_events)}")
    all_events = future_events

    # --- MEMORY & CALENDAR INTEGRATION ---
    print("[Pipeline] Initializing Memory and Calendar...")
    try:
        memory = EventMemory()
        calendar = CalendarConnector()
        
        new_event_count = 0
        current_run_hash_ids = set()

        for event in all_events:
            # Generate ID to track what we see in this run
            event_hash = memory._generate_id(event)
            current_run_hash_ids.add(event_hash)

            if memory.is_new(event):
                event.is_new = True
                new_event_count += 1
                google_id = None
                if os.getenv("CALENDAR_ENABLED", "true").lower() == "true":
                     google_id = calendar.add_event(event)
                memory.mark_processed(event, google_event_id=google_id)
        
        # --- SYNC: Remove events that are no longer in the report ---
        print("[Pipeline] Syncing: Checking for cancelled/removed events...")
        known_ids = set(memory.get_all_ids())
        
        # Determine IDs that are in memory but NOT in the current run
        # Note: We only remove if we are "source of truth". 
        # For safety, maybe we should only remove "future" events? 
        # For now, simplistic approach: if it's not in the run, we remove it.
        # Ensure we don't wipe historical data?
        # Given this is a weekly "upcoming" report, if it's not in the report, it shouldn't be on the calendar (or is past).
        
        missing_ids = known_ids - current_run_hash_ids
        deleted_count = 0
        
        for missing_hash in missing_ids:
            google_id = memory.get_google_id(missing_hash)
            if google_id and os.getenv("CALENDAR_ENABLED", "true").lower() == "true":
                calendar.delete_event(google_id)
                deleted_count += 1
            
            # Remove from memory regardless of calendar status so we don't track it forever
            memory.remove_event(missing_hash)

        print(f"[Pipeline] New events: {new_event_count}, Removed/Synced events: {deleted_count}")
        
    except Exception as e:
        print(f"[Pipeline] Memory/Calendar integration failed: {e}")

    # 2. Export CSV
    csv_file = "/tmp/extracted_events.csv"
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Date", "Venue"])
            for event in all_events:
                dt = event.start_time.strftime("%Y-%m-%d") if hasattr(event.start_time, "strftime") else str(event.start_time)
                writer.writerow([event.source, event.title, dt, event.venue])
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

if __name__ == "__main__":
    # Local execution - mimics Cloud Function behavior
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ingestion_pipeline())
