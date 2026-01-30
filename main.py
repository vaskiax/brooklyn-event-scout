import asyncio
import os
import csv
import functions_framework
import sys
from datetime import datetime

print("[Startup] Initializing modules...")
try:
    from src.ingestion.mta import MTAConnector
    from src.ingestion.weather import WeatherConnector
    from src.ingestion.nyrr import NYRRCollector
    from src.ingestion.prospect_park import ProspectParkCollector
    from src.reporting.report_generator import ReportGenerator
    from src.reporting.notifier import Notifier
    print("[Startup] All modules imported successfully.")
except Exception as e:
    print(f"[FATAL STARTUP ERROR] Failed to import modules: {e}")
    sys.exit(1)

async def run_ingestion_pipeline():
    """Main orchestration logic for event ingestion and reporting."""
    print("=== PIPELINE START ===")
    print(f"[Pipeline] Env Check: NOTIFICATIONS={os.getenv('NOTIFICATIONS_ENABLED', 'N/A')}")
    print(f"[Pipeline] Env Check: RECIPIENT={os.getenv('STAKEHOLDER_EMAIL', 'N/A')}")
    
    all_events = []
    
    # 1. Collectors
    print("[Pipeline] Spawning collectors...")
    try:
        collectors = [
            NYRRCollector().fetch_upcoming_races(),
            ProspectParkCollector().fetch_events(),
        ]
        
        results = []
        for coro in collectors:
            name = "CollectorTask" # Simplified to avoid __qualname__ issues
            print(f"[Pipeline] Awaiting {name}...")
            try:
                res = await coro
                print(f"[Pipeline] {name} finished.")
                results.append(res)
            except Exception as e:
                print(f"[Pipeline] {name} CRASHED: {e}")
                results.append([])

        for r in results:
            all_events.extend(r)
    except Exception as e:
        print(f"[Pipeline] Major failure in collector orchestration: {e}")

    print(f"[Pipeline] Successfully aggregated {len(all_events)} events.")

    # 2. Export CSV
    csv_file = "/tmp/extracted_events.csv"
    if all_events:
        try:
            with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Source", "Title", "Start Time", "Venue", "Impact Score"])
                for event in all_events:
                    time_str = event.start_time.strftime("%Y-%m-%d %H:%M") if isinstance(event.start_time, datetime) else str(event.start_time)
                    writer.writerow([event.source, event.title, time_str, event.venue, event.impact_score])
            print(f"[Pipeline] CSV exported to {csv_file}")
        except Exception as e:
            print(f"[Pipeline] CSV Export Failed: {e}")
    
    # 3. Generate Report
    print("[Pipeline] Generating HTML report...")
    try:
        report_html = ReportGenerator.generate_html_report(all_events)
    except Exception as e:
        print(f"[Pipeline] Report Generation Failed: {e}")
        report_html = "<h1>Error generating report</h1>"
    
    # 4. Notify
    if os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true":
        recipient = os.getenv("STAKEHOLDER_EMAIL")
        print(f"[Pipeline] Notifications ACTIVE for {recipient}")
        if recipient:
            try:
                notifier = Notifier()
                success = await notifier.send_email(
                    recipient=recipient,
                    subject=f"Weekly Event Summary - {datetime.now().strftime('%Y-%m-%d')}",
                    html_content=report_html,
                    attachment_path=csv_file if os.path.exists(csv_file) else None
                )
                print(f"[Pipeline] Notification result: {'SUCCESS' if success else 'FAILED'}")
            except Exception as e:
                print(f"[Pipeline] Notification CRASHED: {e}")
        else:
            print("[Pipeline] SKIP: No recipient defined.")
    else:
        print("[Pipeline] SKIP: Notifications disabled by ENV.")

    print("=== PIPELINE COMPLETE ===")
    return all_events

@functions_framework.http
def cloud_function_entry(request):
    """Universal HTTP entry point for Google Cloud Function."""
    print(f"--- TRIGGERED BY {request.method} ---")
    
    try:
        # We run the ingestion pipeline regardless of request content for this use case
        events = asyncio.run(run_ingestion_pipeline())
        msg = f"SUCCESS: {len(events)} events processed"
        print(f"--- {msg} ---")
        return msg, 200
    except Exception as e:
        print(f"--- FATAL CRASH: {e} ---")
        return f"Error: {e}", 500

if __name__ == "__main__":
    asyncio.run(run_ingestion_pipeline())
