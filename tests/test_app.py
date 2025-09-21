"""
Comprehensive test suite for the Trip Planner ADK application.

This file contains both unit tests and integration tests to validate
the functionality of the multi-agent trip planning system.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

# Import application components
from app import TripPlannerApp
from schemas import (
    TripRequest, BudgetRange, GroupType, InterestCategory,
    POI, POICategory, WeatherInfo, Itinerary, AgentResponse
)


class TestTripPlannerApp:
    """Test the main application functionality."""
    
    @pytest.fixture
    def app(self):
        """Create a test application instance."""
        with patch.dict('os.environ', {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_MAPS_API_KEY': 'test-maps-key',
            'OPENWEATHER_API_KEY': 'test-weather-key',
            'STRIPE_API_KEY': 'test-stripe-key'
        }):
            return TripPlannerApp()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session object."""
        session = Mock()
        session.id = "test-session-123"
        session.user_id = "test-user-456"
        return session
    
    def test_app_initialization(self, app):
        """Test that the application initializes correctly."""
        assert app is not None
        assert hasattr(app, 'tools')
        assert hasattr(app, 'agents')
        assert 'orchestrator' in app.agents
        assert len(app.agents) >= 5  # Core agents
    
    def test_configuration_loading(self, app):
        """Test configuration loading from environment variables."""
        config = app.config
        assert config['project_id'] == 'test-project'
        assert config['google_maps_api_key'] == 'test-maps-key'
        assert config['vertex_ai']['project_id'] == 'test-project'
    
    @pytest.mark.asyncio
    async def test_basic_trip_planning(self, app, mock_session):
        """Test basic trip planning workflow."""
        # Mock the orchestrator response
        mock_response = AgentResponse(
            agent_name="orchestrator",
            success=True,
            data={
                "itinerary": {
                    "id": "test-itinerary-123",
                    "trip_request": {
                        "destination": "Paris, France",
                        "start_date": "2024-06-01T00:00:00",
                        "duration_days": 3,
                        "number_of_travelers": 2,
                        "budget_range": "medium",
                        "group_type": "couple",
                        "interests": ["culture", "food"]
                    },
                    "days": [
                        {
                            "day": 1,
                            "date": "2024-06-01",
                            "items": [
                                {
                                    "id": "activity-1",
                                    "title": "Louvre Museum",
                                    "start_time": "09:00",
                                    "end_time": "12:00",
                                    "estimated_cost": 15.0
                                }
                            ],
                            "total_estimated_cost": 150.0
                        }
                    ],
                    "total_cost": 450.0,
                    "created_at": "2024-01-01T00:00:00",
                    "version": 1
                },
                "session_id": "test-session-123",
                "ai_insights": {
                    "highlights": ["Amazing art at the Louvre", "French cuisine experience"]
                }
            },
            message="Your 3-day trip to Paris is ready!"
        )
        
        with patch.object(app.agents['orchestrator'], 'plan_trip', return_value=mock_response):
            response = await app.process_user_input(
                "Plan a 3-day trip to Paris for 2 people, budget $2000, interested in culture and food",
                mock_session
            )
        
        assert "Paris" in response
        assert "3-day" in response
        assert "450.00" in response
        assert "Louvre Museum" in response


class TestDataSchemas:
    """Test the Pydantic data schemas."""
    
    def test_trip_request_validation(self):
        """Test TripRequest schema validation."""
        # Valid trip request
        trip_data = {
            "destination": "Tokyo, Japan",
            "start_date": datetime.now() + timedelta(days=30),
            "duration_days": 5,
            "number_of_travelers": 2,
            "budget_range": BudgetRange.MEDIUM,
            "group_type": GroupType.COUPLE,
            "interests": [InterestCategory.CULTURE, InterestCategory.FOOD]
        }
        
        trip_request = TripRequest(**trip_data)
        assert trip_request.destination == "Tokyo, Japan"
        assert trip_request.duration_days == 5
        assert trip_request.budget_range == BudgetRange.MEDIUM
    
    def test_poi_validation(self):
        """Test POI schema validation."""
        poi_data = {
            "id": "poi-123",
            "name": "Tokyo National Museum",
            "category": POICategory.MUSEUM,
            "location": {
                "latitude": 35.7186,
                "longitude": 139.7754,
                "address": "Tokyo, Japan"
            },
            "rating": 4.5,
            "price_level": 2,
            "opening_hours": {
                "monday": "09:00-17:00",
                "tuesday": "09:00-17:00"
            },
            "estimated_duration_minutes": 120,
            "estimated_cost": Decimal("15.00")
        }
        
        poi = POI(**poi_data)
        assert poi.name == "Tokyo National Museum"
        assert poi.rating == 4.5
        assert poi.estimated_cost == Decimal("15.00")
    
    def test_weather_info_validation(self):
        """Test WeatherInfo schema validation."""
        weather_data = {
            "date": datetime.now().date(),
            "temperature_celsius": 22.5,
            "condition": "sunny",
            "description": "Clear sky",
            "humidity_percent": 65,
            "wind_speed_kmh": 12.3,
            "precipitation_chance_percent": 10
        }
        
        weather = WeatherInfo(**weather_data)
        assert weather.temperature_celsius == 22.5
        assert weather.condition == "sunny"
        assert weather.precipitation_chance_percent == 10


