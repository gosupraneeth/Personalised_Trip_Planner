#!/usr/bin/env python3
"""
Test script to demonstrate the improved itinerary planning with realistic timing.
"""

import sys
import logging
from datetime import date, timedelta
from decimal import Decimal

# Add the project root to the path
sys.path.append('/Users/prgosu/Projects/PersonalisedTripPlanner2')

from schemas import (
    TripRequest, POI, POICategory, Coordinates, Address, 
    WeatherInfo, WeatherCondition, GroupType, BudgetRange
)
from agents.place_finder import PlaceFinderAgent
from agents.itinerary_planner import ItineraryPlannerAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_pois():
    """Create sample POIs for testing with various optimal timing needs."""
    sample_pois = [
        POI(
            id="1",
            name="Nandi Hills Sunrise Point",
            description="Breathtaking hilltop location famous for spectacular sunrise views and cool morning breeze",
            category=POICategory.ATTRACTION,
            coordinates=Coordinates(latitude=13.3707, longitude=77.6837),
            address=Address(
                formatted_address="Nandi Hills, Chikkaballapur, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.3,
            review_count=8500,
            estimated_visit_duration=120,
            popularity_score=88.0
        ),
        POI(
            id="2",
            name="ISKCON Bangalore",
            description="Beautiful temple complex with stunning architecture, peaceful gardens, and morning prayer sessions",
            category=POICategory.RELIGIOUS,
            coordinates=Coordinates(latitude=12.9716, longitude=77.5946),
            address=Address(
                formatted_address="Hare Krishna Hill, Chord Road, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.5,
            review_count=5000,
            estimated_visit_duration=90,
            popularity_score=85.0
        ),
        POI(
            id="3", 
            name="Lalbagh Botanical Garden",
            description="A beautiful sprawling garden with diverse flora and fauna, perfect for peaceful walks and nature photography",
            category=POICategory.PARK,
            coordinates=Coordinates(latitude=12.9507, longitude=77.5848),
            address=Address(
                formatted_address="Mavalli, Bengaluru, Karnataka",
                city="Bangalore", 
                country="India"
            ),
            rating=4.3,
            review_count=8000,
            estimated_visit_duration=120,
            popularity_score=82.0
        ),
        POI(
            id="4",
            name="Visvesvaraya Industrial & Technological Museum", 
            description="Interactive science museum with fascinating exhibits on technology and innovation",
            category=POICategory.MUSEUM,
            coordinates=Coordinates(latitude=12.9717, longitude=77.5925),
            address=Address(
                formatted_address="Kasturba Road, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.1,
            review_count=3000,
            estimated_visit_duration=150,
            popularity_score=75.0
        ),
        POI(
            id="5",
            name="UB City Mall",
            description="Luxury shopping destination with high-end brands, fine dining, and air-conditioned comfort",
            category=POICategory.SHOPPING,
            coordinates=Coordinates(latitude=12.9716, longitude=77.6198),
            address=Address(
                formatted_address="UB City Mall, Vittal Mallya Road, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.2,
            review_count=3500,
            estimated_visit_duration=180,
            popularity_score=76.0
        ),
        POI(
            id="6",
            name="Toit Brewpub",
            description="Popular craft brewery and restaurant known for fresh beer and great evening atmosphere",
            category=POICategory.NIGHTLIFE,
            coordinates=Coordinates(latitude=12.9719, longitude=77.6205),
            address=Address(
                formatted_address="Indiranagar, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.4,
            review_count=4200,
            estimated_visit_duration=150,
            popularity_score=81.0
        ),
        POI(
            id="7",
            name="Cubbon Park",
            description="Large urban park perfect for evening walks, jogging, and outdoor activities with lush greenery",
            category=POICategory.PARK,
            coordinates=Coordinates(latitude=12.9762, longitude=77.5993),
            address=Address(
                formatted_address="Cubbon Park, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.2,
            review_count=6500,
            estimated_visit_duration=90,
            popularity_score=79.0
        ),
        POI(
            id="8",
            name="Sunset Point - Nandi Hills",
            description="Spectacular viewpoint offering panoramic sunset views over the Bangalore plains",
            category=POICategory.ATTRACTION,
            coordinates=Coordinates(latitude=13.3709, longitude=77.6840),
            address=Address(
                formatted_address="Nandi Hills, Chikkaballapur, Bangalore",
                city="Bangalore",
                country="India"
            ),
            rating=4.5,
            review_count=7200,
            estimated_visit_duration=90,
            popularity_score=87.0
        )
    ]
    return sample_pois

def create_sample_trip_request():
    """Create a sample trip request."""
    start_date = date.today() + timedelta(days=7)
    return TripRequest(
        destination="Bangalore",
        start_date=start_date,
        end_date=start_date + timedelta(days=2),  # 3 day trip to showcase timing variety
        group_type="couple",
        number_of_travelers=2,
        budget_range="moderate",  # Using correct enum value
        special_interests=["culture", "nature", "food", "photography"]
    )

def create_sample_weather():
    """Create sample weather data for 3 days."""
    return [
        WeatherInfo(
            date=date.today() + timedelta(days=7),
            temperature_high=28,
            temperature_low=18,
            condition=WeatherCondition.SUNNY,
            humidity=65,
            wind_speed=10
        ),
        WeatherInfo(
            date=date.today() + timedelta(days=8),
            temperature_high=33,
            temperature_low=24,
            condition=WeatherCondition.SUNNY,
            humidity=70,
            wind_speed=8
        ),
        WeatherInfo(
            date=date.today() + timedelta(days=9),
            temperature_high=26,
            temperature_low=20,
            condition=WeatherCondition.PARTLY_CLOUDY,
            humidity=75,
            wind_speed=12
        )
    ]

def test_improved_itinerary():
    """Test the improved itinerary planning."""
    logger.info("Testing improved itinerary planning...")
    
    # Create test data
    trip_request = create_sample_trip_request()
    pois = create_sample_pois()
    weather_data = create_sample_weather()
    
    # Mock vertex config (normally would come from config.yaml)
    vertex_config = {
        "project_id": "test-project",
        "location": "us-central1",
        "model": "gemini-1.5-pro"
    }
    
    try:
        # Test place finder enhancement
        logger.info("Testing place enhancement...")
        place_finder = PlaceFinderAgent(vertex_config)
        
        # Enhance POIs (this would normally happen in find_places)
        enhanced_pois = []
        for poi in pois:
            enhanced_poi = place_finder._enhance_poi_details(poi, trip_request)
            enhanced_pois.append(enhanced_poi)
            logger.info(f"Enhanced {poi.name}: {enhanced_poi.estimated_visit_duration}min, Score: {enhanced_poi.popularity_score}")
        
        # Test itinerary creation
        logger.info("Testing itinerary planning...")
        itinerary_planner = ItineraryPlannerAgent(vertex_config)
        
        response = itinerary_planner.create_itinerary(
            trip_request,
            enhanced_pois,
            weather_data
        )
        
        if response.success:
            itinerary = response.data["itinerary"]
            summary = response.data["summary"]
            
            logger.info("✅ Itinerary created successfully!")
            print(f"\n🎯 **Trip Summary:**")
            print(f"📍 **Destination:** {summary['destination']}")
            print(f"📅 **Duration:** {summary['duration_days']} days")
            print(f"💰 **Total Estimated Cost:** {summary['total_cost']}")
            print(f"🎯 **Activities:** {summary['total_activities']}")
            print(f"⏰ **Total Time:** {summary['total_estimated_time']}")
            print(f"📊 **Avg Activities/Day:** {summary['average_activities_per_day']}")
            
            print(f"\n📋 **Daily Itinerary:**")
            for day_summary in summary['daily_breakdown']:
                print(f"**Day {day_summary['day']}** ({day_summary['activities']} activities, {day_summary['estimated_cost']}, {day_summary['total_time']})")
                print(f"  🕘 {day_summary['time_range']}")
                
                # Get detailed items for this day
                day_data = next(day for day in itinerary['days'] if day['day'] == day_summary['day'])
                
                for item in day_data['items']:
                    poi_name = item['poi']['name']
                    time_slot = item['time_slot']
                    notes = item.get('notes', '')
                    print(f"  • {poi_name} ({time_slot})")
                    if notes:
                        # Show only the description part, not all notes
                        description = notes.split(' | ')[0] if ' | ' in notes else notes
                        print(f"    {description}")
                
                print()
        
        else:
            logger.error(f"Failed to create itinerary: {response.error}")
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_itinerary()