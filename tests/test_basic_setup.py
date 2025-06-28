import unittest
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class TestBasicSetup(unittest.TestCase):
    """Test basic setup and imports"""
    
    def test_imports(self):
        """Test that all main modules can be imported"""
        try:
            from app.models.schemas import BookingRequest, Booking, ConversationState
            from app.services.calendar_service import CalendarService
            from app.services.conversation_service import ConversationService
            from app.services.agent_service import BookingAgent
            self.assertTrue(True, "All imports successful")
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_schema_creation(self):
        """Test that Pydantic models can be created"""
        try:
            from app.models.schemas import BookingRequest, ConversationState
            
            # Test BookingRequest creation
            booking_req = BookingRequest(
                user_name="Test User",
                email="test@example.com",
                preferred_date="2024-01-01",
                duration=60
            )
            self.assertEqual(booking_req.user_name, "Test User")
            
            # Test ConversationState creation
            state = ConversationState(session_id="test-session")
            self.assertEqual(state.session_id, "test-session")
            self.assertEqual(state.stage, "greeting")
            
        except Exception as e:
            self.fail(f"Schema creation failed: {e}")

if __name__ == '__main__':
    unittest.main() 