class TestUserIntentAgent:
    """Test the User Intent Agent functionality."""
    
    @pytest.fixture
    def user_intent_agent(self):
        """Create a User Intent Agent for testing."""
        from agents.user_intent import UserIntentAgent
        vertex_config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-1.5-pro"
        }
        return UserIntentAgent(vertex_config)
    
    def test_extract_trip_requirements(self, user_intent_agent):
        """Test trip requirement extraction from user input."""
        user_input = "I want to visit Paris for 4 days with my family, budget around $3000, we love museums and food"
        
        # Mock the Vertex AI response
        mock_ai_response = {
            "destination": "Paris, France",
            "duration_days": 4,
            "number_of_travelers": 4,
            "budget_estimate": 3000,
            "group_type": "family",
            "interests": ["culture", "food", "museums"]
        }
        
        with patch.object(user_intent_agent, '_call_vertex_ai', return_value=json.dumps(mock_ai_response)):
            response = user_intent_agent.analyze_user_input(user_input)
        
        assert response.success
        assert "Paris" in response.data["destination"]
        assert response.data["duration_days"] == 4
        assert "family" in response.data["group_type"]
    
    def test_validate_complete_requirements(self, user_intent_agent):
        """Test validation of complete trip requirements."""
        complete_data = {
            "destination": "Tokyo, Japan",
            "start_date": "2024-06-01",
            "duration_days": 5,
            "number_of_travelers": 2,
            "budget_estimate": 2500,
            "group_type": "couple",
            "interests": ["culture", "food"]
        }
        
        validation = user_intent_agent.validate_trip_requirements(complete_data)
        assert validation["is_complete"] is True
        assert len(validation["missing_required"]) == 0
    
    def test_validate_incomplete_requirements(self, user_intent_agent):
        """Test validation of incomplete trip requirements."""
        incomplete_data = {
            "destination": "Tokyo, Japan",
            "duration_days": 5
            # Missing other required fields
        }
        
        validation = user_intent_agent.validate_trip_requirements(incomplete_data)
        assert validation["is_complete"] is False
        assert "number_of_travelers" in validation["missing_required"]


class TestPlaceFinderAgent:
    """Test the Place Finder Agent functionality."""
    
    @pytest.fixture
    def place_finder_agent(self):
        """Create a Place Finder Agent for testing."""
        from agents.place_finder import PlaceFinderAgent
        vertex_config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-1.5-pro"
        }
        return PlaceFinderAgent(vertex_config)
    
    @pytest.fixture
    def mock_maps_tool(self):
        """Create a mock Maps API tool."""
        maps_tool = Mock()
        maps_tool.search_nearby_places.return_value = [
            {
                "place_id": "place-1",
                "name": "Tokyo National Museum",
                "types": ["museum"],
                "geometry": {"location": {"lat": 35.7186, "lng": 139.7754}},
                "rating": 4.5,
                "price_level": 2
            }
        ]
        return maps_tool
    
    @pytest.fixture
    def mock_bigquery_tool(self):
        """Create a mock BigQuery tool."""
        bigquery_tool = Mock()
        bigquery_tool.get_popular_pois.return_value = []
        bigquery_tool.cache_poi.return_value = True
        return bigquery_tool
    
    def test_find_places_for_trip(self, place_finder_agent, mock_maps_tool, mock_bigquery_tool):
        """Test finding places for a trip request."""
        trip_request_data = {
            "destination": "Tokyo, Japan",
            "start_date": datetime.now() + timedelta(days=30),
            "duration_days": 3,
            "number_of_travelers": 2,
            "budget_range": BudgetRange.MEDIUM,
            "group_type": GroupType.COUPLE,
            "interests": [InterestCategory.CULTURE]
        }
        trip_request = TripRequest(**trip_request_data)
        
        response = place_finder_agent.find_places(
            trip_request=trip_request,
            maps_tool=mock_maps_tool,
            bigquery_tool=mock_bigquery_tool
        )
        
        assert response.success
        assert "places" in response.data
        assert len(response.data["places"]) > 0
        
        # Verify Maps API was called
        mock_maps_tool.search_nearby_places.assert_called()


