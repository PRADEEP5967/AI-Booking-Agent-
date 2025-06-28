#!/usr/bin/env python3
"""
Simple test script to verify basic setup
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test basic imports"""
    print("Testing imports...")
    
    try:
        from app.models.schemas import BookingRequest, ConversationState
        print("✅ Schemas imported successfully")
    except ImportError as e:
        print(f"❌ Schema import failed: {e}")
        return False
    
    try:
        from app.services.conversation_service import ConversationService
        print("✅ ConversationService imported successfully")
    except ImportError as e:
        print(f"❌ ConversationService import failed: {e}")
        return False
    
    try:
        from app.services.calendar_service import CalendarService
        print("✅ CalendarService imported successfully")
    except ImportError as e:
        print(f"❌ CalendarService import failed: {e}")
        return False
    
    return True

def test_schema_creation():
    """Test schema creation"""
    print("\nTesting schema creation...")
    
    try:
        from app.models.schemas import BookingRequest, ConversationState
        
        # Test BookingRequest
        booking_req = BookingRequest(
            user_name="Test User",
            email="test@example.com",
            preferred_date="2024-01-01",
            preferred_time="10:00",
            duration=60
        )
        print(f"✅ BookingRequest created: {booking_req.user_name}")
        
        # Test ConversationState
        state = ConversationState(session_id="test-session")
        print(f"✅ ConversationState created: {state.session_id}")
        
        return True
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False

def test_service_initialization():
    """Test service initialization"""
    print("\nTesting service initialization...")
    
    try:
        from app.services.conversation_service import ConversationService
        from app.services.calendar_service import CalendarService
        
        # Test ConversationService
        conv_service = ConversationService()
        print("✅ ConversationService initialized")
        
        # Test CalendarService
        cal_service = CalendarService()
        print("✅ CalendarService initialized")
        
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running setup tests...\n")
    
    tests = [
        test_imports,
        test_schema_creation,
        test_service_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 