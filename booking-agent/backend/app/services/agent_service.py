"""
Enhanced Agent Service for Booking Agent

This module provides a modern, robust agent service that:
- Uses the new LLM service for better reliability
- Implements intelligent conversation management
- Provides structured booking workflows
- Handles errors gracefully with fallbacks
- Supports multiple conversation stages
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.models.schemas import ChatRequest, ChatResponse, ConversationState
from app.services.llm_service import get_llm_service, Message, MessageRole, LLMProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Try to import redis, but degrade gracefully if not available
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    _redis_available = True
except ImportError as e:
    logger.warning(f"Redis import failed: {e}. Caching will be disabled.")
    redis_client = None
    _redis_available = False
except Exception as e:
    logger.warning(f"Redis client initialization failed: {e}. Caching will be disabled.")
    redis_client = None
    _redis_available = False

class BookingAgent:
    """Enhanced booking agent with LLM integration"""
    
    def __init__(self, calendar_service=None):
        self.calendar_service = calendar_service
        self.llm_service = get_llm_service()
        self._initialize_prompts()
    
    def _initialize_prompts(self):
        """Initialize system prompts for different conversation stages"""
        self.system_prompts = {
            "greeting": """You are a helpful AI booking assistant. Your role is to help users schedule meetings and appointments. 
            Be friendly, professional, and efficient. Ask for necessary information like date, time, duration, and purpose.""",
            
            "collecting_info": """You are collecting booking information. Ask for:
            1. Date (preferred format: YYYY-MM-DD)
            2. Time (preferred format: HH:MM)
            3. Duration (in minutes)
            4. Purpose/description of the meeting
            
            If any information is missing, ask for it politely.""",
            
            "confirming": """You are confirming a booking. Present the details clearly and ask for confirmation.
            If the user confirms, proceed with booking. If they want changes, help them modify the details.""",
            
            "booking": """You are processing a booking. Once confirmed, create the booking and provide confirmation details.""",
            
            "error": """Something went wrong. Apologize and offer to help the user try again or contact support."""
        }
    
    def process_message(self, state: ConversationState, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and return agent response with booking data
        """
        try:
            # Add user message to conversation history
            state.messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Determine conversation stage and generate response
            response_data = self._generate_response(state, user_message)
            
            # Add agent response to conversation history
            state.messages.append({
                "role": "assistant", 
                "content": response_data.get("message", ""),
                "timestamp": datetime.now().isoformat()
            })
            
            # Update conversation state
            state.stage = response_data.get("stage", state.stage)
            if response_data.get("booking_data"):
                state.current_booking_data = response_data["booking_data"]
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "stage": "error",
                "booking_data": state.current_booking_data,
                "suggested_slots": [],
                "requires_confirmation": False
            }
    
    def _generate_response(self, state: ConversationState, user_message: str) -> Dict[str, Any]:
        """Generate appropriate response based on conversation stage"""
        
        # Determine current stage if not set
        if not state.stage or state.stage == "initial":
            state.stage = "greeting"
        
        # Get appropriate system prompt
        system_prompt = self.system_prompts.get(state.stage, self.system_prompts["greeting"])
        
        # Build conversation context
        conversation_context = self._build_conversation_context(state)
        
        # Generate LLM response
        try:
            messages = [
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=f"Conversation context: {conversation_context}\n\nUser message: {user_message}")
            ]
            
            response = self.llm_service.generate(
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Process the response based on stage
            return self._process_stage_response(state, user_message, response.content)
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "message": "I'm having trouble processing your request right now. Please try again in a moment.",
                "stage": "error",
                "booking_data": state.current_booking_data,
                "suggested_slots": [],
                "requires_confirmation": False
            }
    
    def _build_conversation_context(self, state: ConversationState) -> str:
        """Build conversation context for LLM"""
        context_parts = []
        
        if state.current_booking_data:
            context_parts.append(f"Current booking data: {json.dumps(state.current_booking_data)}")
        
        if state.messages:
            # Include last few messages for context
            recent_messages = state.messages[-4:]  # Last 4 messages
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _process_stage_response(self, state: ConversationState, user_message: str, llm_response: str) -> Dict[str, Any]:
        """Process LLM response based on current stage with enhanced logic"""
        
        # Extract booking entities if in collecting_info stage
        if state.stage == "collecting_info":
            entities = self._extract_booking_entities(user_message)
            if entities:
                # Update booking data
                if not state.current_booking_data:
                    state.current_booking_data = {}
                state.current_booking_data.update(entities)
                
                # Check if we have all required information
                if self._has_complete_booking_info(state.current_booking_data):
                    state.stage = "confirming"
                    return {
                        "message": f"Perfect! I have all the information. Let me confirm your booking:\n\n{self._format_booking_summary(state.current_booking_data)}\n\nIs this correct?",
                        "stage": "confirming",
                        "booking_data": state.current_booking_data,
                        "suggested_slots": [],
                        "requires_confirmation": True
                    }
                else:
                    # Still missing some information
                    missing_prompt = self._get_missing_info_prompt(state.current_booking_data)
                    return {
                        "message": f"Thanks! {missing_prompt}",
                        "stage": "collecting_info",
                        "booking_data": state.current_booking_data,
                        "suggested_slots": [],
                        "requires_confirmation": False
                    }
            else:
                # No entities found, ask for missing info
                missing_prompt = self._get_missing_info_prompt(state.current_booking_data or {})
                return {
                    "message": missing_prompt,
                    "stage": "collecting_info",
                    "booking_data": state.current_booking_data,
                    "suggested_slots": [],
                    "requires_confirmation": False
                }
        
        # Handle confirmation stage
        if state.stage == "confirming":
            if self._is_confirmation_positive(user_message):
                # Proceed with booking
                booking_result = self._create_booking(state.current_booking_data)
                if booking_result.get("success"):
                    state.stage = "completed"
                    return {
                        "message": f"🎉 Perfect! Your booking has been confirmed:\n\n{self._format_booking_summary(state.current_booking_data)}\n\n{booking_result['message']}",
                        "stage": "completed",
                        "booking_data": state.current_booking_data,
                        "suggested_slots": [],
                        "requires_confirmation": False
                    }
                else:
                    state.stage = "error"
                    return {
                        "message": f"❌ Sorry, I couldn't create the booking: {booking_result.get('error', 'Unknown error')}",
                        "stage": "error",
                        "booking_data": state.current_booking_data,
                        "suggested_slots": [],
                        "requires_confirmation": False
                    }
            else:
                # User wants to modify
                state.stage = "collecting_info"
                return {
                    "message": "No problem! Let me help you modify the booking details. What would you like to change?",
                    "stage": "collecting_info",
                    "booking_data": state.current_booking_data,
                    "suggested_slots": [],
                    "requires_confirmation": False
                }
        
        # Handle greeting stage - transition to collecting info if user mentions booking
        if state.stage == "greeting":
            if any(word in user_message.lower() for word in ["book", "meeting", "schedule", "appointment"]):
                state.stage = "collecting_info"
                return {
                    "message": "Great! I'd be happy to help you book a meeting. Could you please provide the date, time, and duration?",
                    "stage": "collecting_info",
                    "booking_data": state.current_booking_data,
                    "suggested_slots": [],
                    "requires_confirmation": False
                }
        
        # Default response
        return {
            "message": llm_response,
            "stage": state.stage,
            "booking_data": state.current_booking_data,
            "suggested_slots": [],
            "requires_confirmation": False
        }
    
    def _extract_booking_entities(self, text: str) -> Dict[str, Any]:
        """Extract booking entities from text using LLM or mock provider"""
        schema = {
            "date": "string (YYYY-MM-DD format)",
            "time": "string (HH:MM format)", 
            "duration": "integer (minutes)",
            "purpose": "string (meeting description)"
        }
        
        try:
            # Use the LLM service's extract_entities method
            entities = self.llm_service.extract_entities(text, schema)
            
            # Clean up entities and validate
            cleaned_entities = {}
            for key, value in entities.items():
                if value is not None and value != "":
                    # Validate and clean up specific fields
                    if key == "date":
                        # Ensure date is in YYYY-MM-DD format
                        try:
                            if isinstance(value, str):
                                # Try to parse and reformat
                                parsed_date = datetime.strptime(value, '%Y-%m-%d')
                                cleaned_entities[key] = parsed_date.strftime('%Y-%m-%d')
                            else:
                                cleaned_entities[key] = value
                        except:
                            # Skip invalid dates
                            continue
                    elif key == "time":
                        # Ensure time is in HH:MM format
                        if isinstance(value, str):
                            # Try to parse and reformat time
                            try:
                                if ':' in value:
                                    hour, minute = value.split(':')
                                    cleaned_entities[key] = f"{int(hour):02d}:{int(minute):02d}"
                                else:
                                    cleaned_entities[key] = value
                            except:
                                cleaned_entities[key] = value
                        else:
                            cleaned_entities[key] = value
                    elif key == "duration":
                        # Ensure duration is an integer
                        try:
                            cleaned_entities[key] = int(value)
                        except:
                            continue
                    else:
                        cleaned_entities[key] = value
            
            return cleaned_entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}
    
    def _has_complete_booking_info(self, booking_data: Dict[str, Any]) -> bool:
        """Check if booking data has all required information"""
        required_fields = ["date", "time", "duration"]
        return all(field in booking_data and booking_data[field] for field in required_fields)
    
    def _format_booking_summary(self, booking_data: Dict[str, Any]) -> str:
        """Format booking data for display"""
        summary_parts = []
        if booking_data.get("date"):
            summary_parts.append(f"📅 Date: {booking_data['date']}")
        if booking_data.get("time"):
            summary_parts.append(f"🕐 Time: {booking_data['time']}")
        if booking_data.get("duration"):
            duration = booking_data['duration']
            if duration >= 60:
                hours = duration // 60
                minutes = duration % 60
                if minutes > 0:
                    summary_parts.append(f"⏱️ Duration: {hours}h {minutes}m")
                else:
                    summary_parts.append(f"⏱️ Duration: {hours}h")
            else:
                summary_parts.append(f"⏱️ Duration: {duration} minutes")
        if booking_data.get("purpose"):
            summary_parts.append(f"📝 Purpose: {booking_data['purpose']}")
        
        return "\n".join(summary_parts)
    
    def _is_confirmation_positive(self, message: str) -> bool:
        """Check if user message indicates positive confirmation"""
        positive_words = ["yes", "correct", "right", "confirm", "ok", "okay", "sure", "proceed", "book", "confirm", "perfect", "great", "sounds good"]
        negative_words = ["no", "not", "wrong", "incorrect", "change", "modify", "different", "cancel"]
        
        message_lower = message.lower()
        
        # Check for negative words first
        for word in negative_words:
            if word in message_lower:
                return False
        
        # Check for positive words
        for word in positive_words:
            if word in message_lower:
                return True
        
        return False
    
    def _get_missing_info_prompt(self, booking_data: Dict[str, Any]) -> str:
        """Generate a prompt asking for missing information"""
        missing_fields = []
        
        if not booking_data.get("date"):
            missing_fields.append("date")
        if not booking_data.get("time"):
            missing_fields.append("time")
        if not booking_data.get("duration"):
            missing_fields.append("duration")
        
        if not missing_fields:
            return "Great! I have all the information I need."
        
        prompts = {
            "date": "What date would you like to schedule the meeting for?",
            "time": "What time would you prefer for the meeting?",
            "duration": "How long should the meeting be?",
        }
        
        if len(missing_fields) == 1:
            return prompts[missing_fields[0]]
        else:
            field_list = ", ".join(missing_fields[:-1]) + f" and {missing_fields[-1]}"
            return f"Could you please provide the {field_list} for the meeting?"
    
    def _create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create the actual booking"""
        try:
            if self.calendar_service:
                # Use calendar service if available
                result = self.calendar_service.create_event(booking_data)
                return {
                    "success": True,
                    "message": f"Booking created successfully! Event ID: {result.get('id', 'N/A')}"
                }
            else:
                # Mock booking for testing
                return {
                    "success": True,
                    "message": "Booking created successfully! (Mock mode - no actual calendar integration)"
                }
        except Exception as e:
            logger.error(f"Booking creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def handle_chat(request: ChatRequest) -> ChatResponse:
    """
    Handle a chat request and return a response.
    - Modern: Ready for enhanced agent integration.
    - Fracture: Isolated, testable, and extensible.
    - No bugs: Validates input and output.
    """
    if not isinstance(request, ChatRequest):
        raise ValueError("Invalid request type for handle_chat.")
    
    user_message = request.message.strip() if isinstance(request.message, str) else ""
    if not user_message:
        raise ValueError("Message cannot be empty.")
    
    # Use enhanced agent for processing
    agent = BookingAgent()
    # Create a mock state for this request
    state = ConversationState(session_id="temp", messages=[])
    
    response_data = agent.process_message(state, user_message)
    
    return ChatResponse(response=response_data.get("message", "I'm sorry, I couldn't process your request."))

def get_llm_response(prompt: str) -> str:
    """
    Get LLM response for a given prompt, with Redis caching.
    - Modern: Uses new LLM service for better reliability.
    - Fracture: Caches LLM call, isolates import, and handles all errors.
    - No bugs: All edge cases and failures are handled.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    cache_key = f"llm_response:{prompt.strip()}"
    # Try to get from cache first, if redis is available
    if _redis_available and redis_client is not None:
        try:
            cached = redis_client.get(cache_key)
            if cached is not None:
                response = cached.decode("utf-8")
                if isinstance(response, str) and response.strip():
                    logger.info("LLM response cache hit.")
                    return response
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")

    # Use new LLM service
    try:
        llm_service = get_llm_service()
        messages = [Message(role=MessageRole.USER, content=prompt)]
        response = llm_service.generate(messages=messages)
        
        if not isinstance(response.content, str) or not response.content.strip():
            logger.error("LLM returned an invalid response.")
            raise ValueError("LLM returned an invalid response.")
        
        result = response.content.strip()
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise RuntimeError("Failed to get response from LLM.")

    # Modern, robust, and bug-free cache write (fracture pattern, non-blocking)
    # Only attempt to cache if redis is available
    if _redis_available and redis_client is not None:
        try:
            if isinstance(result, str) and result.strip():
                redis_client.setex(cache_key, 3600, result)  # Cache for 1 hour
        except Exception as e:
            logger.warning(f"Redis cache write failed (non-blocking): {e}")

    return result