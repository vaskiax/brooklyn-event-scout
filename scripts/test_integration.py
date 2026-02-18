import sys
import os
import shutil
from datetime import datetime
import asyncio

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.event import Event
from src.utils.memory import EventMemory

# Mock Calendar to avoid real API calls during test
class MockCalendarConnector:
    def __init__(self):
        self.events = []
    
    def add_event(self, event):
        print(f"[MockCalendar] Added event: {event.title}")
        self.events.append(event)
        return True

async def test_integration():
    print("=== STARTING VERIFICATION ===")
    
    # 1. Setup minimal environment
    test_memory_file = "data/test_event_memory.json"
    if os.path.exists(test_memory_file):
        os.remove(test_memory_file)
    
    # 2. Initialize Components
    memory = EventMemory(storage_file=test_memory_file)
    calendar = MockCalendarConnector()
    
    # 3. Create Dummy Events
    events = [
        Event(title="Test Event 1", start_time=datetime.now(), venue="Prospect Park", source="Test", impact_score=3),
        Event(title="Test Event 2", start_time=datetime.now(), venue="Brooklyn Museum", source="Test", impact_score=5)
    ]
    
    # 4. First Run (Should detect 2 new events)
    print("\n--- Run 1 (Fresh Memory) ---")
    new_count = 0
    for event in events:
        if memory.is_new(event):
            event.is_new = True
            new_count += 1
            calendar.add_event(event)
            memory.mark_processed(event)
    
    print(f"New Events Detected: {new_count}")
    if new_count != 2:
        print("FAIL: Expected 2 new events.")
        return
    
    # 5. Second Run (Should detect 0 new events)
    print("\n--- Run 2 (Existing Memory) ---")
    # Reload memory to simulate fresh start
    memory = EventMemory(storage_file=test_memory_file)
    
    new_count_2 = 0
    for event in events:
        # Reset flag for test
        event.is_new = False 
        if memory.is_new(event):
            event.is_new = True
            new_count_2 += 1
            calendar.add_event(event)
            memory.mark_processed(event)
            
    print(f"New Events Detected: {new_count_2}")
    if new_count_2 != 0:
        print("FAIL: Expected 0 new events on second run.")
        return

    # 6. Test New Event Addition
    print("\n--- Run 3 (Add New Event) ---")
    new_event = Event(title="Test Event 3", start_time=datetime.now(), venue="Grand Army Plaza", source="Test", impact_score=4)
    events.append(new_event)
    
    new_count_3 = 0
    for event in events:
        if memory.is_new(event):
            event.is_new = True
            new_count_3 += 1
            calendar.add_event(event)
            memory.mark_processed(event)
            
    print(f"New Events Detected: {new_count_3}")
    if new_count_3 != 1:
        print(f"FAIL: Expected 1 new event, got {new_count_3}")
        return

    print("\n=== VERIFICATION SUCCESSFUL ===")
    print("Memory logic works. Calendar add_event called correctly.")

if __name__ == "__main__":
    asyncio.run(test_integration())
