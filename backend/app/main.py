import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Load environment variables and setup logging
from dotenv import load_dotenv
load_dotenv()

from .config.settings import settings
from .models.schemas import (
    BookingRequest,
    Booking,
    ConversationState,
    ConversationMessage,
    AgentResponse
)
from .services.calendar_service import CalendarService
from .services.conversation_service import ConversationService
from .services.agent_service import BookingAgent

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Booking Agent API",
    description="AI-powered booking system with conversational interface",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    calendar_service = CalendarService()
    booking_agent = BookingAgent(calendar_service)
    conversation_service = ConversationService()
    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    calendar_service = None
    booking_agent = None
    conversation_service = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Booking Agent API is running!", "status": "healthy"}

@app.post("/conversation/start")
async def start_conversation():
    """Start a new conversation session"""
    try:
        if conversation_service is None:
            raise HTTPException(status_code=500, detail="Conversation service unavailable")
            
        session_id = str(uuid.uuid4())
        state = ConversationState(session_id=session_id)
        success = conversation_service.store_conversation(session_id, state)
        
        if success:
            logger.info(f"Started new conversation session: {session_id}")
            return {"session_id": session_id, "message": "Conversation started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start conversation")
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/conversation/{session_id}/message")
async def send_message(session_id: str, message_data: Dict[str, str]):
    """Send a message in an existing conversation"""
    try:
        if conversation_service is None or booking_agent is None:
            raise HTTPException(status_code=500, detail="Required services unavailable")
            
        user_message = message_data.get("message", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get conversation state
        state = conversation_service.get_conversation(session_id)
        if not state:
            # Auto-recover: create new session if not found
            logger.warning(f"Session {session_id} not found, creating new session")
            state = ConversationState(session_id=session_id)
            conversation_service.store_conversation(session_id, state)
        
        # Process message with booking agent
        response = booking_agent.process_message(state, user_message)
        
        # Update conversation state
        conversation_service.store_conversation(session_id, state)
        
        logger.info(f"Processed message for session {session_id}")
        
        return {
            "response": response.message,
            "booking_data": response.booking_data,
            "suggested_slots": response.suggested_slots,
            "stage": state.stage,
            "requires_confirmation": response.requires_confirmation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history"""
    try:
        if conversation_service is None:
            raise HTTPException(status_code=500, detail="Conversation service unavailable")
            
        state = conversation_service.get_conversation(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "session_id": session_id,
            "messages": state.messages,
            "stage": state.stage,
            "booking_data": state.current_booking_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/bookings")
async def create_booking(booking_request: BookingRequest):
    """Create a new booking directly (non-conversational)"""
    try:
        if calendar_service is None:
            raise HTTPException(status_code=500, detail="Calendar service unavailable")
            
        # Create booking object
        booking = Booking(
            id=str(uuid.uuid4()),
            customer_name=booking_request.user_name,
            customer_email=booking_request.email,
            customer_phone=None,  # Not in BookingRequest
            service_type=booking_request.meeting_type or "consultation",
            scheduled_datetime=datetime.now(),  # This should be parsed from request
            duration_minutes=booking_request.duration,
            notes=None
        )
        
        # Create calendar event
        success = calendar_service.book_slot(
            booking.scheduled_datetime,
            booking.scheduled_datetime + timedelta(minutes=booking.duration_minutes),
            f"{booking.service_type} - {booking.customer_name}",
            f"Customer: {booking.customer_name}\nEmail: {booking.customer_email}",
            [booking.customer_email] if booking.customer_email else None
        )
        
        if success.get("status") in ("booked", "mock_booked"):
            logger.info(f"Created booking: {booking.id}")
            return {"booking_id": booking.id, "status": "confirmed"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create booking")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/available-slots")
async def get_available_slots(date: str, duration: int = 60):
    """Get available time slots for a specific date"""
    try:
        if calendar_service is None:
            raise HTTPException(status_code=500, detail="Calendar service unavailable")
            
        target_date = datetime.fromisoformat(date)
        slots = calendar_service.get_available_slots(target_date, duration)
        
        logger.info(f"Retrieved {len(slots)} available slots for {date}")
        return {"date": date, "available_slots": slots}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Error getting available slots for {date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health", tags=["Monitoring"])
async def health_check():
    return JSONResponse({"status": "ok"})

@app.get("/ready", tags=["Monitoring"])
async def readiness_check():
    # Optionally check DB, external APIs, etc.
    try:
        # e.g., ping Google Calendar, DB, etc.
        return JSONResponse({"status": "ready"})
    except Exception as e:
        return JSONResponse({"status": "not ready", "error": str(e)}, status_code=503)

@app.get("/admin/status")
async def admin_status():
    """Admin endpoint to check system status"""
    try:
        status = {
            "backend": "running",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(conversation_service._conversations) if conversation_service else 0,
            "calendar_service": "mock" if not calendar_service or not calendar_service.service else "connected",
            "booking_agent": "available" if booking_agent else "unavailable"
        }
        return status
    except Exception as e:
        logger.error(f"Error getting admin status: {e}")
        return {"error": str(e)}

@app.post("/admin/cleanup")
async def cleanup_sessions():
    """Admin endpoint to cleanup old sessions"""
    try:
        if conversation_service:
            conversation_service.cleanup_old_sessions()
            return {"message": "Session cleanup completed"}
        return {"error": "Conversation service not available"}
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")
        return {"error": str(e)}

@app.get("/admin/sessions")
async def list_sessions():
    """Admin endpoint to list active sessions"""
    try:
        if conversation_service:
            sessions = conversation_service.list_conversations()
            return {
                "total_sessions": len(sessions),
                "sessions": list(sessions.keys())
            }
        return {"error": "Conversation service not available"}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)