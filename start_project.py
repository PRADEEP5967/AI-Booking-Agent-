#!/usr/bin/env python3
"""
Comprehensive startup script for AI Booking Agent
Handles both backend and frontend startup with proper error handling
"""

import os
import sys
import time
import subprocess
import requests
import signal
import threading
from pathlib import Path

def check_port(port: int) -> bool:
    """Check if a port is available"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port: int) -> int:
    """Find an available port starting from start_port"""
    port = start_port
    while not check_port(port):
        port += 1
    return port

def start_backend():
    """Start the backend server"""
    print("🚀 Starting Backend Server...")
    
    # Check if backend port is available
    backend_port = 8000
    if not check_port(backend_port):
        print(f"⚠️  Port {backend_port} is in use, checking if backend is already running...")
        try:
            response = requests.get(f"http://localhost:{backend_port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend is already running on port {backend_port}")
                return backend_port
        except:
            pass
        print(f"❌ Port {backend_port} is occupied and backend is not responding")
        return None
    
    # Start backend
    try:
        backend_process = subprocess.Popen([
            sys.executable, "start_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for backend to start
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            try:
                response = requests.get(f"http://localhost:{backend_port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Backend started successfully on port {backend_port}")
                    return backend_port
            except:
                pass
        
        print("❌ Backend failed to start within 30 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend(backend_port: int):
    """Start the frontend server"""
    print("🎨 Starting Frontend Server...")
    
    # Find available frontend port
    frontend_port = find_available_port(8501)
    print(f"📍 Frontend will use port {frontend_port}")
    
    # Set environment variable for frontend
    env = os.environ.copy()
    env['BOOKING_AGENT_API_URL'] = f"http://localhost:{backend_port}"
    
    try:
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "frontend/streamlit_app.py",
            "--server.port", str(frontend_port),
            "--server.address", "localhost"
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for frontend to start
        for i in range(15):  # Wait up to 15 seconds
            time.sleep(1)
            try:
                response = requests.get(f"http://localhost:{frontend_port}", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Frontend started successfully on port {frontend_port}")
                    return frontend_port
            except:
                pass
        
        print("❌ Frontend failed to start within 15 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🤖 AI Booking Agent - Startup Script")
    print("=" * 50)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  No .env file found. Creating from template...")
        if Path("env_template.txt").exists():
            import shutil
            shutil.copy("env_template.txt", ".env")
            print("✅ Created .env file from template. Please edit it with your configuration.")
        else:
            print("❌ No env_template.txt found. Please create a .env file manually.")
    
    # Start backend
    backend_port = start_backend()
    if not backend_port:
        print("❌ Failed to start backend. Exiting.")
        return 1
    
    # Start frontend
    frontend_port = start_frontend(backend_port)
    if not frontend_port:
        print("❌ Failed to start frontend. Exiting.")
        return 1
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 AI Booking Agent is now running!")
    print(f"📍 Backend API: http://localhost:{backend_port}")
    print(f"📍 API Docs:   http://localhost:{backend_port}/docs")
    print(f"📍 Frontend:   http://localhost:{frontend_port}")
    print(f"📍 Admin:      http://localhost:{backend_port}/admin/status")
    print("\n🔄 Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 