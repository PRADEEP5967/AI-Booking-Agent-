"""
Booking Agent LLM Integration Module

This module provides the core logic for a conversational booking agent that:
- Accepts user input in natural language
- Understands and guides the conversation toward booking a slot
- Checks availability from a calendar (Google Calendar or similar)
- Books a confirmed time slot, ensuring all required information is collected and updated
"""

import logging
import asyncio
from typing import Optional, Any, Dict, Union
from functools import lru_cache
from app.config.settings import settings
import time

logger = logging.getLogger(__name__)

# Try importing OpenAI, fallback to None if unavailable
try:
    import openai
    _openai_available = True
except ImportError:
    logger.warning("openai package not installed. LLM calls will not work.")
    openai = None
    _openai_available = False

# --- Calendar Integration (Google Calendar) ---
try:
    from googleapiclient.discovery import build as google_build
    from google.oauth2 import service_account
    _calendar_available = True
except ImportError:
    logger.warning("Google Calendar integration not available.")
    google_build = None
    service_account = None
    _calendar_available = False

# --- LLM Call Utilities ---

async def async_call_llm(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 256,
    temperature: float = 0.2,
    system_prompt: Optional[str] = None,
    extra_messages: Optional[list] = None,
    timeout: int = 30
) -> str:
    """
    Asynchronously call the language model with a given prompt using OpenAI API.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string")
    if not _openai_available or openai is None:
        raise RuntimeError("openai package is not installed.")
    if not settings.LLM_API_KEY:
        raise RuntimeError("OpenAI API key is not set in settings.")

    openai.api_key = settings.LLM_API_KEY
    model = model or settings.LLM_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": prompt})

    try:
        # Fix: Use asyncio.get_running_loop() if available, else get_event_loop()
        if hasattr(openai, "AsyncOpenAI"):
            client = openai.AsyncOpenAI(api_key=settings.LLM_API_KEY)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
            )
            content = getattr(response.choices[0].message, "content", None)
            if content is None:
                raise RuntimeError("LLM response content is None")
            result = content.strip()
        else:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            def sync_call():
                try:
                    import openai as _openai
                except ImportError:
                    raise RuntimeError("openai package is not installed.")
                if not hasattr(_openai, "ChatCompletion") and not hasattr(_openai, "chat"):
                    raise RuntimeError("openai.ChatCompletion is not available.")
                # Support both old and new OpenAI SDKs
                if hasattr(_openai, "ChatCompletion") and hasattr(getattr(_openai, "ChatCompletion"), "create"):
                    # Old SDK (openai<1.0)
                    return getattr(_openai, "ChatCompletion").create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                elif hasattr(_openai, "chat") and hasattr(getattr(_openai, "chat"), "completions") and hasattr(getattr(_openai.chat, "completions"), "create"):
                    # New SDK (openai>=1.0)
                    return getattr(_openai.chat, "completions").create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                else:
                    raise RuntimeError("No supported OpenAI chat completion method found.")
            response = await loop.run_in_executor(
                None,
                sync_call
            )
            # Fix: Defensive extraction of message content
            message = None
            if hasattr(response.choices[0], "message"):
                msg = response.choices[0].message
                if isinstance(msg, dict):
                    message = msg.get("content")
                else:
                    message = getattr(msg, "content", None)
            elif isinstance(response.choices[0], dict):
                message = response.choices[0].get("message", {}).get("content")
            else:
                # Try to get message.content attribute if present
                msg = getattr(response.choices[0], "message", None)
                if msg is not None:
                    message = getattr(msg, "content", None)
            if message is None:
                raise RuntimeError("LLM response content is None")
            result = message.strip()
        return result
    except Exception as e:
        logger.error(f"Async LLM call failed: {e}")
        raise RuntimeError(f"Failed to get response from LLM: {e}")

def call_llm(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 256,
    temperature: float = 0.2,
    system_prompt: Optional[str] = None,
    extra_messages: Optional[list] = None,
    timeout: int = 30
) -> str:
    """
    Synchronously call the language model with a given prompt using OpenAI API.
    """
    try:
        # Fix: Use asyncio.new_event_loop() if already in a running loop
        try:
            return asyncio.run(
                async_call_llm(
                    prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    extra_messages=extra_messages,
                    timeout=timeout,
                )
            )
        except RuntimeError as e:
            # If already in an event loop (e.g. FastAPI), fallback to thread
            try:
                import nest_asyncio  # type: ignore
                nest_asyncio.apply()
            except ImportError:
                logger.warning("nest_asyncio not installed, event loop issues may occur.")
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            coro = async_call_llm(
                prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                extra_messages=extra_messages,
                timeout=timeout,
            )
            return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"call_llm failed: {e}")
        raise

# --- Booking Agent Conversation Logic ---

@lru_cache(maxsize=64)
def get_booking_system_prompt() -> str:
    """
    System prompt for the booking agent LLM.
    """
    return (
        "You are a helpful assistant for booking meetings. "
        "Your job is to guide the user to book a time slot. "
        "Ask for missing information (date, time, duration) if not provided. "
        "Once all required information is collected, confirm the booking. "
        "Check the calendar for availability before confirming. "
        "If the slot is unavailable, suggest alternatives. "
        "Always respond in a friendly, concise manner."
    )

@lru_cache(maxsize=64)
def get_entity_extraction_prompt() -> str:
    """
    Cached prompt template for entity extraction.
    """
    return (
        "Extract the date, time, and duration (in minutes) from the user's message. "
        "If any value is missing, return null for that field. "
        "Respond ONLY with a JSON object like: "
        "{\"date\": \"2024-06-10\", \"time\": \"10:00\", \"duration\": 30}\n"
        "User message: "
    )

def extract_booking_entities(message: str) -> Dict[str, Union[str, int, None]]:
    """
    Use the LLM to extract booking entities (date, time, duration) from a user message.
    Returns a dict with keys: date, time, duration (if found).
    """
    import json
    prompt = get_entity_extraction_prompt() + message
    try:
        response = call_llm(prompt, max_tokens=128, temperature=0.0)
        # Fix: Try to extract JSON robustly, fallback to None on error
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and end > start:
            response_json = response[start:end+1]
        else:
            response_json = response
        try:
            entities = json.loads(response_json)
        except Exception as e:
            logger.error(f"JSON decode error in extract_booking_entities: {e} | response: {response_json}")
            return {"date": None, "time": None, "duration": None}
        for key in ("date", "time", "duration"):
            if key not in entities:
                entities[key] = None
        return entities
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return {"date": None, "time": None, "duration": None}

async def async_extract_booking_entities(message: str) -> Dict[str, Union[str, int, None]]:
    """
    Async version of extract_booking_entities for fast, non-blocking use.
    """
    import json
    prompt = get_entity_extraction_prompt() + message
    try:
        response = await async_call_llm(prompt, max_tokens=128, temperature=0.0)
        # Fix: Try to extract JSON robustly, fallback to None on error
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and end > start:
            response_json = response[start:end+1]
        else:
            response_json = response
        try:
            entities = json.loads(response_json)
        except Exception as e:
            logger.error(f"JSON decode error in async_extract_booking_entities: {e} | response: {response_json}")
            return {"date": None, "time": None, "duration": None}
        for key in ("date", "time", "duration"):
            if key not in entities:
                entities[key] = None
        return entities
    except Exception as e:
        logger.error(f"Async entity extraction failed: {e}")
        return {"date": None, "time": None, "duration": None}

# --- Calendar Availability and Booking ---

def get_calendar_service():
    """
    Returns an authenticated Google Calendar service object.
    """
    if not _calendar_available:
        raise RuntimeError("Google Calendar integration is not available.")
    credentials_info = getattr(settings, "GOOGLE_SERVICE_ACCOUNT_INFO", None)
    if not credentials_info:
        raise RuntimeError("Google service account info not set in settings.")
    if service_account is None:
        raise RuntimeError("google.oauth2.service_account is not available.")
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    if google_build is None:
        raise RuntimeError("googleapiclient.discovery.build is not available.")
    service = google_build("calendar", "v3", credentials=credentials)
    return service

def check_availability(date: str, time_: str, duration: int, calendar_id: Optional[str] = None) -> bool:
    """
    Checks if the requested slot is available in the calendar.
    """
    from datetime import datetime, timedelta
    if not _calendar_available:
        logger.warning("Calendar check requested but integration is unavailable.")
        return False
    if not (isinstance(date, str) and isinstance(time_, str) and isinstance(duration, int)):
        logger.error(f"Invalid types for check_availability: date={date}, time_={time_}, duration={duration}")
        return False
    try:
        service = get_calendar_service()
        calendar_id = calendar_id or getattr(settings, "DEFAULT_CALENDAR_ID", None)
        if not calendar_id:
            logger.error("DEFAULT_CALENDAR_ID not set in settings.")
            return False
        start_dt = datetime.fromisoformat(f"{date}T{time_}")
        end_dt = start_dt + timedelta(minutes=duration)
        # Fix: Use RFC3339 format with timezone if needed
        time_min = start_dt.isoformat() + "Z" if start_dt.tzinfo is None else start_dt.isoformat()
        time_max = end_dt.isoformat() + "Z" if end_dt.tzinfo is None else end_dt.isoformat()
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        return len(events) == 0
    except Exception as e:
        logger.error(f"Error checking calendar availability: {e}")
        return False

def book_time_slot(date: str, time_: str, duration: int, summary: str = "Meeting", calendar_id: Optional[str] = None) -> bool:
    """
    Books the requested slot in the calendar if available.
    """
    from datetime import datetime, timedelta
    if not _calendar_available:
        logger.warning("Booking requested but calendar integration is unavailable.")
        return False
    if not (isinstance(date, str) and isinstance(time_, str) and isinstance(duration, int)):
        logger.error(f"Invalid types for book_time_slot: date={date}, time_={time_}, duration={duration}")
        return False
    try:
        service = get_calendar_service()
        calendar_id = calendar_id or getattr(settings, "DEFAULT_CALENDAR_ID", None)
        if not calendar_id:
            logger.error("DEFAULT_CALENDAR_ID not set in settings.")
            return False
        start_dt = datetime.fromisoformat(f"{date}T{time_}")
        end_dt = start_dt + timedelta(minutes=duration)
        timezone = getattr(settings, "DEFAULT_TIMEZONE", "UTC")
        event = {
            "summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone},
        }
        service.events().insert(calendarId=calendar_id, body=event).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to book slot: {e}")
        return False

# --- Main Booking Agent Logic ---

def guide_booking_conversation(user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Accepts user input, guides the conversation, checks availability, and books a slot if possible.
    Returns a dict with the agent's reply and booking status.
    """
    # Step 1: Extract entities from user message
    entities = extract_booking_entities(user_message)
    missing = [k for k, v in entities.items() if not v]
    reply = ""
    booking_status = "incomplete"
    booked = False

    # Step 2: If missing info, ask for it
    if missing:
        reply = f"To book your meeting, could you please provide the following: {', '.join(missing)}?"
    else:
        # Step 3: Check calendar availability
        date = entities.get("date")
        time_ = entities.get("time")
        duration = entities.get("duration")
        if not (isinstance(date, str) and isinstance(time_, str) and isinstance(duration, int)):
            reply = "Sorry, I couldn't understand the date, time, or duration. Could you please rephrase?"
            booking_status = "error"
        else:
            available = check_availability(date, time_, duration)
            if available:
                # Step 4: Book the slot
                booked = book_time_slot(date, time_, duration)
                if booked:
                    reply = (
                        f"Your meeting is booked for {date} at {time_} "
                        f"for {duration} minutes. Looking forward to it!"
                    )
                    booking_status = "confirmed"
                else:
                    reply = "Sorry, I was unable to book your meeting due to a technical issue."
                    booking_status = "error"
            else:
                reply = (
                    f"Sorry, the slot on {date} at {time_} is not available. "
                    "Would you like to try a different time?"
                )
                booking_status = "unavailable"

    # Optionally, update context with latest info
    if context is not None and isinstance(context, dict):
        context.update(entities)
        context["booking_status"] = booking_status

    return {
        "reply": reply,
        "entities": entities,
        "booking_status": booking_status,
        "booked": booked,
    }

