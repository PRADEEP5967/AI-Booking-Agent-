from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    text: str
    timestamp: Optional[datetime] = None

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool

class BookingRequest(BaseModel):
    user_name: str
    email: str
    preferred_date: str
    preferred_time: Optional[str]
    duration: int = 60
    meeting_type: Optional[str] = None

class Booking(BaseModel):
    id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    service_type: str
    scheduled_datetime: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ConversationState(BaseModel):
    session_id: str
    stage: str = "greeting"
    messages: List[ConversationMessage] = []
    current_booking_data: Dict[str, Any] = {}
    available_slots: List[TimeSlot] = []

class AgentResponse(BaseModel):
    message: str
    booking_data: Optional[Dict[str, Any]] = None
    suggested_slots: Optional[List[TimeSlot]] = None
    requires_confirmation: bool = False

class AvailabilityRequest(BaseModel):
    start_time: str
    end_time: str

class AvailabilityResponse(BaseModel):
    available: bool

class BookingResponse(BaseModel):
    status: str
    start: str
    end: str
    summary: Optional[str] = None 