class TestWeatherAgent:
    """Test the Weather Agent functionality."""
    
    @pytest.fixture
    def weather_agent(self):
        """Create a Weather Agent for testing."""
        from agents.weather import WeatherAgent
        vertex_config = {
            "project_id": "test-project",
            "location": "us-central1",
            "model": "gemini-1.5-pro"
        }
        return WeatherAgent(vertex_config)
    
    @pytest.fixture
    def mock_weather_tool(self):
        """Create a mock Weather API tool."""
        weather_tool = Mock()
        weather_tool.get_forecast.return_value = [
            {
                "date": datetime.now().date(),
                "temperature_celsius": 20.0,
                "condition": "sunny",
                "description": "Clear sky",
                "humidity_percent": 60,
                "wind_speed_kmh": 10.0,
                "precipitation_chance_percent": 5
            }
        ]
        return weather_tool
    
    def test_analyze_weather_for_trip(self, weather_agent, mock_weather_tool):
        """Test weather analysis for a trip."""
        trip_request_data = {
            "destination": "Paris, France",
            "start_date": datetime.now() + timedelta(days=10),
            "duration_days": 4,
            "number_of_travelers": 2,
            "budget_range": BudgetRange.MEDIUM,
            "group_type": GroupType.COUPLE,
            "interests": [InterestCategory.CULTURE]
        }
        trip_request = TripRequest(**trip_request_data)
        
        response = weather_agent.analyze_weather_for_trip(
            trip_request=trip_request,
            weather_tool=mock_weather_tool
        )
        
        assert response.success
        assert "weather_forecast" in response.data
        assert "weather_analysis" in response.data
        
        # Verify weather API was called
        mock_weather_tool.get_forecast.assert_called()
    
    def test_filter_activities_by_weather(self, weather_agent):
        """Test filtering activities based on weather conditions."""
        # Create test POIs
        outdoor_poi = POI(
            id="outdoor-1",
            name="Central Park",
            category=POICategory.PARK,
            location={"latitude": 40.7829, "longitude": -73.9654, "address": "New York, NY"},
            rating=4.5,
            estimated_cost=Decimal("0.00")
        )
        
        indoor_poi = POI(
            id="indoor-1",
            name="Metropolitan Museum",
            category=POICategory.MUSEUM,
            location={"latitude": 40.7794, "longitude": -73.9632, "address": "New York, NY"},
            rating=4.7,
            estimated_cost=Decimal("25.00")
        )
        
        pois = [outdoor_poi, indoor_poi]
        
        # Create test weather data
        rainy_weather = WeatherInfo(
            date=datetime.now().date(),
            temperature_celsius=15.0,
            condition="rainy",
            description="Heavy rain",
            humidity_percent=85,
            wind_speed_kmh=15.0,
            precipitation_chance_percent=90
        )
        
        weather_data = [rainy_weather]
        
        trip_request_data = {
            "destination": "New York, NY",
            "start_date": datetime.now(),
            "duration_days": 1,
            "number_of_travelers": 2,
            "budget_range": BudgetRange.MEDIUM,
            "group_type": GroupType.COUPLE,
            "interests": [InterestCategory.CULTURE]
        }
        trip_request = TripRequest(**trip_request_data)
        
        filtered = weather_agent.filter_activities_by_weather(pois, weather_data, trip_request)
        
        # On rainy days, should prioritize indoor activities
        assert len(filtered["indoor_activities"]) > 0
        assert any(poi.name == "Metropolitan Museum" for poi in filtered["indoor_activities"])


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_trip_planning_workflow(self):
        """Test the complete trip planning workflow end-to-end."""
        # This test would require mock implementations of all external APIs
        # For brevity, we'll test the workflow structure
        
        app = TripPlannerApp()
        
        # Mock session
        session = Mock()
        session.id = "integration-test-session"
        session.user_id = "integration-test-user"
        
        # Mock all tool responses
        with patch.multiple(
            app.tools.get('maps', Mock()),
            search_nearby_places=Mock(return_value=[]),
            get_place_details=Mock(return_value={})
        ):
            with patch.multiple(
                app.tools.get('weather', Mock()),
                get_forecast=Mock(return_value=[])
            ):
                with patch.multiple(
                    app.agents['orchestrator'],
                    plan_trip=Mock(return_value=AgentResponse(
                        agent_name="orchestrator",
                        success=True,
                        data={"itinerary": {"destination": "Test City"}},
                        message="Test trip planned successfully"
                    ))
                ):
                    response = await app.process_user_input(
                        "Plan a weekend trip to San Francisco for 2 people",
                        session
                    )
                    
                    assert "Test trip planned successfully" in response


@pytest.mark.performance
class TestPerformance:
    """Performance tests for the application."""
    
    def test_agent_response_time(self):
        """Test that agents respond within acceptable time limits."""
        # This would measure actual response times
        pass
    
    def test_concurrent_sessions(self):
        """Test handling of multiple concurrent planning sessions."""
        # This would test concurrent session handling
        pass


if __name__ == "__main__":
    # Run specific test scenarios for development
    pytest.main([
        "tests/test_app.py::TestTripPlannerApp::test_app_initialization",
        "tests/test_app.py::TestDataSchemas::test_trip_request_validation",
        "-v"
    ])