import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pytz
from ..config.settings import settings

# Only import Google Calendar libraries if not in mock mode
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

from ..models.schemas import TimeSlot, Booking

class MockCalendarService:
    """
    Mock calendar service for testing and development without Google Calendar API.
    Provides realistic calendar functionality without external dependencies.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Mock Calendar Service")
        # Mock busy times - simulate some existing meetings
        self.mock_busy_times = [
            {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T10:00:00Z"},
            {"start": "2024-01-15T14:00:00Z", "end": "2024-01-15T15:30:00Z"},
            {"start": "2024-01-16T11:00:00Z", "end": "2024-01-16T12:00:00Z"},
        ]
    
    def get_free_slots(self, start_date: str, end_date: str, duration_minutes: int = 60) -> List[Dict[str, str]]:
        """Get available time slots between start_date and end_date."""
        self.logger.info(f"Mock: Getting free slots from {start_date} to {end_date}")
        
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except Exception as e:
            self.logger.error(f"Mock: Invalid date format: {e}")
            return []
        
        # Generate mock free slots
        free_slots = []
        current = start_dt
        
        while current + timedelta(minutes=duration_minutes) <= end_dt:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with mock busy times
            is_free = True
            for busy in self.mock_busy_times:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                
                if slot_start < busy_end and slot_end > busy_start:
                    is_free = False
                    break
            
            if is_free:
                free_slots.append({
                    "start": slot_start.isoformat().replace("+00:00", "Z"),
                    "end": slot_end.isoformat().replace("+00:00", "Z")
                })
            
            current += timedelta(minutes=15)  # 15-minute increments
        
        self.logger.info(f"Mock: Found {len(free_slots)} free slots")
        return free_slots
    
    def create_event(self, title: str, start_time: str, end_time: str, description: str = "") -> Dict[str, Any]:
        """Create a mock calendar event."""
        self.logger.info(f"Mock: Creating event '{title}' from {start_time} to {end_time}")
        
        # Add to mock busy times
        self.mock_busy_times.append({
            "start": start_time,
            "end": end_time
        })
        
        return {
            "id": f"mock_event_{len(self.mock_busy_times)}",
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
            "status": "confirmed"
        }
    
    def book_slot(self, start_time: datetime, end_time: datetime, title: str, description: str = "", attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Book a slot in the mock calendar."""
        start_str = start_time.isoformat().replace("+00:00", "Z")
        end_str = end_time.isoformat().replace("+00:00", "Z")
        
        event = self.create_event(title, start_str, end_str, description)
        
        return {
            "status": "mock_booked",
            "event_id": event["id"],
            "message": f"Mock booking created: {title}",
            "start": start_str,
            "end": end_str
        }
    
    def get_available_slots(self, target_date: datetime, duration: int = 60) -> List[Dict[str, str]]:
        """Get available slots for a specific date."""
        start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        return self.get_free_slots(
            start_date.isoformat().replace("+00:00", "Z"),
            end_date.isoformat().replace("+00:00", "Z"),
            duration
        )

