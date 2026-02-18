from datetime import datetime
import sys
import os

# Mock Event class
class Event:
    def __init__(self, title, venue, description="", source=""):
        self.title = title
        self.venue = venue
        self.description = description
        self.source = source
        self.start_time = datetime.now()
        self.impact_score = 5

def test_filter():
    print("=== DEBUGGING FILTER LOGIC ===")
    
    # 1. Mock Data (Copied from Fallbacks)
    events = []
    
    # NYRR Fallbacks
    nyrr_fallbacks = [
        ("Fred Lebow Half Marathon", "Central Park"),
        ("Gridiron 4M", "Central Park"),
        ("Manhattan 10K", "Central Park"),
        ("NYC Half Marathon", "Brooklyn to Manhattan"),
        ("SHAPE + Health Women's Half", "Central Park"),
        ("Brooklyn Half Marathon", "Brooklyn"),
        ("Global Running Day 5K", "Central Park"),
        ("Queens 10K", "Flushing Meadows"),
        ("Bronx 10M", "The Bronx"),
        ("Staten Island Half", "Staten Island"),
        ("New York City Marathon", "Five Boroughs"),
    ]
    for t, v in nyrr_fallbacks:
        events.append(Event(t, v, source="NYRR"))

    # Prospect Park Fallbacks
    pp_fallbacks = [
        ("Prospect Park 5K: February Edition", "The Loop"),
        ("Ice Skating at LeFrak Center", "Lakeside"),
        ("Smorgasburg Prospect Park", "Breeze Hill"),
        ("Prospect Park Zoo: Winter Wildlife", "Prospect Park Zoo"),
        ("Birdwatching Tour", "Audubon Center"),
        ("Lakeside Broomball League", "LeFrak Center"),
        ("Wednesday Morning Run", "Entrance Parkside"),
        ("Prospect Park Alliance Volunteer Day", "Lullwater"),
        ("History Tour: Battle Pass", "Lookout Hill"),
        ("Nature Exploration-Kids", "EcoCenter"),
    ]
    for t, v in pp_fallbacks:
        events.append(Event(t, v, source="ProspectPark"))

    # 2. Run Filter
    brooklyn_keywords = ["Brooklyn", "Prospect Park", "Kings", "696 Flatbush", "Grand Army", "Lakeside", "LeFrak", "Zoo", "Breeze Hill"]
    
    kept = []
    dropped = []
    
    for event in events:
        text = f"{event.title} {event.venue} {event.description or ''}".lower()
        if any(kw.lower() in text for kw in brooklyn_keywords):
            kept.append(event)
        else:
            dropped.append(event)
            
    print(f"\nTotal Events: {len(events)}")
    print(f"Kept: {len(kept)}")
    print(f"Dropped: {len(dropped)}")
    
    print("\n--- KEPT EVENTS ---")
    for e in kept:
        print(f"[MATCH] {e.source}: {e.title} ({e.venue})")
        
    print("\n--- DROPPED EVENTS ---")
    for e in dropped:
        print(f"[DROP]  {e.source}: {e.title} ({e.venue})")

if __name__ == "__main__":
    test_filter()
