#!/usr/bin/env python3
"""
Test script to verify the full trip planning flow with minimal required inputs
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import OrchestratorAgent
from tools.firestore_tool import FirestoreTool
from tools.maps_api import MapsApiTool
from tools.weather_api import WeatherApiTool
from tools.bigquery_tool import BigQueryTool
import uuid

def test_minimal_trip_planning():
    """Test that the system can create an itinerary with minimal required inputs"""
    
    print("🧪 Testing minimal trip planning flow...")
    
    # Initialize tools (minimal setup)
    try:
        firestore_tool = FirestoreTool(project_id="oceanic-abacus-472717-j4")
        maps_tool = MapsApiTool()
        weather_tool = WeatherApiTool()
        bigquery_tool = BigQueryTool()
        
        tools = {
            'firestore': firestore_tool,
            'maps': maps_tool,
            'weather': weather_tool,
            'bigquery': bigquery_tool
        }
        
        # Create orchestrator
        orchestrator = OrchestratorAgent(tools=tools)
        
        # Test user ID
        test_user_id = f"test-{uuid.uuid4().hex[:8]}"
        print(f"📋 Test User ID: {test_user_id}")
        
        # Step 1: Initial minimal request
        print("\n🔄 Step 1: Initial request with minimal info")
        response1 = orchestrator.process_request(
            user_id=test_user_id,
            user_input="I want to go to Barcelona"
        )
        print(f"Response 1: {response1.get('response', 'No response')}")
        print(f"Status: {response1.get('status', 'Unknown')}")
        
        # Step 2: Provide dates
        print("\n🔄 Step 2: Provide dates")
        response2 = orchestrator.process_request(
            user_id=test_user_id,
            user_input="March 15 to March 18, 2024"
        )
        print(f"Response 2: {response2.get('response', 'No response')}")
        print(f"Status: {response2.get('status', 'Unknown')}")
        
        # Step 3: Provide number of travelers
        print("\n🔄 Step 3: Provide number of travelers")
        response3 = orchestrator.process_request(
            user_id=test_user_id,
            user_input="2 people"
        )
        print(f"Response 3: {response3.get('response', 'No response')}")
        print(f"Status: {response3.get('status', 'Unknown')}")
        
        # Check if we got an itinerary
        if response3.get('status') == 'success' and 'itinerary' in response3.get('response', '').lower():
            print("\n✅ SUCCESS: System generated itinerary with minimal inputs!")
        elif 'clarifying_questions' in response3 and len(response3['clarifying_questions']) == 0:
            print("\n✅ SUCCESS: No more clarifying questions needed!")
        else:
            print(f"\n❌ ISSUE: Status = {response3.get('status')}, still asking questions")
            if 'clarifying_questions' in response3:
                print(f"Remaining questions: {response3['clarifying_questions']}")
        
        return response3
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_minimal_trip_planning()
    if result:
        print(f"\n📋 Final result status: {result.get('status', 'Unknown')}")
    else:
        print("\n❌ Test script failed to complete")