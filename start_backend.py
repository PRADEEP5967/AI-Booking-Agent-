#!/usr/bin/env python3
"""
Simple script to start the booking agent backend server
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    """Start the FastAPI server"""
    try:
        import uvicorn
        
        print("🚀 Starting Booking Agent Backend Server...")
        print("📍 API will be available at: http://localhost:8000")
        print("📚 API Documentation at: http://localhost:8000/docs")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies: pip install fastapi uvicorn")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 