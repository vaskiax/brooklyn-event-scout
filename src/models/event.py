from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BaseEvent(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    venue: str
    source: str
    raw_data: Optional[dict] = None

class Event(BaseEvent):
    impact_score: Optional[int] = Field(None, ge=1, le=5)
    attendance_estimate: Optional[int] = None
    is_new: bool = False

class Alert(BaseModel):
    category: str # Weather, Transit, etc.
    severity: str # Low, Med, High
    headline: str
    description: str
    source: str
    start_time: datetime
    end_time: Optional[datetime] = None
    affected_areas: List[str] = []
