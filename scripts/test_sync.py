import sys
import os
import shutil
from datetime import datetime
import asyncio

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.event import Event
from src.utils.memory import EventMemory

# Mock Calendar
class MockCalendarConnector:
    def __init__(self):
        self.events = {} # id -> event
        self.counter = 0
    
    def add_event(self, event):
        self.counter += 1
        fake_id = f"evt_{self.counter}"
        print(f"[MockCalendar] Added event: {event.title} (ID: {fake_id})")
        self.events[fake_id] = event
        return fake_id

    def delete_event(self, event_id):
        if event_id in self.events:
            print(f"[MockCalendar] Deleted event: {self.events[event_id].title} (ID: {event_id})")
            del self.events[event_id]
            return True
        print(f"[MockCalendar] Event {event_id} not found to delete.")
        return False

async def test_sync_logic():
    print("=== STARTING SYNC VERIFICATION ===")
    
    test_memory_file = "data/test_sync_memory.json"
    if os.path.exists(test_memory_file):
        os.remove(test_memory_file)
    
    memory = EventMemory(storage_file=test_memory_file)
    calendar = MockCalendarConnector()
    
    # 1. Run 1: Two events
    print("\n--- Run 1 (Add 2 Events) ---")
    run1_events = [
        Event(title="Event A", start_time=datetime.now(), venue="Parkside", source="Test", impact_score=3),
        Event(title="Event B", start_time=datetime.now(), venue="Lullwater", source="Test", impact_score=3)
    ]
    
    current_run_hash_ids = set()
    for event in run1_events:
        event_hash = memory._generate_id(event)
        current_run_hash_ids.add(event_hash)
        if memory.is_new(event):
            google_id = calendar.add_event(event)
            memory.mark_processed(event, google_event_id=google_id)

    # Sync Logic (Manual simulation of main.py logic)
    known_ids = set(memory.get_all_ids())
    missing_ids = known_ids - current_run_hash_ids
    for missing_hash in missing_ids:
        gid = memory.get_google_id(missing_hash)
        if gid:
            calendar.delete_event(gid)
        memory.remove_event(missing_hash)
        
    print(f"Memory size: {len(memory.event_map)}")
    if len(memory.event_map) != 2:
        print("FAIL: Expected 2 events in memory.")
        return

    # 2. Run 2: Event B is gone (cancelled), Event C is new
    print("\n--- Run 2 (Event A stays, B gone, C added) ---")
    run2_events = [
        Event(title="Event A", start_time=datetime.now(), venue="Parkside", source="Test", impact_score=3),
         # Event B removed
        Event(title="Event C", start_time=datetime.now(), venue="Lookout Hill", source="Test", impact_score=3)
    ]
    
    current_run_hash_ids_2 = set()
    for event in run2_events:
        event_hash = memory._generate_id(event)
        current_run_hash_ids_2.add(event_hash)
        if memory.is_new(event):
            google_id = calendar.add_event(event)
            memory.mark_processed(event, google_event_id=google_id)
            
    # Sync Logic
    known_ids = set(memory.get_all_ids())
    missing_ids = known_ids - current_run_hash_ids_2
    print(f"Detected Missing Hashes: {len(missing_ids)}")
    
    for missing_hash in missing_ids:
        gid = memory.get_google_id(missing_hash)
        if gid:
            calendar.delete_event(gid)
        memory.remove_event(missing_hash)

    print(f"Memory size: {len(memory.event_map)}") # Should be A and C
    if len(memory.event_map) != 2:
        print("FAIL: Expected 2 events in memory (A and C).")
        return
        
    print("\n=== VERIFICATION SUCCESSFUL ===")

if __name__ == "__main__":
    asyncio.run(test_sync_logic())
