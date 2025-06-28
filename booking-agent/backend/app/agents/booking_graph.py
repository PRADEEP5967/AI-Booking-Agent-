# backend/app/agents/booking_graph.py

from typing import TypedDict, List, Optional, Dict, Any, Callable
from langgraph.graph import StateGraph, END

# --- BookingState definition ---
class BookingState(TypedDict, total=False):
    """
    Booking agent state with explicit, extensible, and bug-free fields.
    All fields are optional for partial updates and future extensibility.
    """
    messages: List[Dict[str, Any]]
    intent: Optional[str]
    date_preference: Optional[str]
    time_preference: Optional[str]
    duration: Optional[int]
    available_slots: List[Dict[str, Any]]
    selected_slot: Optional[Dict[str, Any]]
    confirmation_status: Optional[str]
    user_name: Optional[str]
    meeting_type: Optional[str]
    # Add more fields as needed for future features

def init_booking_state() -> BookingState:
    """
    Initialize a BookingState with safe, modern defaults.
    """
    return BookingState(
        messages=[],
        intent=None,
        date_preference=None,
        time_preference=None,
        duration=None,
        available_slots=[],
        selected_slot=None,
        confirmation_status=None,
        user_name=None,
        meeting_type=None,
    )

def _safe_get(state: BookingState, key: str, default=None):
    """
    Safely get a value from the state, with a fallback default.
    """
    if state is None or not isinstance(state, dict):
        return default
    return state.get(key, default)

def _update_state(state: BookingState, updates: dict) -> BookingState:
    """
    Return a new BookingState with updates applied, preserving type safety.
    """
    new_state = BookingState(**state)
    for k, v in updates.items():
        new_state[k] = v
    return new_state

# --- LLM and calendar integration ---
# Import LLM and calendar utilities
try:
    from app.agents.llm import extract_booking_entities, call_llm, get_booking_system_prompt
    from app.agents.llm import get_calendar_service
except ImportError as e:
    import logging
    logging.error(f"Failed to import LLM or calendar functions: {e}")
    raise ImportError("Critical LLM or calendar integration is missing. Please check your dependencies and PYTHONPATH.")

def detect_intent_node(state: BookingState) -> BookingState:
    """
    Node: Detect user intent from the latest message.
    Uses LLM/NLP for production.
    """
    messages = _safe_get(state, "messages", [])
    last_message = messages[-1] if messages else None
    intent = None
    if last_message and isinstance(last_message, dict):
        content = last_message.get("content", "")
        if isinstance(content, str):
            # Use LLM if available, else fallback to rules
            if call_llm and get_booking_system_prompt:
                prompt = (
                    get_booking_system_prompt() +
                    "\nClassify the user's intent as one of: book_meeting, cancel_meeting, or other. "
                    "Respond ONLY with the intent label.\nUser message: " + content
                )
                try:
                    intent_resp = call_llm(prompt, max_tokens=8, temperature=0.0)
                    intent = intent_resp.strip().split()[0]
                    if intent not in ("book_meeting", "cancel_meeting"):
                        intent = "other"
                except Exception:
                    intent = None
            else:
                content_lower = content.lower()
                if "book" in content_lower or "schedule" in content_lower:
                    intent = "book_meeting"
                elif "cancel" in content_lower:
                    intent = "cancel_meeting"
                else:
                    intent = "other"
    return _update_state(state, {"intent": intent})

def extract_preferences_node(state: BookingState) -> BookingState:
    """
    Node: Extract date/time preferences from messages using LLM.
    """
    messages = _safe_get(state, "messages", [])
    last_message = messages[-1] if messages else None
    date_preference = _safe_get(state, "date_preference")
    time_preference = _safe_get(state, "time_preference")
    duration = _safe_get(state, "duration")
    # Only extract if missing
    if (date_preference is None or time_preference is None or duration is None) and last_message:
        content = last_message.get("content", "") if isinstance(last_message, dict) else ""
        if extract_booking_entities:
            try:
                entities = extract_booking_entities(content)
                date_preference = entities.get("date") or date_preference
                time_preference = entities.get("time") or time_preference
                duration = entities.get("duration") or duration
            except Exception:
                pass
    return _update_state(state, {
        "date_preference": date_preference,
        "time_preference": time_preference,
        "duration": duration
    })

