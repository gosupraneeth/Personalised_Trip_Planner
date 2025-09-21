#!/usr/bin/env python3
"""
Test script to verify enhanced features: currency localization, complete activity lists, and transportation details.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from agents.itinerary_planner import ItineraryPlannerAgent
from schemas.trip_models import TripRequest
from tools.maps_api import MapsApiTool
from schemas.poi_models import POI, POICategory, Coordinates
from schemas.weather_transport_models import WeatherCondition
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_currency_localization():
    """Test that currency is properly localized for different destinations."""
    from config import VertexAIConfig
    vertex_config = VertexAIConfig()
    planner = ItineraryPlannerAgent(vertex_config)
    
    # Test Indian destination (should use INR ₹)
    currency_code, symbol, rate = planner._get_destination_currency("Bangalore")
    assert currency_code == "INR"
    assert symbol == "₹"
    assert rate == 83.0
    
    # Test formatting
    formatted = planner._format_currency(Decimal("100"), "Bangalore")
    assert "₹" in formatted
    assert "8,300" in formatted  # 100 USD * 83 rate
    
    # Test US destination
    currency_code, symbol, rate = planner._get_destination_currency("New York")
    assert currency_code == "USD"
    assert symbol == "$"
    assert rate == 1.0
    
    formatted = planner._format_currency(Decimal("100"), "New York")
    assert "$100.00" == formatted

def test_enhanced_transportation():
    """Test enhanced transportation details with multiple modes."""
    planner = ItineraryPlannerAgent()
    maps_tool = MapsApiTool()
    
    # Create sample POIs with coordinates
    poi1 = POI(
        name="ISKCON Temple",
        category=POICategory.RELIGIOUS,
        address="Sri Radha Krishna Temple, Rajajinagar, Bangalore",
        coordinates=Coordinates(latitude=12.9716, longitude=77.5946),
        rating=4.5,
        description="Beautiful temple"
    )
    
    poi2 = POI(
        name="Cubbon Park",
        category=POICategory.PARK,
        address="Cubbon Park, Bangalore",
        coordinates=Coordinates(latitude=12.9698, longitude=77.5986),
        rating=4.3,
        description="Large urban park"
    )
    
    # Test transport calculation
    transport = planner._calculate_transport(poi1, poi2, maps_tool, "Bangalore")
    
    if transport:
        print(f"\n🚗 Transportation Details:")
        print(f"Mode: {transport.mode}")
        print(f"Duration: {transport.duration_minutes} minutes")
        print(f"Distance: {transport.distance_km:.1f} km")
        print(f"Cost: {transport.cost}")
        print(f"Route Options: {transport.route_description}")
        
        # Check that route description includes multiple transport options
        assert "🚶" in transport.route_description  # Walking
        assert "🚗" in transport.route_description  # Taxi
        assert "₹" in transport.route_description   # INR currency
    
def test_complete_activity_lists():
    """Test that activity lists show all activities without truncation."""
    planner = ItineraryPlannerAgent()
    
    # Create a trip request for Bangalore
    trip_request = TripRequest(
        destination="Bangalore",
        start_date=date.today(),
        end_date=date.today(),
        number_of_travelers=2,
        interests=["temples", "parks", "museums", "breweries", "shopping"]
    )
    
    # Create mock itinerary with many POIs to test truncation
    sample_pois = [
        POI(name=f"Activity {i+1}", category=POICategory.ATTRACTION, address=f"Address {i+1}",
             coordinates=Coordinates(latitude=12.97+i*0.01, longitude=77.59+i*0.01),
             rating=4.0, description=f"Description {i+1}")
        for i in range(6)  # Create 6 activities
    ]
    
    # Mock the create_plan method to return the expected structure
    maps_tool = MapsApiTool()
    
    # Test activity preview generation - this should show all activities
    from schemas.itinerary_models import DayPlan, ItineraryItem
    from datetime import datetime
    
    # Create itinerary items
    items = []
    for i, poi in enumerate(sample_pois):
        item = ItineraryItem(
            poi=poi,
            time_slot=f"{9+i}:00 - {10+i}:00",
            estimated_duration=60,
            cost_estimate=Decimal("10"),
            notes=f"Visit {poi.name}"
        )
        items.append(item)
    
    # Create day plan
    day_plan = DayPlan(
        day=1,
        date=trip_request.start_date,
        items=items,
        total_estimated_cost=Decimal("60"),
        weather=None
    )
    
    # Create mock itinerary
    from schemas.itinerary_models import Itinerary
    itinerary = Itinerary(
        trip_request=trip_request,
        days=[day_plan],
        total_cost=Decimal("60")
    )
    
    # Test summary generation
    summary = planner._create_itinerary_summary(itinerary)
    
    # Check that all activities are shown in the preview
    daily_breakdown = summary["daily_breakdown"]
    assert len(daily_breakdown) == 1
    
    activity_preview = daily_breakdown[0]["activity_preview"]
    print(f"\n📋 Activity Preview: {activity_preview}")
    
    # Should show all 6 activities, not truncated
    assert len(activity_preview) == 6
    assert "Activity 1" in activity_preview
    assert "Activity 6" in activity_preview
    assert "... and" not in str(activity_preview)  # No truncation message
    
    # Test currency localization in summary
    assert "₹" in summary["total_cost"]
    assert "₹" in daily_breakdown[0]["estimated_cost"]

if __name__ == "__main__":
    print("🧪 Testing Enhanced Features...")
    
    print("\n1️⃣ Testing Currency Localization...")
    test_currency_localization()
    print("✅ Currency localization working!")
    
    print("\n2️⃣ Testing Enhanced Transportation...")
    test_enhanced_transportation()
    print("✅ Enhanced transportation working!")
    
    print("\n3️⃣ Testing Complete Activity Lists...")
    test_complete_activity_lists()
    print("✅ Complete activity lists working!")
    
    print("\n🎉 All enhanced features are working correctly!")