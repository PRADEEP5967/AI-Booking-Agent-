#!/usr/bin/env python3
"""
Test script for improved LLM services
"""

import os
import sys
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_service():
    """Test the LLM service functionality"""
    try:
        from app.services.llm_service import get_llm_service, Message, MessageRole
        
        print("🔧 Testing LLM Service...")
        
        # Get LLM service
        llm_service = get_llm_service()
        print(f"✅ LLM Service initialized")
        print(f"📋 Available providers: {llm_service.get_available_providers()}")
        
        # Test basic generation
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello! How are you?")
        ]
        
        print("🤖 Testing LLM generation...")
        response = llm_service.generate(messages=messages, max_tokens=100, temperature=0.7)
        print(f"✅ LLM Response: {response.content[:100]}...")
        
        # Test entity extraction
        print("🔍 Testing entity extraction...")
        schema = {
            "date": "string (YYYY-MM-DD format)",
            "time": "string (HH:MM format)",
            "duration": "integer (minutes)"
        }
        
        text = "I want to book a meeting for tomorrow at 2 PM for 30 minutes"
        entities = llm_service.extract_entities(text, schema)
        print(f"✅ Extracted entities: {entities}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Service test failed: {e}")
        logger.exception("LLM Service test failed")
        return False

def test_agent_service():
    """Test the agent service functionality"""
    try:
        from app.services.agent_service import BookingAgent
        from app.models.schemas import ConversationState
        
        print("🤖 Testing Agent Service...")
        
        # Create agent
        agent = BookingAgent()
        print("✅ Agent initialized")
        
        # Create conversation state
        state = ConversationState(session_id="test-123", messages=[])
        
        # Test message processing
        test_messages = [
            "Hello, I'd like to book a meeting",
            "Tomorrow at 2 PM for 30 minutes",
            "Yes, that's correct"
        ]
        
        for i, message in enumerate(test_messages):
            print(f"📝 Processing message {i+1}: {message}")
            response = agent.process_message(state, message)
            print(f"🤖 Agent response: {response.get('message', 'No response')[:100]}...")
            print(f"📊 Stage: {response.get('stage', 'unknown')}")
            print(f"📋 Booking data: {response.get('booking_data', {})}")
            print("---")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent Service test failed: {e}")
        logger.exception("Agent Service test failed")
        return False

def test_backward_compatibility():
    """Test backward compatibility functions"""
    try:
        from app.services.llm_service import call_llm, async_call_llm
        
        print("🔄 Testing backward compatibility...")
        
        # Test sync call
        response = call_llm("Hello! How are you?", max_tokens=50)
        print(f"✅ Sync call response: {response[:50]}...")
        
        # Test async call
        import asyncio
        async def test_async():
            response = await async_call_llm("Hello! How are you?", max_tokens=50)
            print(f"✅ Async call response: {response[:50]}...")
        
        asyncio.run(test_async())
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        logger.exception("Backward compatibility test failed")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting LLM Services Tests...")
    print("=" * 50)
    
    tests = [
        ("LLM Service", test_llm_service),
        ("Agent Service", test_agent_service),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLM services are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 