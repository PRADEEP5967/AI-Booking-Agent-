#!/usr/bin/env python3
"""
Test script to verify all backend imports work correctly.
"""

def test_imports():
    try:
        # Test main imports
        from app.main import app
        print("✓ Main app imports successfully")
        
        # Test service imports
        from app.services.agent_service import BookingAgent
        print("✓ BookingAgent imports successfully")
        
        from app.services.calendar_service import CalendarService
        print("✓ CalendarService imports successfully")
        
        from app.services.conversation_service import ConversationService
        print("✓ ConversationService imports successfully")
        
        # Test model imports
        from app.models.schemas import (
            BookingRequest, Booking, ConversationState, 
            ConversationMessage, AgentResponse, TimeSlot
        )
        print("✓ All schema models import successfully")
        
        # Test agent imports
        from app.agents.booking_agent import BookingAgent as BookingAgentClass
        print("✓ BookingAgent class imports successfully")
        
        from app.agents.tools import parse_time, parse_date, detect_intent
        print("✓ Agent tools import successfully")
        
        print("\n✓ All imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports() 