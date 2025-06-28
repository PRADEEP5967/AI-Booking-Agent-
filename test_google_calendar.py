#!/usr/bin/env python3
"""
Test script to verify Google Calendar integration and mock mode functionality.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

def test_calendar_service():
    """Test the calendar service in both mock and real modes"""
    print("🧪 Testing Google Calendar Integration...")
    
    try:
        from services.calendar_service import CalendarService
        from config.settings import settings
        
        print(f"📋 Current settings:")
        print(f"  - USE_MOCK_CALENDAR: {settings.USE_MOCK_CALENDAR}")
        print(f"  - GOOGLE_CALENDAR_CREDENTIALS_FILE: {settings.GOOGLE_CALENDAR_CREDENTIALS_FILE}")
        
        # Test calendar service initialization
        print("\n🔧 Initializing Calendar Service...")
        calendar_service = CalendarService()
        
        if calendar_service.mock_service:
            print("✅ Mock Calendar Service initialized successfully")
        else:
            print("✅ Real Google Calendar Service initialized successfully")
        
        # Test getting free slots
        print("\n📅 Testing free slots retrieval...")
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        free_slots = calendar_service.get_free_slots(
            start_date.isoformat().replace("+00:00", "Z"),
            end_date.isoformat().replace("+00:00", "Z"),
            60
        )
        
        print(f"✅ Found {len(free_slots)} free slots")
        if free_slots:
            print(f"   First slot: {free_slots[0]}")
        
        # Test creating an event
        print("\n📝 Testing event creation...")
        event_title = "Test Meeting"
        event_start = (start_date + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        event_end = (start_date + timedelta(hours=3)).isoformat().replace("+00:00", "Z")
        
        created_event = calendar_service.create_event(
            event_title,
            event_start,
            event_end,
            "Test event description"
        )
        
        print(f"✅ Event created successfully")
        print(f"   Event ID: {created_event.get('id', 'mock_event')}")
        print(f"   Title: {created_event.get('summary', event_title)}")
        
        # Test booking a slot
        print("\n🎯 Testing slot booking...")
        booking_result = calendar_service.book_slot(
            start_date + timedelta(hours=4),
            start_date + timedelta(hours=5),
            "Booked Test Meeting",
            "This is a test booking"
        )
        
        print(f"✅ Booking result: {booking_result.get('status', 'unknown')}")
        print(f"   Message: {booking_result.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing calendar service: {e}")
        return False

def test_credentials():
    """Test Google Calendar credentials"""
    print("\n🔐 Testing Google Calendar Credentials...")
    
    credentials_file = "credentials/google_credentials.json"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    try:
        import json
        with open(credentials_file, 'r') as f:
            credentials = json.load(f)
        
        print(f"✅ Credentials file found and valid JSON")
        
        # Check if it's the right type of credentials
        if "installed" in credentials:
            print("✅ OAuth 2.0 client credentials (installed app)")
            client_id = credentials["installed"]["client_id"]
            print(f"   Client ID: {client_id[:20]}...")
            return True
        elif "web" in credentials:
            print("✅ OAuth 2.0 client credentials (web app)")
            client_id = credentials["web"]["client_id"]
            print(f"   Client ID: {client_id[:20]}...")
            return True
        elif "type" in credentials and credentials["type"] == "service_account":
            print("❌ Service account credentials (not supported for OAuth flow)")
            print("   Please use OAuth 2.0 client credentials instead")
            return False
        else:
            print("❌ Unknown credentials format")
            return False
            
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🌍 Testing Environment Configuration...")
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file found: {env_file}")
        
        # Read and display key settings
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            lines = env_content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if 'MOCK' in key or 'CALENDAR' in key or 'GOOGLE' in key:
                        print(f"   {key}: {value}")
        except Exception as e:
            print(f"   Warning: Could not read .env file: {e}")
    else:
        print(f"⚠️  .env file not found: {env_file}")
        print("   Using default environment variables")
    
    # Check environment variables
    mock_calendar = os.getenv("USE_MOCK_CALENDAR", "true")
    print(f"   USE_MOCK_CALENDAR: {mock_calendar}")
    
    return True

def main():
    """Main test runner"""
    print("🤖 Google Calendar Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", test_environment),
        ("Google Calendar Credentials", test_credentials),
        ("Calendar Service", test_calendar_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Google Calendar integration is working correctly.")
        print("\nNext steps:")
        print("  • If using mock mode: You can test booking flows without real Google Calendar")
        print("  • If using real mode: Your Google Calendar integration is ready")
        print("  • To switch modes: Set USE_MOCK_CALENDAR=true/false in your .env file")
    else:
        print("\n⚠️ Some tests failed. Here are the issues and solutions:")
        print("\nCommon issues:")
        print("  • Missing .env file: Copy env_template.txt to .env")
        print("  • Wrong credentials type: Use OAuth 2.0 client credentials, not service account")
        print("  • Missing Google Calendar API: Enable it in Google Cloud Console")
        print("  • Network issues: Check your internet connection")
        
        if not results[1][1]:  # Credentials test failed
            print("\n🔧 To fix credentials:")
            print("  1. Go to Google Cloud Console")
            print("  2. Create OAuth 2.0 client credentials")
            print("  3. Download as JSON")
            print("  4. Place in credentials/google_credentials.json")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 