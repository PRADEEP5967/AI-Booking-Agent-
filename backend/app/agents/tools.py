# Placeholder for agent tools (e.g., time parsing, intent detection)
import re
from datetime import datetime, timedelta
from typing import Optional

def parse_time(text: str) -> Optional[str]:
    """
    Parse a time string from user input and return in HH:MM 24-hour format.
    Supports common time formats (e.g., '10am', '2:30 PM', '14:00', 'noon').
    Returns None if no valid time found.
    """
    if not isinstance(text, str):
        return None
    text = text.strip().lower()
    # Handle special cases
    if "noon" in text:
        return "12:00"
    if "midnight" in text:
        return "00:00"
    # Regex for times like 10am, 2:30 pm, 14:00, etc.
    patterns = [
        r'(?<!\d)(\d{1,2}):(\d{2})\s*(am|pm)?(?!\d)',  # 2:30 pm, 14:00
        r'(?<!\d)(\d{1,2})\s*(am|pm)(?!\w)',           # 10am, 2 pm
        r'(?<!\d)(\d{1,2})(?!\d)',                     # 9, 14
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            hour = None
            minute = 0
            ampm = None
            # Pattern 1: (\d{1,2}):(\d{2})\s*(am|pm)?
            if len(groups) >= 2 and groups[1] is not None and groups[1].isdigit():
                hour = int(groups[0])
                minute = int(groups[1])
                ampm = groups[2] if len(groups) > 2 and groups[2] else None
            # Pattern 2: (\d{1,2})\s*(am|pm)
            elif len(groups) >= 2 and groups[0] and groups[1] in ("am", "pm"):
                hour = int(groups[0])
                ampm = groups[1]
            # Pattern 3: (\d{1,2})
            elif len(groups) >= 1 and groups[0] and groups[0].isdigit():
                hour = int(groups[0])
            # Apply am/pm logic
            if hour is not None:
                if ampm:
                    if ampm == "pm" and hour != 12:
                        hour += 12
                    if ampm == "am" and hour == 12:
                        hour = 0
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return f"{hour:02d}:{minute:02d}"
    return None

def parse_date(text: str, today: Optional[datetime] = None) -> Optional[str]:
    """
    Parse a date string from user input and return in YYYY-MM-DD format.
    Handles 'today', 'tomorrow', weekdays, and explicit dates.
    Returns None if no valid date found.
    """
    if not isinstance(text, str):
        return None
    text = text.strip().lower()
    today = today or datetime.today()
    # Handle 'today' and 'tomorrow'
    if "today" in text:
        return today.strftime("%Y-%m-%d")
    if "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    # Handle weekdays
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(weekdays):
        if day in text:
            days_ahead = (i - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            return target.strftime("%Y-%m-%d")
    # Handle explicit date formats (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY)
    # Try ISO format first
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if match:
        y, m, d = match.groups()
        try:
            dt = datetime(int(y), int(m), int(d))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    # Try MM/DD/YYYY and DD/MM/YYYY (ambiguous, prefer MM/DD/YYYY for US)
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if match:
        first, second, year = match.groups()
        # Try MM/DD/YYYY
        try:
            dt = datetime(int(year), int(first), int(second))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        # Try DD/MM/YYYY
        try:
            dt = datetime(int(year), int(second), int(first))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    return None

def detect_intent(text: str) -> str:
    """
    Detect user intent from input text.
    Returns one of: 'book', 'cancel', 'reschedule', 'greet', 'unknown'.
    """
    if not isinstance(text, str):
        return "unknown"
    text = text.lower()
    # Use word boundaries to avoid false positives
    if re.search(r'\b(book|schedule|reserve|set up|make appointment)\b', text):
        return "book"
    if re.search(r'\b(cancel|delete|remove|drop)\b', text):
        return "cancel"
    if re.search(r'\b(reschedule|move|change time|postpone)\b', text):
        return "reschedule"
    if re.search(r'\b(hi|hello|hey|greetings)\b', text):
        return "greet"
    return "unknown"

def handle_edge_cases(user_input, state):
    edge_cases = {
        "past_date": "I can only book future appointments.",
        "outside_hours": "I can only book during business hours (9 AM - 6 PM).",
        "conflicting_slots": "That time is already booked. Here are alternatives:",
        "invalid_duration": "Meeting duration should be between 15 minutes and 4 hours.",
        "weekend_booking": "Would you prefer a weekday slot instead?"
    }
    # Extract booking data from state
    booking_data = getattr(state, 'current_booking_data', {})
    # 1. Check for past date
    date_str = booking_data.get('scheduled_datetime') or booking_data.get('preferred_date')
    booking_date = None
    if date_str:
        try:
            if isinstance(date_str, datetime):
                booking_date = date_str
            elif isinstance(date_str, str):
                if len(date_str) == 10:
                    booking_date = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    booking_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            if booking_date and booking_date.date() < datetime.now().date():
                return edge_cases["past_date"]
        except Exception:
            pass
    # 2. Check for outside business hours
    time_str = booking_data.get('preferred_time')
    hour = None
    if not time_str and 'scheduled_datetime' in booking_data:
        try:
            dt = booking_data['scheduled_datetime']
            if isinstance(dt, str):
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M')
            if isinstance(dt, datetime):
                hour = dt.hour
        except Exception:
            hour = None
    elif time_str:
        try:
            hour = int(time_str.split(':')[0])
        except Exception:
            hour = None
    if hour is not None and (hour < 9 or hour >= 18):
        return edge_cases["outside_hours"]
    # 3. Check for weekend booking
    if booking_date:
        try:
            weekday = booking_date.weekday()
            if weekday >= 5:
                return edge_cases["weekend_booking"]
        except Exception:
            pass
    # 4. Check for invalid duration
    duration = booking_data.get('duration') or booking_data.get('duration_minutes')
    try:
        if duration is not None:
            duration_int = int(duration)
            if duration_int < 15 or duration_int > 240:
                return edge_cases["invalid_duration"]
    except Exception:
        pass
    # 5. Check for conflicting slots
    # If available_slots exists and none are available, it's a conflict
    available_slots = getattr(state, 'available_slots', [])
    if isinstance(available_slots, list) and len(available_slots) > 0:
        if not any(getattr(slot, 'available', True) for slot in available_slots):
            return edge_cases["conflicting_slots"]
    # No edge case detected
    return None

conversation_flows = {
    "greeting": ["Hello! I can help you book appointments. What works for you?"],
    "date_clarification": ["Which date did you have in mind?", "What day works best?"],
    "time_suggestion": ["I have these slots available:", "Would any of these work?"],
    "confirmation": ["Great! Let me confirm:", "Booking confirmed for:"]
} 