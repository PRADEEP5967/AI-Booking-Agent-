from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

def _validate_iso8601(value: str, field_name: str) -> str:
    """
    Validates that a string is a valid ISO 8601 datetime.
    Accepts 'Z' as UTC.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string in ISO 8601 format.")
    try:
        # Accepts both with and without 'Z'
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        raise ValueError(f"{field_name} must be a valid ISO 8601 datetime string.")
    return value

def _trim_if_str(value):
    if isinstance(value, str):
        return value.strip()
    return value

class ConversationMessage(BaseModel):
    """Message in a conversation"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of the message")

class ConversationState(BaseModel):
    """State of a conversation session"""
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="List of conversation messages")
    stage: str = Field(default="initial", description="Current conversation stage")
    current_booking_data: Optional[Dict[str, Any]] = Field(None, description="Current booking information")

class AgentResponse(BaseModel):
    """Response from the booking agent"""
    message: str = Field(..., description="Agent's response message")
    booking_data: Optional[Dict[str, Any]] = Field(None, description="Booking data if available")
    suggested_slots: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested time slots")
    stage: str = Field(..., description="Current conversation stage")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is required")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message to the agent.")

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v):
        v = _trim_if_str(v)
        if not v:
            raise ValueError("Message cannot be empty.")
        return v

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent's response to the user.")

    @field_validator("response")
    @classmethod
    def response_not_empty(cls, v):
        v = _trim_if_str(v)
        if not v:
            raise ValueError("Response cannot be empty.")
        return v

class AvailabilityRequest(BaseModel):
    start_time: str = Field(..., description="ISO 8601 start time (e.g., '2024-06-10T10:00:00Z').")
    end_time: str = Field(..., description="ISO 8601 end time (e.g., '2024-06-10T10:30:00Z').")

    @field_validator("start_time")
    @classmethod
    def validate_start_time_isoformat(cls, v):
        return _validate_iso8601(v, "start_time")

    @field_validator("end_time")
    @classmethod
    def validate_end_time_isoformat(cls, v):
        return _validate_iso8601(v, "end_time")

    @model_validator(mode="after")
    def check_end_after_start(self):
        start = self.start_time
        end = self.end_time
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end_dt <= start_dt:
                raise ValueError("end_time must be after start_time.")
        except Exception:
            raise ValueError("start_time and end_time must be valid ISO 8601 datetime strings and end_time must be after start_time.")
        return self

class AvailabilityResponse(BaseModel):
    available: bool = Field(..., description="Whether the requested time slot is available.")

class BookingRequest(BaseModel):
    start_time: str = Field(..., description="ISO 8601 start time for the booking.")
    end_time: str = Field(..., description="ISO 8601 end time for the booking.")
    summary: Optional[str] = Field(None, description="Optional summary or title for the booking.")

    @field_validator("start_time")
    @classmethod
    def validate_start_time_isoformat(cls, v):
        return _validate_iso8601(v, "start_time")

    @field_validator("end_time")
    @classmethod
    def validate_end_time_isoformat(cls, v):
        return _validate_iso8601(v, "end_time")

    @field_validator("summary")
    @classmethod
    def summary_trim(cls, v):
        return _trim_if_str(v)

    @model_validator(mode="after")
    def check_end_after_start(self):
        start = self.start_time
        end = self.end_time
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end_dt <= start_dt:
                raise ValueError("end_time must be after start_time.")
        except Exception:
            raise ValueError("start_time and end_time must be valid ISO 8601 datetime strings and end_time must be after start_time.")
        return self

class BookingResponse(BaseModel):
    status: str = Field(..., description="Status of the booking (e.g., 'confirmed', 'failed').")
    start: str = Field(..., description="ISO 8601 start time of the booking.")
    end: str = Field(..., description="ISO 8601 end time of the booking.")
    summary: Optional[str] = Field(None, description="Summary or title of the booking.")

    @field_validator("status")
    @classmethod
    def status_not_empty(cls, v):
        v = _trim_if_str(v)
        if not v:
            raise ValueError("Status cannot be empty.")
        return v

    @field_validator("start")
    @classmethod
    def validate_start_isoformat(cls, v):
        return _validate_iso8601(v, "start")

    @field_validator("end")
    @classmethod
    def validate_end_isoformat(cls, v):
        return _validate_iso8601(v, "end")

    @field_validator("summary")
    @classmethod
    def summary_trim(cls, v):
        return _trim_if_str(v)

    @model_validator(mode="after")
    def check_end_after_start(self):
        start = self.start
        end = self.end
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end_dt <= start_dt:
                raise ValueError("end must be after start.")
        except Exception:
            raise ValueError("start and end must be valid ISO 8601 datetime strings and end must be after start.")
        return self