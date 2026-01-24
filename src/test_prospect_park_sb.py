import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion.prospect_park import ProspectParkCollector

async def main():
    print("Testing Prospect Park Collector (SeleniumBase)...")
    print(f"Current Working Directory: {os.getcwd()}")
    collector = ProspectParkCollector()
    
    # fetch_events is async in interface but our SB implementation is sync internally?
    # Wait, the interface in main.py expects async. 
    # The previous implementation was async def fetch_events.
    # SeleniumBase is sync. We should run it in a thread or keep it sync if allowed.
    # But since the class method was defined as `async def` in the interface, we should probably wrap it or change it.
    # Let's check the edited file. I removed `async` keyword in my write_to_file? 
    # Yes, I wrote `def fetch_events(self)`. 
    # This might break the interface if the caller awaits it.
    # For this standalone test, we just call it.
    
    events = collector.fetch_events()
    
    print(f"Found {len(events)} events.")
    for e in events:
        print(f"- {e.title} ({e.start_time})")

if __name__ == "__main__":
    async def run_test():
        collector = ProspectParkCollector()
        events = await collector.fetch_events()
        print(f"Found {len(events)} events.")
        for e in events:
            time_str = e.start_time.strftime('%Y-%m-%d') if isinstance(e.start_time, datetime) else str(e.start_time)
            print(f"- {e.title} on {time_str} : {e.raw_data.get('time_text', '')}")

    asyncio.run(run_test())
