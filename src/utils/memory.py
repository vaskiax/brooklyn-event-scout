import json
import os
import hashlib
from datetime import datetime
from typing import List, Set, Dict, Optional

class EventMemory:
    """
    Manages a persistent record of processed events to avoid duplicates,
    identify new events, and track Google Calendar IDs for sync.
    """
    def __init__(self, storage_file: str = "data/event_memory.json"):
        self.storage_file = storage_file
        # Map: hash_id -> google_event_id (or None if not on calendar)
        self.event_map: Dict[str, Optional[str]] = {} 
        self.load()

    def _generate_id(self, event) -> str:
        """Generates a consistent hash ID for an event."""
        # Normalize data to ensure consistent hashing
        raw_str = f"{event.title}|{event.start_time}|{event.venue}".lower().strip()
        return hashlib.md5(raw_str.encode()).hexdigest()

    def load(self):
        """Loads data from the storage file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    
                    # Migration Logic: Handle old format (list of IDs)
                    if "processed_ids" in data and isinstance(data["processed_ids"], list):
                        # Convert list to dict with None values
                        self.event_map = {uid: None for uid in data["processed_ids"]}
                    else:
                        # New format
                        self.event_map = data.get("event_map", {})
            except Exception as e:
                print(f"[EventMemory] Warning: Failed to load memory file: {e}")
                self.event_map = {}
        else:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_file)), exist_ok=True)

    def save(self):
        """Saves current state to the storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "event_map": self.event_map
                }, f, indent=2)
        except Exception as e:
            print(f"[EventMemory] Error saving memory file: {e}")

    def is_new(self, event) -> bool:
        """Checks if an event is new (hash not in map)."""
        event_id = self._generate_id(event)
        return event_id not in self.event_map

    def mark_processed(self, event, google_event_id: Optional[str] = None):
        """Marks an event as processed and stores its Google Calendar ID."""
        event_id = self._generate_id(event)
        self.event_map[event_id] = google_event_id
        self.save()

    def get_google_id(self, event_hash: str) -> Optional[str]:
        """Returns the Google Calendar ID for a given hash."""
        return self.event_map.get(event_hash)

    def remove_event(self, event_hash: str):
        """Removes an event from memory."""
        if event_hash in self.event_map:
            del self.event_map[event_hash]
            self.save()

    def get_all_ids(self) -> List[str]:
        """Returns a list of all currently tracked event hashes."""
        return list(self.event_map.keys())
