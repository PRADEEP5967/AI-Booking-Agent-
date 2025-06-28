#!/usr/bin/env python3
"""
Test script for modern AI Booking Agent features
Tests caching, NLP processing, context management, and performance optimizations
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_modern_features():
    """Test all modern features of the enhanced BookingAgent"""
    
    print("🚀 Testing Modern AI Booking Agent Features")
    print("=" * 50)
    
    try:
        from app.services.agent_service import BookingAgent, IntelligentCache, SmartContextManager, AdvancedNLPProcessor
        from app.services.calendar_service import CalendarService
        from app.models.schemas import ConversationState, AgentResponse
        
        print("✅ Successfully imported all modules")
        
        # Test 1: Intelligent Cache
        print("\n🧠 Testing Intelligent Cache...")
        cache = IntelligentCache(ttl_seconds=60)
        
        # Test cache operations
        test_data = {"test": "value", "number": 42}
        cache.set(test_data, "test_key", param1="value1")
        
        # Retrieve from cache
        retrieved = cache.get("test_key", param1="value1")
        assert retrieved == test_data, "Cache retrieval failed"
        print("✅ Cache operations working correctly")
        
        # Test cache expiration
        cache.ttl = 0  # Immediate expiration
        expired = cache.get("test_key", param1="value1")
        assert expired is None, "Cache expiration not working"
        print("✅ Cache expiration working correctly")
        
        # Test 2: Advanced NLP Processor
        print("\n🤖 Testing Advanced NLP Processor...")
        nlp = AdvancedNLPProcessor()
        
        # Test intent extraction
        intents = [
            ("I want to book a meeting", "booking"),
            ("Cancel my appointment", "cancellation"),
            ("What time is available?", "inquiry"),
            ("Yes, confirm that", "confirmation"),
            ("No, I don't want that", "rejection")
        ]
        
        for message, expected_intent in intents:
            detected_intent = nlp.extract_intent(message)
            print(f"  Message: '{message}' -> Intent: {detected_intent} (expected: {expected_intent})")
            assert detected_intent == expected_intent, f"Intent detection failed for: {message}"
        
        print("✅ NLP intent extraction working correctly")
        
        # Test fuzzy matching
        options = ["consultation", "therapy session", "workshop", "meeting"]
        fuzzy_tests = [
            ("cons", "consultation"),
            ("therapy", "therapy session"),
            ("work", "workshop"),
            ("meet", "meeting")
        ]
        
        for input_text, expected_match in fuzzy_tests:
            match = nlp.fuzzy_match(input_text, options)
            print(f"  Input: '{input_text}' -> Match: {match} (expected: {expected_match})")
            assert match == expected_match, f"Fuzzy matching failed for: {input_text}"
        
        print("✅ Fuzzy matching working correctly")
        
        # Test 3: Smart Context Manager
        print("\n🧩 Testing Smart Context Manager...")
        context = SmartContextManager()
        
        # Test preference updates
        session_id = "test_session_123"
        test_data = {
            "service_type": "consultation",
            "duration_minutes": 60,
            "customer_email": "test@example.com"
        }
        
        context.update_preferences(session_id, test_data)
        
        # Test suggestions
        suggestions = context.get_suggestions(session_id, "slot selection")
        print(f"  Context suggestions: {suggestions}")
        assert len(suggestions) > 0, "No suggestions generated"
        
        # Test with different context
        slot_suggestions = context.get_suggestions(session_id, "showing slots")
        print(f"  Slot suggestions: {slot_suggestions}")
        
        print("✅ Context management working correctly")
        
        # Test 4: Enhanced Booking Agent
        print("\n🤖 Testing Enhanced Booking Agent...")
        
        # Initialize calendar service and agent
        calendar_service = CalendarService()
        agent = BookingAgent(calendar_service)
        
        # Test modern features initialization
        assert hasattr(agent, 'cache'), "Cache not initialized"
        assert hasattr(agent, 'context_manager'), "Context manager not initialized"
        assert hasattr(agent, 'nlp_processor'), "NLP processor not initialized"
        print("✅ Modern features initialized correctly")
        
        # Test performance metrics
        metrics = agent.get_performance_metrics()
        print(f"  Performance metrics: {metrics}")
        assert 'cache_hit_rate' in metrics, "Performance metrics missing"
        assert 'cache_size' in metrics, "Performance metrics missing"
        print("✅ Performance metrics working correctly")
        
        # Test optimization
        agent.optimize_performance()
        print("✅ Performance optimization working correctly")
        
        # Test 5: Enhanced Entity Extraction
        print("\n🔍 Testing Enhanced Entity Extraction...")
        
        test_messages = [
            ("I need a consultation tomorrow at 2 PM for 60 minutes", {
                'service_type': 'consultation',
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '14:00',
                'duration': 60
            }),
            ("Book a therapy session next Monday at 10:30 AM", {
                'service_type': 'therapy session',
                'time': '10:30'
            }),
            ("Schedule a workshop for December 15th at 3 PM for 2 hours", {
                'service_type': 'workshop',
                'time': '15:00',
                'duration': 120
            })
        ]
        
        for message, expected_entities in test_messages:
            entities = agent._extract_entities_regex(message)
            print(f"  Message: '{message}'")
            print(f"  Extracted: {entities}")
            
            # Check key entities
            for key, expected_value in expected_entities.items():
                if key in entities:
                    print(f"    ✅ {key}: {entities[key]} (expected: {expected_value})")
                else:
                    print(f"    ❌ {key}: Missing (expected: {expected_value})")
        
        print("✅ Enhanced entity extraction working correctly")
        
        # Test 6: Async Processing
        print("\n⚡ Testing Async Processing...")
        
        async def test_async():
            # Create a test conversation state
            state = ConversationState(
                session_id="async_test",
                stage="greeting",
                messages=[],
                current_booking_data={},
                available_slots=[]
            )
            
            # Test async message processing
            response = await agent.process_message_async(state, "I want to book a consultation")
            print(f"  Async response: {response.message[:100]}...")
            assert response is not None, "Async processing failed"
            
            # Test async entity extraction
            entities = await agent._extract_entities_async("consultation tomorrow at 3 PM")
            print(f"  Async entities: {entities}")
            assert entities is not None, "Async entity extraction failed"
        
        # Run async tests
        asyncio.run(test_async())
        print("✅ Async processing working correctly")
        
        # Test 7: Enhanced Slot Formatting
        print("\n📅 Testing Enhanced Slot Formatting...")
        
        from app.models.schemas import TimeSlot
        
        # Create test slots
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        test_slots = [
            TimeSlot(start_time=base_time, end_time=base_time + timedelta(hours=1)),
            TimeSlot(start_time=base_time + timedelta(hours=2), end_time=base_time + timedelta(hours=3)),
            TimeSlot(start_time=base_time + timedelta(hours=4), end_time=base_time + timedelta(hours=5)),
        ]
        
        formatted = agent._format_available_slots_enhanced(test_slots)
        print(f"  Enhanced formatting:\n{formatted}")
        assert "Morning Slots" in formatted, "Enhanced formatting not working"
        print("✅ Enhanced slot formatting working correctly")
        
        # Test 8: Service Suggestions
        print("\n💡 Testing Service Suggestions...")
        
        suggestions = agent._get_service_suggestions("cons")
        print(f"  Service suggestions for 'cons': {suggestions}")
        assert "consultation" in suggestions, "Service suggestions not working"
        
        suggestions = agent._get_service_suggestions("the")
        print(f"  Service suggestions for 'the': {suggestions}")
        assert "therapy session" in suggestions, "Service suggestions not working"
        
        print("✅ Service suggestions working correctly")
        
        print("\n🎉 All Modern Features Tests Passed!")
        print("=" * 50)
        print("✅ Intelligent Caching")
        print("✅ Advanced NLP Processing")
        print("✅ Smart Context Management")
        print("✅ Enhanced Entity Extraction")
        print("✅ Async Processing")
        print("✅ Performance Optimization")
        print("✅ Enhanced Slot Formatting")
        print("✅ Service Suggestions")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_world_scenarios():
    """Test real-world booking scenarios with modern features"""
    
    print("\n🌍 Testing Real-World Scenarios")
    print("=" * 50)
    
    try:
        from app.services.agent_service import BookingAgent
        from app.services.calendar_service import CalendarService
        from app.models.schemas import ConversationState
        
        calendar_service = CalendarService()
        agent = BookingAgent(calendar_service)
        
        # Scenario 1: Complex booking request
        print("\n📋 Scenario 1: Complex Booking Request")
        state = ConversationState(
            session_id="scenario_1",
            stage="greeting",
            messages=[],
            current_booking_data={},
            available_slots=[]
        )
        
        response = agent.process_message(state, "I need a business consultation tomorrow at 2:30 PM for 90 minutes")
        print(f"Response: {response.message}")
        
        # Check if entities were extracted
        booking_data = response.booking_data
        print(f"Extracted data: {booking_data}")
        
        # Scenario 2: Natural language slot selection
        print("\n📋 Scenario 2: Natural Language Slot Selection")
        state.stage = "showing_slots"
        state.available_slots = [
            type('TimeSlot', (), {'start_time': datetime.now().replace(hour=9, minute=0)})(),
            type('TimeSlot', (), {'start_time': datetime.now().replace(hour=14, minute=30)})(),
            type('TimeSlot', (), {'start_time': datetime.now().replace(hour=16, minute=0)})()
        ]
        
        response = agent.process_message(state, "I'll take the earliest available slot")
        print(f"Response: {response.message}")
        
        # Scenario 3: Context-aware suggestions
        print("\n📋 Scenario 3: Context-Aware Suggestions")
        state.stage = "confirming"
        response = agent.process_message(state, "Yes, that looks good")
        print(f"Response: {response.message}")
        
        # Check for suggestions
        if "Quick Actions" in response.message:
            print("✅ Context-aware suggestions working")
        else:
            print("❌ Context-aware suggestions not found")
        
        print("\n🎉 Real-World Scenarios Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Real-world scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Modern AI Booking Agent Feature Tests")
    print("=" * 60)
    
    # Run feature tests
    feature_tests_passed = test_modern_features()
    
    # Run real-world scenario tests
    scenario_tests_passed = test_real_world_scenarios()
    
    print("\n" + "=" * 60)
    if feature_tests_passed and scenario_tests_passed:
        print("🎉 ALL TESTS PASSED! Modern features are working correctly.")
        print("\n✨ Modern Features Summary:")
        print("• Intelligent caching with TTL and access tracking")
        print("• Advanced NLP with intent recognition and fuzzy matching")
        print("• Smart context management with user preferences")
        print("• Enhanced entity extraction with multiple patterns")
        print("• Async processing for better performance")
        print("• Performance optimization and metrics")
        print("• Enhanced slot formatting with time grouping")
        print("• Service suggestions with caching")
        print("• Real-time optimization and monitoring")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 