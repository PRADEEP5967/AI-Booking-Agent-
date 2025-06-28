#!/usr/bin/env python3
"""
Test script to verify frontend-backend connection.
"""

import requests
import json

def test_backend_connection():
    """Test if the frontend can connect to the backend"""
    print("🧪 Testing Frontend-Backend Connection...")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Session creation
    print("\n2. Testing session creation...")
    try:
        response = requests.post(f"{base_url}/conversation/start", timeout=10)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get("session_id")
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Session creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Test 3: Message sending
    print("\n3. Testing message sending...")
    try:
        message_data = {"message": "Hello"}
        response = requests.post(
            f"{base_url}/conversation/{session_id}/message",
            json=message_data,
            timeout=10
        )
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Message sent successfully")
            print(f"   Response: {response_data.get('response', '')[:100]}...")
        else:
            print(f"❌ Message sending failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Message sending error: {e}")
        return False
    
    # Test 4: Session retrieval
    print("\n4. Testing session retrieval...")
    try:
        response = requests.get(f"{base_url}/conversation/{session_id}", timeout=10)
        if response.status_code == 200:
            session_info = response.json()
            messages = session_info.get("messages", [])
            print(f"✅ Session retrieved: {len(messages)} messages")
        else:
            print(f"❌ Session retrieval failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Session retrieval error: {e}")
        return False
    
    # Test 5: Admin sessions
    print("\n5. Testing admin sessions...")
    try:
        response = requests.get(f"{base_url}/admin/sessions", timeout=10)
        if response.status_code == 200:
            admin_data = response.json()
            total_sessions = admin_data.get("total_sessions", 0)
            print(f"✅ Admin sessions: {total_sessions} total sessions")
        else:
            print(f"❌ Admin sessions failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin sessions error: {e}")
        return False
    
    print("\n🎉 All tests passed! Frontend should be able to connect to backend.")
    return True

def main():
    """Main test runner"""
    print("🤖 Frontend-Backend Connection Test")
    print("=" * 50)
    
    success = test_backend_connection()
    
    if success:
        print("\n✨ The backend is ready for frontend connections!")
        print("\nNext steps:")
        print("  1. Start the frontend: streamlit run frontend/streamlit_app.py")
        print("  2. Open http://localhost:8501 in your browser")
        print("  3. Try sending a message - it should work now!")
    else:
        print("\n❌ Some tests failed. Check the backend logs for errors.")
    
    return success

if __name__ == "__main__":
    main() 