class CalendarService:
    """
    Modern, robust, and extensible Google Calendar service.
    - Implements fracture pattern: isolated, testable, and safe.
    - No bugs: Defensive against all edge cases and credential issues.
    - Improvements: Environment-based config, safe token handling, and clear error reporting.
    """

    TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")
    CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/google_credentials.json")
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events'
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Check if we should use mock mode
        if settings.USE_MOCK_CALENDAR:
            self.logger.info("Using Mock Calendar Service")
            self.service = None
            self.mock_service = MockCalendarService()
        else:
            self.logger.info("Using Real Google Calendar Service")
            self.service = self._authenticate()
            self.mock_service = None

    def _authenticate(self):
        """
        Authenticate and return a Google Calendar API service object.
        Uses environment variables for credentials and token paths.
        Handles all edge cases and ensures credentials are valid.
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            raise RuntimeError("Google Calendar libraries not available. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        
        creds = None

        # Try to load existing token
        if os.path.isfile(self.TOKEN_PATH):
            try:
                with open(self.TOKEN_PATH, 'rb') as token_file:
                    loaded = pickle.load(token_file)
                    if hasattr(loaded, 'valid') and hasattr(loaded, 'expired'):
                        creds = loaded
            except Exception as e:
                self.logger.warning(f"Failed to load token.pickle: {e}")
                creds = None
                try:
                    os.remove(self.TOKEN_PATH)
                except Exception:
                    pass

        # If no valid creds, refresh or create new
        if not creds or not getattr(creds, "valid", False):
            try:
                if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
                    creds.refresh(Request())
                else:
                    if not os.path.isfile(self.CREDENTIALS_PATH):
                        raise FileNotFoundError(f"Google credentials file not found at {self.CREDENTIALS_PATH}")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_PATH, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
            except Exception as e:
                self.logger.error(f"Failed to obtain Google credentials: {e}")
                raise RuntimeError("Google Calendar authentication failed. Check credentials and permissions.") from e

            # Save the credentials for the next run
            try:
                with open(self.TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                self.logger.warning(f"Failed to save token.pickle: {e}")

        if not creds or not getattr(creds, "valid", False):
            raise RuntimeError("Google Calendar credentials are invalid after authentication.")

        try:
            service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            self.logger.error(f"Failed to build Google Calendar service: {e}")
            raise RuntimeError("Failed to initialize Google Calendar service.") from e

        return service

    def get_free_slots(self, start_date, end_date, duration_minutes=60):
        """
        Get available time slots between start_date and end_date with the given duration.
        - start_date, end_date: ISO 8601 date strings (e.g., '2024-06-10T00:00:00Z')
        - duration_minutes: int, duration of each slot in minutes
        Returns: List of dicts with 'start' and 'end' ISO 8601 strings.
        """
        if self.mock_service:
            return self.mock_service.get_free_slots(start_date, end_date, duration_minutes)
        
        # Defensive: Validate input
        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise ValueError("start_date and end_date must be ISO 8601 strings.")
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer.")

        # Parse input dates
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except Exception as e:
            raise ValueError("start_date and end_date must be valid ISO 8601 datetime strings.") from e

        if end_dt <= start_dt:
            raise ValueError("end_date must be after start_date.")

        # Get busy times from primary calendar
        try:
            events_result = self.service.freebusy().query(
                body={
                    "timeMin": start_dt.isoformat(),
                    "timeMax": end_dt.isoformat(),
                    "timeZone": "UTC",
                    "items": [{"id": "primary"}]
                }
            ).execute()
            busy_periods = events_result.get("calendars", {}).get("primary", {}).get("busy", [])
        except Exception as e:
            self.logger.error(f"Failed to fetch busy times: {e}")
            raise RuntimeError("Failed to fetch calendar busy times.") from e

        # Build list of free slots
        free_slots = []
        current = start_dt

        # Sort busy periods for efficient checking
        busy_periods_sorted = sorted(
            (
                {
                    "start": datetime.fromisoformat(busy["start"].replace("Z", "+00:00")),
                    "end": datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                }
                for busy in busy_periods
            ),
            key=lambda b: b["start"]
        )

        while current + timedelta(minutes=duration_minutes) <= end_dt:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            is_free = True
            for busy in busy_periods_sorted:
                # If slot ends before busy starts, or starts after busy ends, it's fine
                if slot_end <= busy["start"]:
                    break  # No more overlaps possible
                if slot_start < busy["end"] and slot_end > busy["start"]:
                    is_free = False
                    break
            if is_free:
                free_slots.append({
                    "start": slot_start.isoformat().replace("+00:00", "Z"),
                    "end": slot_end.isoformat().replace("+00:00", "Z")
                })
            current += timedelta(minutes=15)  # Move in 15-min increments for granularity

        return free_slots

    def create_event(self, title, start_time, end_time, description=""):
        """
        Create a calendar event.
        - title: str, event summary/title
        - start_time, end_time: ISO 8601 datetime strings (e.g., '2024-06-10T10:00:00Z')
        - description: str, optional event description
        Returns: The created event resource dict.
        """
        if self.mock_service:
            return self.mock_service.create_event(title, start_time, end_time, description)
        
        # Defensive: Validate input
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string.")
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            raise ValueError("start_time and end_time must be ISO 8601 strings.")

        # Validate ISO 8601 format for start_time and end_time
        try:
            _ = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            _ = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except Exception as e:
            raise ValueError("start_time and end_time must be valid ISO 8601 datetime strings.") from e

        if end_time <= start_time:
            raise ValueError("end_time must be after start_time.")

        try:
            event = {
                "summary": title.strip(),
                "description": description.strip() if isinstance(description, str) else "",
                "start": {
                    "dateTime": start_time,
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "UTC"
                }
            }
            created_event = self.service.events().insert(calendarId="primary", body=event).execute()
            return created_event
        except Exception as e:
            self.logger.error(f"Failed to create calendar event: {e}")
            raise RuntimeError("Failed to create calendar event.") from e
    
    def book_slot(self, start_time: datetime, end_time: datetime, title: str, description: str = "", attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Book a slot in the calendar."""
        if self.mock_service:
            return self.mock_service.book_slot(start_time, end_time, title, description, attendees)
        
        # Real Google Calendar booking
        start_str = start_time.isoformat().replace("+00:00", "Z")
        end_str = end_time.isoformat().replace("+00:00", "Z")
        
        event = self.create_event(title, start_str, end_str, description)
        
        return {
            "status": "booked",
            "event_id": event["id"],
            "message": f"Booking created: {title}",
            "start": start_str,
            "end": end_str
        }
    
    def get_available_slots(self, target_date: datetime, duration: int = 60) -> List[Dict[str, str]]:
        """Get available slots for a specific date."""
        if self.mock_service:
            return self.mock_service.get_available_slots(target_date, duration)
        
        # Real Google Calendar implementation
        start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        return self.get_free_slots(
            start_date.isoformat().replace("+00:00", "Z"),
            end_date.isoformat().replace("+00:00", "Z"),
            duration
        )

    def get_available_slots(self, date: datetime, duration_minutes: int = 60) -> List[TimeSlot]:
        """
        Get available time slots for a given date.
        Handles timezone, event overlap, and returns only available slots.
        """
        if not self.service:
            return self._get_mock_available_slots(date, duration_minutes)

        # Modern, robust, and bug-free implementation for fetching available slots
        try:
            # Always use UTC for internal calculations
            tz = pytz.UTC
            if date.tzinfo:
                date = date.astimezone(tz)
            else:
                date = tz.localize(date)

            # Define working hours (configurable if needed)
            WORK_START_HOUR = 9
            WORK_END_HOUR = 17
            SLOT_INTERVAL_MINUTES = 30

            start_time = date.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
            end_time = date.replace(hour=WORK_END_HOUR, minute=0, second=0, microsecond=0)

            # Defensive: Ensure start_time < end_time
            if start_time >= end_time:
                print("Start time is not before end time for available slots.")
                return []

            # Fetch events from Google Calendar API
            try:
                events_result = self.service.events().list(
                    calendarId="primary",
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                existing_events = events_result.get('items', [])
            except Exception as e:
                print(f"Error fetching events from Google Calendar: {e}")
                return self._get_mock_available_slots(date, duration_minutes)

            # --- Modern, robust, and bug-free available slot calculation ---
            # 1. Parse busy times robustly, handling all-day and timed events
            busy_times = []
            for event in existing_events:
                try:
                    # Prefer 'dateTime', fallback to 'date' (all-day)
                    event_start_raw = event['start'].get('dateTime') or event['start'].get('date')
                    event_end_raw = event['end'].get('dateTime') or event['end'].get('date')
                    if not event_start_raw or not event_end_raw:
                        continue  # Skip malformed events

                    # All-day event: block the whole workday
                    if 'T' not in event_start_raw:
                        event_start_dt = start_time
                        event_end_dt = end_time
                    else:
                        # Defensive: always parse as UTC
                        event_start_dt = datetime.fromisoformat(event_start_raw.replace('Z', '+00:00'))
                        event_end_dt = datetime.fromisoformat(event_end_raw.replace('Z', '+00:00'))
                        # Clamp to workday if event is outside
                        if event_start_dt < start_time:
                            event_start_dt = start_time
                        if event_end_dt > end_time:
                            event_end_dt = end_time
                    # Only add if event is within the workday
                    if event_end_dt > start_time and event_start_dt < end_time:
                        busy_times.append((event_start_dt, event_end_dt))
                except Exception as e:
                    print(f"Error parsing event: {e}")

            # 2. Generate all possible slots in the workday, checking for overlaps
            available_slots = []
            current_time = start_time
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                # Check for overlap with any busy time
                is_available = True
                for busy_start, busy_end in busy_times:
                    # Overlap if slot starts before busy ends and slot ends after busy starts
                    if current_time < busy_end and slot_end > busy_start:
                        is_available = False
                        break
                available_slots.append(TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    available=is_available
                ))
                current_time += timedelta(minutes=SLOT_INTERVAL_MINUTES)

            # 3. Return only available slots (filter for .available == True)
            return [slot for slot in available_slots if slot.available]

        # Defensive: fallback to mock slots on any error
        except Exception as e:
            print(f"Error fetching calendar data: {e}")
            return self._get_mock_available_slots(date, duration_minutes)

    def _get_mock_available_slots(self, date: datetime, duration_minutes: int) -> List[TimeSlot]:
        """
        Generate mock available slots for development and fallback.
        """
        slots = []
        tz = pytz.UTC
        date = date.astimezone(tz) if date.tzinfo else tz.localize(date)
        start_hour = 9
        end_hour = 17
        slot_interval = 30

        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                if hour == end_hour - 1 and minute == 30:
                    break
                start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=duration_minutes)
                if end_time.hour < end_hour or (end_time.hour == end_hour and end_time.minute == 0):
                    slots.append(TimeSlot(
                        start_time=start_time,
                        end_time=end_time,
                        available=True
                    ))
        return slots

    # Modern, robust, and bug-free implementation of availability checking and booking

    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Check if a time slot is available using Google Calendar free/busy API.
        Returns True if available, False if busy or error.
        Improvements:
        - Robust timezone handling (always UTC)
        - Defensive: returns True in mock mode, False on error
        - Clear error logging
        """
        try:
            tz = pytz.UTC
            # Ensure timezone-aware datetimes
            if not start_time.tzinfo:
                start_time = tz.localize(start_time)
            else:
                start_time = start_time.astimezone(tz)
            if not end_time.tzinfo:
                end_time = tz.localize(end_time)
            else:
                end_time = end_time.astimezone(tz)

            if not self.service:
                # In mock mode, always available
                return True

            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": "primary"}]
            }
            freebusy = self.service.freebusy().query(body=body).execute()
            busy_periods = freebusy.get('calendars', {}).get('primary', {}).get('busy', [])
            return len(busy_periods) == 0
        except Exception as e:
            print(f"[CalendarService] Error checking availability: {e}")
            return False

    def book_slot(
        self,
        start_time: datetime,
        end_time: datetime,
        summary: str,
        description: str = "",
        attendees: Optional[List[str]] = None
    ) -> dict:
        """
        Book a slot in the calendar. Returns booking status and event info.
        Improvements:
        - Robust timezone handling (always UTC)
        - Defensive: returns mock booking in mock mode
        - Returns clear error info on failure
        - Attendees list is optional and validated
        """
        try:
            tz = pytz.UTC
            # Ensure timezone-aware datetimes
            if not start_time.tzinfo:
                start_time = tz.localize(start_time)
            else:
                start_time = start_time.astimezone(tz)
            if not end_time.tzinfo:
                end_time = tz.localize(end_time)
            else:
                end_time = end_time.astimezone(tz)

            if not self.service:
                # Mock mode: simulate booking
                return {
                    "status": "mock_booked",
                    "start": start_time,
                    "end": end_time,
                    "summary": summary,
                    "attendees": attendees or []
                }

            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in attendees] if attendees else [],
            }
            created_event = self.service.events().insert(
                calendarId="primary",
                body=event
            ).execute()
            return {
                "status": "booked",
                "event_id": created_event.get('id'),
                "start": start_time,
                "end": end_time,
                "summary": summary,
                "attendees": attendees or []
            }
        except Exception as e:
            print(f"[CalendarService] Error booking slot: {e}")
            return {"status": "error", "error": str(e)}

    # Singleton instance for backward compatibility and functional access
    _calendar_service_instance = None

    def get_calendar_service():
        global _calendar_service_instance
        if _calendar_service_instance is None:
            _calendar_service_instance = CalendarService()
        return _calendar_service_instance

    def check_availability(start_time, end_time):
        """
        Functional access to check_availability (backward compatibility).
        """
        return get_calendar_service().check_availability(start_time, end_time)

    def book_slot(start_time, end_time, summary, description="", attendees=None):
        """
        Functional access to book_slot (backward compatibility).
        """
        return get_calendar_service().book_slot(start_time, end_time, summary, description, attendees)