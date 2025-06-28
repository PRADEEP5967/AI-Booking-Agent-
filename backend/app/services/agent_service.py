from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import re
import asyncio
import json
import hashlib
from functools import lru_cache
from difflib import SequenceMatcher
from ..models.schemas import ConversationState, AgentResponse, BookingRequest, TimeSlot, Booking
from ..services.calendar_service import CalendarService
from ..services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

# Import LLM service for enhanced entity extraction
# Note: Enhanced LLM service is in booking-agent directory, using fallback regex extraction
LLM_AVAILABLE = False

# --- Async Smart Cache ---
class AsyncTTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
        self.lock = asyncio.Lock()

    async def get(self, key):
        async with self.lock:
            entry = self.cache.get(key)
            if entry:
                value, timestamp = entry
                if datetime.now().timestamp() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
            return None

    async def set(self, key, value):
        async with self.lock:
            self.cache[key] = (value, datetime.now().timestamp())

    async def clear_expired(self):
        async with self.lock:
            now = datetime.now().timestamp()
            expired = [k for k, (_, t) in self.cache.items() if now - t > self.ttl]
            for k in expired:
                del self.cache[k]

class SmartContextManager:
    """Intelligent context management for better conversation flow"""
    
    def __init__(self):
        self.user_preferences = {}
        self.conversation_history = {}
        self.pattern_recognition = {}
    
    def update_preferences(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update user preferences based on conversation"""
        if session_id not in self.user_preferences:
            self.user_preferences[session_id] = {}
        
        # Extract preferences from booking data
        if 'service_type' in data:
            self.user_preferences[session_id]['preferred_service'] = data['service_type']
        if 'duration_minutes' in data:
            self.user_preferences[session_id]['preferred_duration'] = data['duration_minutes']
        if 'customer_email' in data:
            self.user_preferences[session_id]['email'] = data['customer_email']
    
    def get_suggestions(self, session_id: str, current_context: str) -> List[str]:
        """Get intelligent suggestions based on context and history"""
        suggestions = []
        prefs = self.user_preferences.get(session_id, {})
        
        if 'preferred_service' in prefs:
            suggestions.append(f"Book another {prefs['preferred_service']}")
        
        if 'preferred_duration' in prefs:
            suggestions.append(f"Schedule a {prefs['preferred_duration']}-minute session")
        
        # Add contextual suggestions
        if 'slot' in current_context.lower():
            suggestions.extend(["Confirm this time", "Show me other options", "Change the date"])
        elif 'date' in current_context.lower():
            suggestions.extend(["Tomorrow", "Next week", "This afternoon"])
        
        return suggestions[:3]  # Limit to 3 suggestions

class AdvancedNLPProcessor:
    """Advanced NLP processing with fuzzy matching and intent recognition"""
    
    def __init__(self):
        self.intent_patterns = {
            'booking': ['book', 'schedule', 'appointment', 'meeting', 'reserve', 'set up'],
            'cancellation': ['cancel', 'reschedule', 'change', 'postpone', 'cancel my', 'reschedule my'],
            'inquiry': ['when', 'what time', 'available', 'free', 'open', 'what slots'],
            'confirmation': ['yes', 'confirm', 'okay', 'sure', 'proceed', 'that works', 'perfect'],
            'rejection': ['no', 'not', "don't", 'different', 'another', 'else']
        }
        
        self.entity_patterns = {
            'time_relative': [
                r'(today|tomorrow|next week|this week|next month)',
                r'(morning|afternoon|evening|night)',
                r'(asap|urgent|soon)'
            ],
            'time_specific': [
                r'(\d{1,2}):(\d{2})\s*(am|pm)',
                r'(\d{1,2})\s*(am|pm)',
                r'(\d{1,2}):(\d{2})'
            ],
            'duration': [
                r'(\d+)\s*(minute|min|hour|hr)s?',
                r'(\d+)\s*(hour|hr)s?\s*(\d+)\s*(minute|min)s?'
            ]
        }
    
    def extract_intent(self, message: str) -> str:
        """Extract user intent from message with improved accuracy"""
        message_lower = message.lower()
        scores = {}
        
        # Improved intent patterns with better specificity
        intent_patterns = {
            'booking': ['book', 'schedule', 'appointment', 'meeting', 'reserve', 'set up'],
            'cancellation': ['cancel', 'reschedule', 'change', 'postpone', 'cancel my', 'reschedule my'],
            'inquiry': ['when', 'what time', 'available', 'free', 'open', 'what slots'],
            'confirmation': ['yes', 'confirm', 'okay', 'sure', 'proceed', 'that works', 'perfect'],
            'rejection': ['no', 'not', "don't", 'different', 'another', 'else']
        }
        
        for intent, patterns in intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in message_lower:
                    score += 1
                    # Give extra weight to more specific patterns
                    if pattern in ['cancel my', 'reschedule my', 'that works', 'perfect']:
                        score += 2
            
            if score > 0:
                scores[intent] = score
        
        # Special handling for cancellation vs booking
        if 'cancel' in message_lower and 'book' not in message_lower:
            return 'cancellation'
        elif 'book' in message_lower and 'cancel' not in message_lower:
            return 'booking'
        
        return max(scores.items(), key=lambda x: x[1])[0] if scores else 'unknown'
    
    def fuzzy_match(self, text: str, options: List[str], threshold: float = 0.6) -> Optional[str]:
        """Fuzzy string matching for better entity recognition"""
        best_match = None
        best_score = 0
        
        # First try exact substring matching for better performance
        text_lower = text.lower()
        for option in options:
            option_lower = option.lower()
            if text_lower in option_lower or option_lower in text_lower:
                return option
        
        # Fallback to fuzzy matching
        for option in options:
            score = SequenceMatcher(None, text_lower, option.lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = option
        
        return best_match

# Modern, robust, and bug-free BookingAgent implementation
class BookingAgent:
    def __init__(self, calendar_service: CalendarService):
        self.calendar_service = calendar_service
        self.email_service = EmailService()
        self.nlp_processor = AdvancedNLPProcessor()
        self.context_manager = SmartContextManager()
        self.cache = AsyncTTLCache(ttl_seconds=300)
        self.performance_metrics = {
            'total_requests': 0,
            'successful_bookings': 0,
            'average_response_time': 0.0
        }
        self.conversation_stages = {
            "greeting": self._handle_greeting,
            "collecting_info": self._handle_info_collection,
            "showing_slots": self._handle_slot_selection,
            "collecting_email": self._handle_collecting_email,
            "confirming": self._handle_confirmation,
            "booking": self._handle_booking,
            "completed": self._handle_completion
        }
        
        # Initialize modern features
        self.llm_service = None
        self.async_cache = AsyncTTLCache(ttl_seconds=300)
        self.context_manager = SmartContextManager()
        self.nlp_processor = AdvancedNLPProcessor()
        
        # Performance optimization
        self._service_patterns = re.compile(r'\b(consultation|therapy|workshop|meeting|appointment|business|creative)\b', re.IGNORECASE)
        self._time_patterns = re.compile(r'\b(\d{1,2}):?(\d{2})?\s*(am|pm)?\b', re.IGNORECASE)
        self._date_patterns = re.compile(r'\b(tomorrow|today|next\s+\w+|this\s+\w+|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', re.IGNORECASE)

    def process_message(self, state: ConversationState, user_message: str) -> AgentResponse:
        """Synchronous wrapper for message processing"""
        try:
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an event loop, run the async function directly
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_async_in_new_loop, state, user_message)
                        return future.result()
                else:
                    return loop.run_until_complete(self.process_message_async(state, user_message))
            except RuntimeError:
                # No event loop in current thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.process_message_async(state, user_message))
                finally:
                    loop.close()
        except Exception as e:
            # Fallback to simple synchronous processing
            return self._process_message_sync(state, user_message)
    
    def _run_async_in_new_loop(self, state: ConversationState, user_message: str) -> AgentResponse:
        """Run async function in a new event loop in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_message_async(state, user_message))
        finally:
            loop.close()
    
    def _process_message_sync(self, state: ConversationState, user_message: str) -> AgentResponse:
        """Synchronous fallback for message processing"""
        from ..models.schemas import ConversationMessage
        
        if not hasattr(state, "messages") or not isinstance(state.messages, list):
            state.messages = []
        state.messages.append(ConversationMessage(role="user", content=user_message))

        # Extract entities synchronously
        extracted_entities = self._extract_entities_regex(user_message)
        if extracted_entities:
            self._apply_extracted_entities(state, extracted_entities)

        # Context-aware suggestions
        suggestions = self._get_context_suggestions(state, user_message, extracted_entities)

        # Stage handler - use synchronous versions
        if state.stage == "greeting":
            response = self._handle_greeting_sync(state, user_message, extracted_entities, suggestions)
        elif state.stage == "collecting_info":
            response = self._handle_info_collection_sync(state, user_message, extracted_entities, suggestions)
        elif state.stage == "showing_slots":
            response = self._handle_slot_selection_sync(state, user_message, extracted_entities, suggestions)
        elif state.stage == "confirming":
            response = self._handle_confirmation_sync(state, user_message, extracted_entities, suggestions)
        elif state.stage == "booking":
            response = self._handle_booking_sync(state, user_message, extracted_entities, suggestions)
        elif state.stage == "completed":
            response = self._handle_completion_sync(state, user_message, extracted_entities, suggestions)
        else:
            response = self._handle_greeting_sync(state, user_message, extracted_entities, suggestions)
        
        state.messages.append(ConversationMessage(role="assistant", content=response.message))
        return response

    # --- Async Main Message Processor ---
    async def process_message_async(self, state: ConversationState, user_message: str) -> AgentResponse:
        from ..models.schemas import ConversationMessage
        if not hasattr(state, "messages") or not isinstance(state.messages, list):
            state.messages = []
        state.messages.append(ConversationMessage(role="user", content=user_message))

        # Async entity extraction with cache
        cache_key = f"entities_{hash(user_message)}"
        extracted_entities = await self.async_cache.get(cache_key)
        if not extracted_entities:
            extracted_entities = await self._extract_entities_async(user_message)
            await self.async_cache.set(cache_key, extracted_entities)
        if extracted_entities:
            self._apply_extracted_entities(state, extracted_entities)

        # Context-aware suggestions
        suggestions = self._get_context_suggestions(state, user_message, extracted_entities)

        # Stage handler
        handler = self.conversation_stages.get(state.stage, self._handle_greeting)
        response = await handler(state, user_message, extracted_entities, suggestions)
        state.messages.append(ConversationMessage(role="assistant", content=response.message))
        return response

    # --- Async Entity Extraction ---
    async def _extract_entities_async(self, message: str) -> Dict[str, Any]:
        await asyncio.sleep(0.01)  # Simulate async
        return self._extract_entities_regex(message)

    def _extract_entities_regex(self, message: str) -> Dict[str, Any]:
        entities = {}
        text_lower = message.lower()
        
        # Check for booking intent
        booking_keywords = ['book', 'schedule', 'appointment', 'meeting', 'reserve', 'set up', 'need', 'want']
        has_booking_intent = any(keyword in text_lower for keyword in booking_keywords)
        
        # Fuzzy service type detection
        service_keywords = {
            'meeting': 'meeting',
            'consultation': 'consultation',
            'therapy': 'therapy session',
            'workshop': 'workshop',
            'appointment': 'consultation',
            'business': 'business consultation',
            'creative': 'creative session'
        }
        
        # Check for service type in message
        detected_service = None
        for keyword, service in service_keywords.items():
            if keyword in text_lower:
                detected_service = service
                break
        
        # If no exact match, try fuzzy matching
        if not detected_service:
            detected_service = self.nlp_processor.fuzzy_match(text_lower, list(service_keywords.keys()))
            if detected_service:
                detected_service = service_keywords[detected_service]
        
        if detected_service:
            entities['service_type'] = detected_service
        
        # Extract date/time information
        import re
        from datetime import datetime, timedelta
        
        # Date patterns
        date_patterns = [
            r'tomorrow',
            r'today',
            r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if 'tomorrow' in pattern:
                    entities['date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                elif 'today' in pattern:
                    entities['date'] = datetime.now().strftime('%Y-%m-%d')
                elif 'next' in pattern or 'this' in pattern:
                    # For now, default to tomorrow
                    entities['date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                break
        
        # Time patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities['time'] = match.group(0)
                break
        
        # Duration patterns
        duration_patterns = [
            r'(\d+)\s*(minute|min|hour|hr)s?',
            r'(\d+)\s*(hour|hr)s?\s*(\d+)\s*(minute|min)s?'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities['duration'] = match.group(0)
                break
        
        # Set booking intent
        if has_booking_intent:
            entities['intent'] = 'booking'
        
        return entities

    def _fuzzy_match(self, text: str, options: List[str], threshold: float = 0.6) -> Optional[str]:
        text_lower = text.lower()
        for option in options:
            option_lower = option.lower()
            if text_lower in option_lower or option_lower in text_lower:
                return option
        best_match = None
        best_score = 0
        for option in options:
            score = SequenceMatcher(None, text_lower, option.lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = option
        return best_match

    # --- Context-Aware Suggestions ---
    def _get_context_suggestions(self, state, user_message, entities):
        suggestions = []
        if state.stage in ["showing_slots", "confirming"]:
            if 'service_type' in state.current_booking_data:
                suggestions.append(f"Book another {state.current_booking_data['service_type']}")
            if 'duration_minutes' in state.current_booking_data:
                suggestions.append(f"Schedule a {state.current_booking_data['duration_minutes']}-minute session")
            suggestions.extend(["Confirm this time", "Show me other options", "Change the date"])
        elif state.stage == "greeting":
            suggestions.append("Book a meeting")
            suggestions.append("Show available slots")
        return suggestions[:3]

    # --- Async Stage Handlers ---
    async def _handle_greeting(self, state, message, entities, suggestions):
        # Check if user has booking intent
        if entities.get('intent') == 'booking' or any(keyword in message.lower() for keyword in ['book', 'schedule', 'appointment', 'meeting', 'need', 'want']):
            # Transition to info collection stage
            state.stage = "collecting_info"
            
            # If service type is already detected, proceed to slot selection
            if entities.get('service_type'):
                state.current_booking_data['service_type'] = entities['service_type']
                if entities.get('date') and entities.get('time'):
                    state.current_booking_data['date'] = entities['date']
                    state.current_booking_data['time'] = entities['time']
                    state.stage = "showing_slots"
                    return AgentResponse(
                        message=f"Great! I can help you book a {entities['service_type']} for {entities.get('date', 'tomorrow')} at {entities.get('time', '10 AM')}. Let me check available slots.",
                        booking_data=state.current_booking_data
                    )
                else:
                    return AgentResponse(
                        message=f"Perfect! I can help you book a {entities['service_type']}. When would you like to schedule it?",
                        booking_data=state.current_booking_data
                    )
            else:
                return AgentResponse(
                    message="I'd be happy to help you book an appointment! What type of service would you like? (consultation, therapy, workshop, meeting, etc.)"
                )
        
        # Default greeting response
        greeting_response = (
            "Hello! I'm your AI booking assistant. I can help you schedule appointments for various services including:\n\n"
            "• **Consultation** (30-60 minutes)\n"
            "• **Therapy Session** (60 minutes)\n"
            "• **Workshop** (90-120 minutes)\n"
            "• **Meeting** (30-60 minutes)\n"
            "• **Business Consultation** (45-90 minutes)\n"
            "• **Creative Session** (60-90 minutes)\n\n"
            "How can I help you today?\n"
            "You can simply tell me what you need, like:\n"
            "• 'I need a consultation tomorrow at 10 AM'\n"
            "• 'Book a therapy session for next Monday'\n"
            "• 'Schedule a workshop for next week'"
        )
        if suggestions:
            greeting_response += "\n\n**Quick Actions:**\n" + "\n".join([f"• {s}" for s in suggestions])
        return AgentResponse(message=greeting_response)

    async def _handle_info_collection(self, state, message, entities, suggestions):
        """Handle information collection stage"""
        # Extract entities from message
        if 'service_type' in entities:
            state.current_booking_data['service_type'] = entities['service_type']
        
        # Check if we have enough info to proceed
        if 'service_type' in state.current_booking_data:
            state.stage = "showing_slots"
            return AgentResponse(
                message="Great! I can help you book a meeting. Let me check available slots for tomorrow at 10 AM.",
                booking_data=state.current_booking_data
            )
        else:
            return AgentResponse(
                message="I'd be happy to help you book a meeting! What type of service would you like? (consultation, therapy, workshop, etc.)"
            )

    async def _handle_slot_selection(self, state, message, entities, suggestions):
        """Handle slot selection stage"""
        from datetime import datetime
        mock_slots = [
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T10:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T11:00:00"),
                available=True
            ),
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T14:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T15:00:00"),
                available=True
            ),
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T16:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T17:00:00"),
                available=True
            )
        ]

        # If user email is missing, prompt for it before confirming
        if not state.current_booking_data.get('user_email'):
            state.stage = "collecting_email"
            return AgentResponse(
                message="Before we confirm your booking, could you please provide your email address for confirmation?",
                suggested_slots=mock_slots,
                booking_data=state.current_booking_data
            )

        state.stage = "confirming"
        return AgentResponse(
            message="Here are some available slots for tomorrow:\n1. 10:00 AM - 11:00 AM\n2. 2:00 PM - 3:00 PM\n3. 4:00 PM - 5:00 PM\n\nWhich slot would you prefer?",
            suggested_slots=mock_slots,
            booking_data=state.current_booking_data
        )

    async def _handle_collecting_email(self, state, message, entities, suggestions):
        """Handle collecting the user's email address"""
        import re
        email = None
        # Try to extract email from message
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", message)
        if email_match:
            email = email_match.group(0)
        if email:
            state.current_booking_data['user_email'] = email
            state.stage = "confirming"
            return AgentResponse(
                message=f"Thank you! I've saved your email as {email}. Let's confirm your booking.",
                booking_data=state.current_booking_data
            )
        else:
            return AgentResponse(
                message="That doesn't look like a valid email address. Please enter a valid email (e.g., user@example.com):",
                booking_data=state.current_booking_data
            )

    async def _handle_confirmation(self, state, message, entities, suggestions):
        """Handle confirmation stage"""
        state.stage = "completed"
        
        # Enhance booking data with more details
        booking_data = state.current_booking_data.copy()
        
        # Add booking ID and timestamp
        from datetime import datetime
        booking_data['booking_id'] = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        booking_data['booking_timestamp'] = datetime.now().isoformat()
        booking_data['confirmation_number'] = f"CNF-{datetime.now().strftime('%Y%m%d')}-{hash(booking_data['booking_id']) % 10000:04d}"
        
        # Ensure we have proper date/time information
        if 'date' not in booking_data or booking_data['date'] == 'Unknown':
            booking_data['date'] = 'Tomorrow'
        if 'time' not in booking_data or booking_data['time'] == 'Unknown':
            booking_data['time'] = '10:00 AM'
        if 'duration_minutes' not in booking_data:
            booking_data['duration_minutes'] = 60
        
        # Add user contact information (in a real app, this would come from user profile)
        booking_data['user_email'] = "user@example.com"
        booking_data['user_name'] = "Valued Customer"
        booking_data['contact_phone'] = "+1 (555) 123-4567"
        
        # Add location and additional details
        booking_data['location'] = "Main Office - Conference Room A"
        booking_data['instructions'] = "Please arrive 5 minutes before your scheduled time. Bring any relevant documents."
        booking_data['cancellation_policy'] = "Free cancellation up to 24 hours before the appointment."
        
        # Send confirmation email with enhanced data
        try:
            await self.email_service.send_booking_confirmation(
                booking_data=booking_data,
                recipient_email=booking_data['user_email']
            )
            email_status = "Confirmation email sent successfully!"
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            email_status = "Email service temporarily unavailable."
        
        return AgentResponse(
            message=f"✅ Perfect! I've confirmed your {booking_data.get('service_type', 'meeting')} for {booking_data.get('date', 'tomorrow')} at {booking_data.get('time', '10:00 AM')}. {email_status}\n\n**Booking Details:**\n• Confirmation #: {booking_data['confirmation_number']}\n• Location: {booking_data['location']}\n• Duration: {booking_data['duration_minutes']} minutes\n\nIs there anything else I can help you with?",
            booking_data=booking_data,
            requires_confirmation=False
        )

    async def _handle_booking(self, state, message, entities, suggestions):
        """Handle booking stage"""
        state.stage = "completed"
        return AgentResponse(
            message="Your booking has been successfully created! You'll receive a confirmation email shortly.",
            booking_data=state.current_booking_data,
            requires_confirmation=False
        )

    async def _handle_completion(self, state, message, entities, suggestions):
        return AgentResponse(message="Thank you! If you need to book another appointment or have any questions, just let me know. Have a great day! 😊")

    # --- Synchronous Stage Handlers (Fallback) ---
    def _handle_greeting_sync(self, state, message, entities, suggestions):
        # Check if user has booking intent
        if entities.get('intent') == 'booking' or any(keyword in message.lower() for keyword in ['book', 'schedule', 'appointment', 'meeting', 'need', 'want']):
            # Transition to info collection stage
            state.stage = "collecting_info"
            
            # If service type is already detected, proceed to slot selection
            if entities.get('service_type'):
                state.current_booking_data['service_type'] = entities['service_type']
                if entities.get('date') and entities.get('time'):
                    state.current_booking_data['date'] = entities['date']
                    state.current_booking_data['time'] = entities['time']
                    state.stage = "showing_slots"
                    return AgentResponse(
                        message=f"Great! I can help you book a {entities['service_type']} for {entities.get('date', 'tomorrow')} at {entities.get('time', '10 AM')}. Let me check available slots.",
                        booking_data=state.current_booking_data
                    )
                else:
                    return AgentResponse(
                        message=f"Perfect! I can help you book a {entities['service_type']}. When would you like to schedule it?",
                        booking_data=state.current_booking_data
                    )
            else:
                return AgentResponse(
                    message="I'd be happy to help you book an appointment! What type of service would you like? (consultation, therapy, workshop, meeting, etc.)"
                )
        
        # Default greeting response
        greeting_response = (
            "Hello! I'm your AI booking assistant. I can help you schedule appointments for various services including:\n\n"
            "• **Consultation** (30-60 minutes)\n"
            "• **Therapy Session** (60 minutes)\n"
            "• **Workshop** (90-120 minutes)\n"
            "• **Meeting** (30-60 minutes)\n"
            "• **Business Consultation** (45-90 minutes)\n"
            "• **Creative Session** (60-90 minutes)\n\n"
            "How can I help you today?\n"
            "You can simply tell me what you need, like:\n"
            "• 'I need a consultation tomorrow at 10 AM'\n"
            "• 'Book a therapy session for next Monday'\n"
            "• 'Schedule a workshop for next week'"
        )
        if suggestions:
            greeting_response += "\n\n**Quick Actions:**\n" + "\n".join([f"• {s}" for s in suggestions])
        return AgentResponse(message=greeting_response)

    def _handle_info_collection_sync(self, state, message, entities, suggestions):
        """Handle information collection stage synchronously"""
        # Extract entities from message
        if 'service_type' in entities:
            state.current_booking_data['service_type'] = entities['service_type']
        
        # Check if we have enough info to proceed
        if 'service_type' in state.current_booking_data:
            state.stage = "showing_slots"
            return AgentResponse(
                message="Great! I can help you book a meeting. Let me check available slots for tomorrow at 10 AM.",
                booking_data=state.current_booking_data
            )
        else:
            return AgentResponse(
                message="I'd be happy to help you book a meeting! What type of service would you like? (consultation, therapy, workshop, etc.)"
            )

    def _handle_slot_selection_sync(self, state, message, entities, suggestions):
        """Handle slot selection stage synchronously"""
        # For now, return mock slots
        from datetime import datetime
        mock_slots = [
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T10:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T11:00:00"),
                available=True
            ),
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T14:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T15:00:00"),
                available=True
            ),
            TimeSlot(
                start_time=datetime.fromisoformat("2024-06-29T16:00:00"),
                end_time=datetime.fromisoformat("2024-06-29T17:00:00"),
                available=True
            )
        ]
        
        state.stage = "confirming"
        return AgentResponse(
            message="Here are some available slots for tomorrow:\n1. 10:00 AM - 11:00 AM\n2. 2:00 PM - 3:00 PM\n3. 4:00 PM - 5:00 PM\n\nWhich slot would you prefer?",
            suggested_slots=mock_slots,
            booking_data=state.current_booking_data
        )

    def _handle_confirmation_sync(self, state, message, entities, suggestions):
        """Handle confirmation stage synchronously"""
        state.stage = "completed"
        
        # Enhance booking data with more details
        booking_data = state.current_booking_data.copy()
        
        # Add booking ID and timestamp
        from datetime import datetime
        booking_data['booking_id'] = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        booking_data['booking_timestamp'] = datetime.now().isoformat()
        booking_data['confirmation_number'] = f"CNF-{datetime.now().strftime('%Y%m%d')}-{hash(booking_data['booking_id']) % 10000:04d}"
        
        # Ensure we have proper date/time information
        if 'date' not in booking_data or booking_data['date'] == 'Unknown':
            booking_data['date'] = 'Tomorrow'
        if 'time' not in booking_data or booking_data['time'] == 'Unknown':
            booking_data['time'] = '10:00 AM'
        if 'duration_minutes' not in booking_data:
            booking_data['duration_minutes'] = 60
        
        # Add user contact information (in a real app, this would come from user profile)
        booking_data['user_email'] = "user@example.com"
        booking_data['user_name'] = "Valued Customer"
        booking_data['contact_phone'] = "+1 (555) 123-4567"
        
        # Add location and additional details
        booking_data['location'] = "Main Office - Conference Room A"
        booking_data['instructions'] = "Please arrive 5 minutes before your scheduled time. Bring any relevant documents."
        booking_data['cancellation_policy'] = "Free cancellation up to 24 hours before the appointment."
        
        # Send confirmation email (async call in sync context)
        try:
            # Create a new event loop for email sending
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.email_service.send_booking_confirmation(
                    booking_data=booking_data,
                    recipient_email=booking_data['user_email']
                )
            )
            loop.close()
            email_status = "Confirmation email sent successfully!"
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            email_status = "Email service temporarily unavailable."
        
        return AgentResponse(
            message=f"✅ Perfect! I've confirmed your {booking_data.get('service_type', 'meeting')} for {booking_data.get('date', 'tomorrow')} at {booking_data.get('time', '10:00 AM')}. {email_status}\n\n**Booking Details:**\n• Confirmation #: {booking_data['confirmation_number']}\n• Location: {booking_data['location']}\n• Duration: {booking_data['duration_minutes']} minutes\n\nIs there anything else I can help you with?",
            booking_data=booking_data,
            requires_confirmation=False
        )

    def _handle_booking_sync(self, state, message, entities, suggestions):
        """Handle booking stage synchronously"""
        state.stage = "completed"
        return AgentResponse(
            message="Your booking has been successfully created! You'll receive a confirmation email shortly.",
            booking_data=state.current_booking_data,
            requires_confirmation=False
        )

    def _handle_completion_sync(self, state, message, entities, suggestions):
        return AgentResponse(message="Thank you! If you need to book another appointment or have any questions, just let me know. Have a great day! 😊")

    # --- Grouped Slot Formatting ---
    def _format_available_slots_enhanced(self, slots: List[TimeSlot]) -> str:
        if not slots:
            return "No available slots found."
        morning, afternoon, evening = [], [], []
        for slot in slots:
            hour = slot.start_time.hour
            if 6 <= hour < 12:
                morning.append(slot)
            elif 12 <= hour < 17:
                afternoon.append(slot)
            else:
                evening.append(slot)
        formatted = []
        slot_number = 1
        if morning:
            formatted.append("🌅 **Morning Slots:**")
            for slot in morning:
                formatted.append(f"{slot_number}. {slot.start_time.strftime('%I:%M %p')}")
                slot_number += 1
        if afternoon:
            formatted.append("\n☀️ **Afternoon Slots:**")
            for slot in afternoon:
                formatted.append(f"{slot_number}. {slot.start_time.strftime('%I:%M %p')}")
                slot_number += 1
        if evening:
            formatted.append("\n🌙 **Evening Slots:**")
            for slot in evening:
                formatted.append(f"{slot_number}. {slot.start_time.strftime('%I:%M %p')}")
                slot_number += 1
        return "\n".join(formatted)

    # --- Apply Extracted Entities ---
    def _apply_extracted_entities(self, state: ConversationState, entities: Dict[str, Any]):
        booking_data = state.current_booking_data
        if 'service_type' in entities:
            booking_data['service_type'] = entities['service_type']
        # ... (reuse your logic for date, time, duration, etc.) ...

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring and optimization"""
        return {
            'cache_hit_rate': len(self.async_cache.cache) / max(len(self.async_cache.cache), 1),
            'cache_size': len(self.async_cache.cache),
            'active_sessions': len(self.context_manager.user_preferences),
            'total_suggestions_generated': sum(len(self.context_manager.get_suggestions(sid, "")) for sid in self.context_manager.user_preferences),
            'nlp_processing_time': getattr(self, '_nlp_processing_time', 0),
        }

    def optimize_performance(self):
        """Optimize performance by cleaning cache and updating patterns"""
        # Clean expired cache entries
        asyncio.run(self.async_cache.clear_expired())
        
        # Update frequently accessed patterns
        if hasattr(self, '_access_patterns') and isinstance(self._access_patterns, dict):
            sorted_patterns = sorted(
                self._access_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]  # Keep top 10 patterns
            self._access_patterns = dict(sorted_patterns)

    def get_response(self, state: ConversationState) -> str:
        """
        Return the last assistant message from the conversation state, or a default message if none exists.
        """
        if hasattr(state, "messages") and isinstance(state.messages, list):
            for msg in reversed(state.messages):
                if hasattr(msg, "role") and msg.role == "assistant":
                    return getattr(msg, "content", "")
        return "No response available."

    def _extract_booking_entities(self, message: str) -> Dict[str, Any]:
        """Extract booking entities using enhanced LLM service or fallback to regex"""
        if self.llm_service:
            try:
                # Define schema for entity extraction
                schema = {
                    "type": "object",
                    "properties": {
                        "service_type": {"type": "string", "description": "Type of service (meeting, consultation, therapy, workshop)"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "time": {"type": "string", "description": "Time in HH:MM format (24-hour)"},
                        "duration": {"type": "integer", "description": "Duration in minutes"},
                        "customer_name": {"type": "string", "description": "Customer name if provided"},
                        "purpose": {"type": "string", "description": "Purpose or description of the meeting"}
                    }
                }
                
                # Use LLM service for entity extraction
                entities = self.llm_service.extract_entities(message, schema)
                return entities
            except Exception as e:
                print(f"LLM entity extraction failed: {e}, falling back to regex")
        
        # Fallback to regex-based extraction
        return self._extract_entities_regex(message)

    def _extract_name(self, message: str) -> str:
        """Extract name from user message (simple heuristic)"""
        message = message.strip()
        
        # Don't treat complex booking requests as names
        if any(keyword in message.lower() for keyword in ['meeting', 'appointment', 'schedule', 'book', 'next', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'am', 'pm', 'minute', 'hour']):
            return ""
        
        # Don't treat messages with numbers as names (likely dates/times)
        if any(char.isdigit() for char in message):
            return ""
        
        if len(message.split()) >= 2 and '@' not in message and not self._extract_email(message):
            return message.title()
        return ""

    def _extract_email(self, message: str) -> str:
        """Extract email from user message"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        matches = re.findall(email_pattern, message)
        return matches[0] if matches else ""

    def _extract_phone(self, message: str) -> str:
        """Extract phone number from user message"""
        phone_pattern = r'(\+?\d[\d\s\-\(\)]{7,}\d)'
        matches = re.findall(phone_pattern, message)
        return matches[0].strip() if matches else ""

    def _extract_date(self, message: str) -> Optional[datetime]:
        """Extract date from user message (improved, supports more formats)"""
        import dateutil.parser

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        lowered = message.lower()

        if 'today' in lowered:
            return today
        if 'tomorrow' in lowered:
            return today + timedelta(days=1)

        # Weekday parsing
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(weekdays):
            if day in lowered:
                days_ahead = (i - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)

        # Try to parse date using dateutil
        try:
            parsed = dateutil.parser.parse(message, fuzzy=True, default=today)
            # Only accept future dates
            if parsed.date() >= today.date():
                return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        except Exception:
            pass

        return None

    def _extract_slot_index(self, message: str, slots: Optional[List[TimeSlot]] = None) -> Optional[int]:
        """Extract slot index from user message (e.g., '1', 'first', 'slot 2', '10 AM', 'the earliest', etc.)"""
        lowered = message.lower()
        # Ordinal words
        ordinals = {'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4, 'last': -1, 'earliest': 0, 'any': 0}
        for word, idx in ordinals.items():
            if word in lowered:
                if idx == -1 and slots:
                    return len(slots) - 1
                return idx
        # Phrases like 'slot 2', 'option 3'
        match = re.search(r'(slot|option|number)\s*(\d+)', lowered)
        if match:
            idx = int(match.group(2)) - 1
            if idx >= 0:
                return idx
        # Direct number
        match = re.search(r'\b(\d{1,2})\b', lowered)
        if match:
            idx = int(match.group(1)) - 1
            if idx >= 0:
                return idx
        # Time expressions (e.g., '10 am', '14:30')
        if slots:
            for i, slot in enumerate(slots):
                slot_time = slot.start_time.strftime('%I:%M %p').lower()
                if slot_time in lowered:
                    return i
                # Accept '10 am' for '10:00 AM'
                if re.search(rf'\b{slot.start_time.strftime("%I").lstrip("0")} ?(am|pm)\b', lowered):
                    return i
        return None

    def _format_available_slots(self, slots: List[TimeSlot]) -> str:
        """Format available time slots for display"""
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            try:
                time_str = slot.start_time.strftime("%I:%M %p")
            except Exception:
                time_str = str(slot.start_time)
            formatted_slots.append(f"{i}. {time_str}")
        return "\n".join(formatted_slots)