# Async version for API endpoints
async def async_guide_booking_conversation(user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Async version of guide_booking_conversation.
    """
    entities = await async_extract_booking_entities(user_message)
    missing = [k for k, v in entities.items() if not v]
    reply = ""
    booking_status = "incomplete"
    booked = False

    if missing:
        reply = f"To book your meeting, could you please provide the following: {', '.join(missing)}?"
    else:
        date = entities.get("date")
        time_ = entities.get("time")
        duration = entities.get("duration")
        if not (isinstance(date, str) and isinstance(time_, str) and isinstance(duration, int)):
            reply = "Sorry, I couldn't understand the date, time, or duration. Could you please rephrase?"
            booking_status = "error"
        else:
            available = check_availability(date, time_, duration)
            if available:
                booked = book_time_slot(date, time_, duration)
                if booked:
                    reply = (
                        f"Your meeting is booked for {date} at {time_} "
                        f"for {duration} minutes. Looking forward to it!"
                    )
                    booking_status = "confirmed"
                else:
                    reply = "Sorry, I was unable to book your meeting due to a technical issue."
                    booking_status = "error"
            else:
                reply = (
                    f"Sorry, the slot on {date} at {time_} is not available. "
                    "Would you like to try a different time?"
                )
                booking_status = "unavailable"

    if context is not None and isinstance(context, dict):
        context.update(entities)
        context["booking_status"] = booking_status

    return {
        "reply": reply,
        "entities": entities,
        "booking_status": booking_status,
        "booked": booked,
    }

def retry_openai_call(func, retries=3, delay=2, *args, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"OpenAI call failed (attempt {attempt+1}), retrying: {e}")
                time.sleep(delay)
            else:
                logger.error(f"OpenAI call failed after {retries} attempts: {e}")
                raise

# End of booking agent LLM service module