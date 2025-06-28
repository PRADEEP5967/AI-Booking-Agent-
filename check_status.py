#!/usr/bin/env python3
"""
Quick status check for the Booking Agent project
"""
import requests
import time

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on http://localhost:8001/")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on http://localhost:8001/")
        return False
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def check_frontend():
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:8502/", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running on http://localhost:8502/")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running on http://localhost:8502/")
        return False
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def main():
    """Check both services"""
    print("🔍 Checking Booking Agent Services...")
    print("-" * 50)
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print("-" * 50)
    if backend_ok and frontend_ok:
        print("🎉 All services are running!")
        print("\n📱 Access your application:")
        print("   Backend API: http://localhost:8001/")
        print("   API Docs:    http://localhost:8001/docs")
        print("   Frontend:    http://localhost:8502/")
        print("\n🚀 Your AI Booking Agent is ready to use!")
    else:
        print("⚠️  Some services are not running.")
        print("\nTo start the services:")
        print("1. Backend: python start_backend.py")
        print("2. Frontend: streamlit run frontend/streamlit_app.py --server.port 8502")

if __name__ == "__main__":
    main() 