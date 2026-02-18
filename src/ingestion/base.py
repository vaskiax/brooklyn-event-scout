from abc import ABC, abstractmethod
from typing import List
from src.models.event import Event

class EventCollector(ABC):
    @abstractmethod
    async def fetch_events(self) -> List[Event]:
        pass
