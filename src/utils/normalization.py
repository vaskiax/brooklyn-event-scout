from datetime import datetime
import re

def normalize_iso_format(date_str: str) -> datetime:
    """
    Attempts to parse various date strings into a datetime object.
    Simplified for Phase 1.
    """
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass
    
    # Add more complex regex or dateparser-like logic here as needed
    return datetime.now() # Fallback

def strip_html(text: str) -> str:
    """Removes HTML tags from a string."""
    return re.sub('<[^<]+?>', '', text)
