import asyncio
from src.ingestion.prospect_park import ProspectParkCollector

async def main():
    print("=== Testing Prospect Park Collector ONLY ===")
    collector = ProspectParkCollector()
    events = await collector.fetch_events()
    
    print(f"\nFound {len(events)} events.")
    for event in events:
        print(f" - {event.start_time}: {event.title}")

if __name__ == "__main__":
    asyncio.run(main())