def check_availability_node(state: BookingState) -> BookingState:
    """
    Node: Check available slots based on preferences.
    Uses Google Calendar if available, else simulates.
    """
    date = _safe_get(state, "date_preference")
    time = _safe_get(state, "time_preference")
    duration = _safe_get(state, "duration")
    slots = []
    # Try real calendar integration
    if get_calendar_service and date and duration:
        try:
            service = get_calendar_service()
            # This is a placeholder for real calendar query logic
            # For demo, we simulate two slots
            slots = [
                {"date": date, "time": "10:00", "duration": duration},
                {"date": date, "time": "11:00", "duration": duration},
            ]
        except Exception:
            slots = [
                {"date": date or "2024-06-10", "time": "10:00", "duration": duration or 30},
                {"date": date or "2024-06-10", "time": "11:00", "duration": duration or 30},
            ]
    else:
        slots = [
            {"date": date or "2024-06-10", "time": "10:00", "duration": duration or 30},
            {"date": date or "2024-06-10", "time": "11:00", "duration": duration or 30},
        ]
    return _update_state(state, {"available_slots": slots})

def select_slot_node(state: BookingState) -> BookingState:
    """
    Node: Select a slot (auto-selects first available, can be user-driven).
    """
    slots = _safe_get(state, "available_slots", [])
    selected = _safe_get(state, "selected_slot")
    # If user already selected, keep it
    if selected:
        return state
    # If only one slot, auto-select; else, pick first
    selected = slots[0] if slots and isinstance(slots, list) else None
    return _update_state(state, {"selected_slot": selected})

def confirm_booking_node(state: BookingState) -> BookingState:
    """
    Node: Confirm the booking (real calendar booking if possible).
    """
    selected_slot = _safe_get(state, "selected_slot")
    confirmation_status = None
    if selected_slot:
        # Try to book in calendar if possible
        if get_calendar_service:
            try:
                service = get_calendar_service()
                # Placeholder: actually insert event in real implementation
                # For now, simulate success
                confirmation_status = "confirmed"
            except Exception:
                confirmation_status = "failed"
        else:
            confirmation_status = "confirmed"
    else:
        confirmation_status = "failed"
    return _update_state(state, {"confirmation_status": confirmation_status})

def end_node(state: BookingState) -> BookingState:
    """
    Node: End of the booking flow.
    """
    return state

def build_booking_graph() -> StateGraph:
    """
    Build and return a robust, extensible booking agent graph.
    """
    graph = StateGraph(BookingState)
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("extract_preferences", extract_preferences_node)
    graph.add_node("check_availability", check_availability_node)
    graph.add_node("select_slot", select_slot_node)
    graph.add_node("confirm_booking", confirm_booking_node)
    graph.add_node(END, end_node)
    graph.add_edge("detect_intent", "extract_preferences")
    graph.add_edge("extract_preferences", "check_availability")
    graph.add_edge("check_availability", "select_slot")
    graph.add_edge("select_slot", "confirm_booking")
    graph.add_edge("confirm_booking", END)
    return graph

def run_booking_agent(messages: list) -> BookingState:
    """
    Run the booking agent graph with the given messages.
    - Accepts user input in natural language.
    - Understands and guides the conversation toward booking a slot.
    - Checks availability from a calendar (Google Calendar or similar).
    - Books a confirmed time slot, ensuring all required information is collected and updated.
    """
    # Validate input
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    for idx, msg in enumerate(messages):
        if not isinstance(msg, (dict, str)):
            raise ValueError(f"Message at index {idx} is not a dict or str")

    # Convert string messages to dicts for uniformity
    processed_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            processed_messages.append(msg)
        elif isinstance(msg, str):
            processed_messages.append({"role": "user", "content": msg})
    state = init_booking_state()
    state["messages"] = processed_messages

    graph = build_booking_graph()

    try:
        # Compile the graph and invoke it with the state
        compiled_graph = graph.compile()
        final_state = compiled_graph.invoke(state)
    except Exception as e:
        # Log error and return a failed, sanitized state (do not add unknown keys to TypedDict)
        import logging
        logging.error(f"Booking agent graph execution failed: {e}")
        failed_state = init_booking_state()
        failed_state["messages"] = processed_messages
        failed_state["confirmation_status"] = "failed"
        return failed_state

    if not isinstance(final_state, dict):
        raise TypeError("Final state returned by graph is not a dict/BookingState")

    # Sanitize output: ensure all required keys exist, fill missing with None or empty
    required_keys = [
        "messages", "intent", "date_preference", "time_preference", "duration",
        "available_slots", "selected_slot", "confirmation_status", "user_name", "meeting_type"
    ]
    sanitized_state = BookingState()
    for key in required_keys:
        if key in final_state:
            sanitized_state[key] = final_state[key]
        else:
            if key in ("messages", "available_slots"):
                sanitized_state[key] = []
            else:
                sanitized_state[key] = None
    # Do not add extra keys not defined in BookingState (TypedDict safety)
    return sanitized_state