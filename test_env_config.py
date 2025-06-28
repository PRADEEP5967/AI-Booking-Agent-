#!/usr/bin/env python3
"""
Test script to verify environment configuration
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_env_variables():
    """Test that environment variables are loaded correctly"""
    print("🔧 Testing Environment Configuration...")
    
    # Test basic environment loading
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test key environment variables
    env_vars = {
        'API_HOST': os.getenv('API_HOST', 'Not set'),
        'API_PORT': os.getenv('API_PORT', 'Not set'),
        'CALENDAR_ID': os.getenv('CALENDAR_ID', 'Not set'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'Not set'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'Not set'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', 'Not set'),
    }
    
    print("\n📋 Environment Variables:")
    for key, value in env_vars.items():
        if 'API_KEY' in key:
            # Mask API keys for security
            display_value = value[:10] + "..." if value != 'Not set' and len(value) > 10 else value
        else:
            display_value = value
        print(f"  {key}: {display_value}")
    
    # Test settings configuration
    try:
        from app.config.settings import settings
        print(f"\n✅ Settings loaded successfully")
        print(f"  API Host: {settings.API_HOST}")
        print(f"  API Port: {settings.API_PORT}")
        print(f"  Log Level: {settings.LOG_LEVEL}")
        print(f"  CORS Origins: {settings.CORS_ORIGINS}")
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        return False
    
    # Test credentials directory
    credentials_dir = "credentials"
    if os.path.exists(credentials_dir):
        print(f"\n✅ Credentials directory exists: {credentials_dir}")
        files = os.listdir(credentials_dir)
        print(f"  Files: {files}")
    else:
        print(f"\n⚠️  Credentials directory missing: {credentials_dir}")
        print("  You'll need to set up Google Calendar credentials")
    
    return True

def test_backend_with_env():
    """Test that backend can start with environment configuration"""
    print("\n🚀 Testing Backend with Environment...")
    
    try:
        from app.main import app
        print("✅ Backend imports successfully with environment config")
        
        # Test that settings are being used
        from app.config.settings import settings
        print(f"✅ Using settings: API_HOST={settings.API_HOST}, PORT={settings.API_PORT}")
        
        return True
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def main():
    """Run all environment tests"""
    print("🧪 Environment Configuration Tests\n")
    
    tests = [
        test_env_variables,
        test_backend_with_env
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Environment Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Environment configuration is working correctly!")
        print("\n📝 Next Steps:")
        print("1. Add your API keys to .env file")
        print("2. Set up Google Calendar credentials")
        print("3. Run: python start_backend.py")
        return True
    else:
        print("⚠️  Some environment tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 