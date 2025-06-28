#!/usr/bin/env python3
"""
Simple script to start the booking agent frontend
"""
import sys
import os
import subprocess

def main():
    """Start the Streamlit frontend"""
    try:
        print("🎨 Starting Booking Agent Frontend...")
        print("📍 Frontend will be available at: http://localhost:8501")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "frontend/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install: pip install streamlit")
        return 1
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 