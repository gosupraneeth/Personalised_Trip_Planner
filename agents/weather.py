"""
Weather Agent for the Trip Planner ADK application.

This agent analyzes weather conditions and provides recommendations
for trip activities based on weather forecasts.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from adk import LlmAgent
from google.cloud import aiplatform

from schemas import WeatherInfo, POI, TripRequest, AgentResponse
from tools import WeatherApiTool

logger = logging.getLogger(__name__)


class WeatherAgent(LlmAgent):
    """Agent for weather analysis and activity recommendations."""
    
    def __init__(self, vertex_config: Dict[str, Any]):
        """Initialize the Weather Agent."""
        super().__init__(
            name="weather_agent",
            description="Analyzes weather conditions and provides activity recommendations"
        )
        self.vertex_config = vertex_config
        self.model_name = vertex_config.get("model", "gemini-1.5-pro")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=vertex_config["project_id"],
            location=vertex_config["location"]
        )
        
        logger.info("Weather Agent initialized")
    
    def analyze_weather_for_trip(
        self,
        trip_request: TripRequest,
        weather_tool: WeatherApiTool
    ) -> AgentResponse:
        """
        Analyze weather conditions for a trip.
        
        Args:
            trip_request: Trip request details
            weather_tool: Weather API tool
            
        Returns:
            AgentResponse with weather analysis
        """
        try:
            # Get weather data for the trip period
            weather_data = weather_tool.get_weather_for_dates(
                location=trip_request.destination,
                start_date=trip_request.start_date,
                end_date=trip_request.end_date
            )
            
            if not weather_data:
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    error="Could not retrieve weather data for the destination"
                )
            
            # Analyze weather suitability
            weather_analysis = weather_tool.analyze_weather_suitability(weather_data)
            
            # Generate AI recommendations
            ai_recommendations = self._generate_weather_recommendations(
                weather_data,
                trip_request
            )
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "weather_forecast": [w.dict() for w in weather_data],
                    "weather_analysis": weather_analysis,
                    "ai_recommendations": ai_recommendations,
                    "suitable_days": weather_analysis.get("suitable_days", 0),
                    "total_days": len(weather_data)
                },
                message=f"Weather analysis complete for {trip_request.destination}"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing weather: {e}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def filter_activities_by_weather(
        self,
        pois: List[POI],
        weather_data: List[WeatherInfo],
        trip_request: TripRequest
    ) -> Dict[str, List[POI]]:
        """
        Filter and organize POIs by weather suitability.
        
        Args:
            pois: List of POIs to filter
            weather_data: Weather forecast data
            trip_request: Trip request details
            
        Returns:
            Dictionary of POIs organized by weather conditions
        """
        try:
            filtered_activities = {
                "sunny_day_activities": [],
                "rainy_day_activities": [],
                "indoor_activities": [],
                "outdoor_activities": [],
                "all_weather_activities": []
            }
            
            for poi in pois:
                # Categorize POI based on weather sensitivity
                weather_category = self._categorize_poi_by_weather(poi)
                
                if weather_category == "outdoor":
                    filtered_activities["outdoor_activities"].append(poi)
                elif weather_category == "indoor":
                    filtered_activities["indoor_activities"].append(poi)
                    filtered_activities["rainy_day_activities"].append(poi)
                else:  # all_weather
                    filtered_activities["all_weather_activities"].append(poi)
                
                # Add to sunny day activities if outdoor or all-weather
                if weather_category in ["outdoor", "all_weather"]:
                    filtered_activities["sunny_day_activities"].append(poi)
            
            logger.info(f"Categorized {len(pois)} POIs by weather suitability")
            return filtered_activities
            
        except Exception as e:
            logger.error(f"Error filtering activities by weather: {e}")
            return {}
    
    def recommend_daily_activities(
        self,
        day_weather: WeatherInfo,
        available_pois: List[POI],
        trip_request: TripRequest
    ) -> List[POI]:
        """
        Recommend activities for a specific day based on weather.
        
        Args:
            day_weather: Weather forecast for the day
            available_pois: Available POIs for the day
            trip_request: Trip request details
            
        Returns:
            List of recommended POIs for the day
        """
        try:
            # Filter POIs based on weather conditions
            suitable_pois = []
            
            for poi in available_pois:
                if self._is_poi_suitable_for_weather(poi, day_weather):
                    suitable_pois.append(poi)
            
            # Rank POIs based on weather and other factors
            ranked_pois = self._rank_pois_for_weather(
                suitable_pois,
                day_weather,
                trip_request
            )
            
            logger.info(f"Recommended {len(ranked_pois)} activities for {day_weather.condition.value} weather")
            return ranked_pois
            
        except Exception as e:
            logger.error(f"Error recommending daily activities: {e}")
            return available_pois
    
    def _generate_weather_recommendations(
        self,
        weather_data: List[WeatherInfo],
        trip_request: TripRequest
    ) -> Dict[str, Any]:
        """Generate AI-powered weather recommendations."""
        try:
            # Create prompt for weather recommendations
            prompt = self._create_weather_prompt(weather_data, trip_request)
            
            # Call Vertex AI
            response = self._call_vertex_ai(prompt)
            
            if response:
                return self._parse_weather_recommendations(response)
            else:
                return self._generate_fallback_recommendations(weather_data)
                
        except Exception as e:
            logger.error(f"Error generating weather recommendations: {e}")
            return self._generate_fallback_recommendations(weather_data)
    
    def _create_weather_prompt(
        self,
        weather_data: List[WeatherInfo],
        trip_request: TripRequest
    ) -> str:
        """Create prompt for weather-based recommendations."""
        weather_summary = ""
        for i, weather in enumerate(weather_data):
            weather_summary += f"Day {i+1} ({weather.date}): {weather.condition.value}, {weather.temperature_high}°C high, {weather.temperature_low}°C low"
            if weather.precipitation_chance:
                weather_summary += f", {weather.precipitation_chance}% chance of rain"
            weather_summary += "\n"
        
        prompt = f"""
You are a travel weather expert. Analyze the weather forecast and provide recommendations for a trip.

Trip Details:
- Destination: {trip_request.destination}
- Duration: {trip_request.duration_days} days
- Group Type: {trip_request.group_type.value}
- Special Interests: {', '.join(trip_request.special_interests) if trip_request.special_interests else 'None'}

Weather Forecast:
{weather_summary}

Provide recommendations in JSON format:
{{
    "overall_assessment": "brief overall weather assessment",
    "best_days": ["list of best weather days with reasons"],
    "challenging_days": ["list of challenging weather days with reasons"],
    "packing_recommendations": ["what to pack for this weather"],
    "activity_recommendations": {{
        "sunny_days": ["activities for sunny weather"],
        "rainy_days": ["activities for rainy weather"],
        "general": ["activities suitable for any weather"]
    }},
    "travel_tips": ["general travel tips for this weather pattern"]
}}
"""
        return prompt
    
    def _call_vertex_ai(self, prompt: str) -> Optional[str]:
        """Call Vertex AI Gemini model."""
        try:
            from vertexai.generative_models import GenerativeModel
            
            model = GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error calling Vertex AI: {e}")
            return None
    
    def _parse_weather_recommendations(self, response: str) -> Dict[str, Any]:
        """Parse AI weather recommendations response."""
        try:
            import json
            
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                recommendations = json.loads(json_str)
                return recommendations
            
            return {}
            
        except Exception as e:
            logger.error(f"Error parsing weather recommendations: {e}")
            return {}
    
    def _generate_fallback_recommendations(self, weather_data: List[WeatherInfo]) -> Dict[str, Any]:
        """Generate basic weather recommendations as fallback."""
        sunny_days = sum(1 for w in weather_data if w.condition.value == "sunny")
        rainy_days = sum(1 for w in weather_data if w.condition.value == "rainy")
        
        return {
            "overall_assessment": f"Weather varies with {sunny_days} sunny days and {rainy_days} rainy days",
            "best_days": [f"Day {i+1}" for i, w in enumerate(weather_data) if w.is_suitable_for_outdoor],
            "challenging_days": [f"Day {i+1}" for i, w in enumerate(weather_data) if not w.is_suitable_for_outdoor],
            "packing_recommendations": ["umbrella or rain jacket", "comfortable walking shoes", "layers for temperature changes"],
            "activity_recommendations": {
                "sunny_days": ["outdoor sightseeing", "parks and gardens", "walking tours"],
                "rainy_days": ["museums", "indoor markets", "shopping centers"],
                "general": ["restaurants", "cultural sites", "transportation hubs"]
            },
            "travel_tips": ["Check weather updates daily", "Plan indoor backup activities"]
        }
    
    def _categorize_poi_by_weather(self, poi: POI) -> str:
        """Categorize POI by weather dependency."""
        indoor_categories = ["museum", "shopping", "restaurant", "accommodation", "entertainment"]
        outdoor_categories = ["park", "beach", "adventure"]
        
        category = poi.category.value.lower()
        
        if category in indoor_categories:
            return "indoor"
        elif category in outdoor_categories:
            return "outdoor"
        else:
            return "all_weather"
    
    def _is_poi_suitable_for_weather(self, poi: POI, weather: WeatherInfo) -> bool:
        """Check if POI is suitable for given weather conditions."""
        weather_category = self._categorize_poi_by_weather(poi)
        
        # Indoor activities are always suitable
        if weather_category == "indoor":
            return True
        
        # Outdoor activities depend on weather
        if weather_category == "outdoor":
            return weather.is_suitable_for_outdoor
        
        # All-weather activities are generally suitable but prefer good weather
        return True
    
    def _rank_pois_for_weather(
        self,
        pois: List[POI],
        weather: WeatherInfo,
        trip_request: TripRequest
    ) -> List[POI]:
        """Rank POIs based on weather suitability and other factors."""
        def weather_score(poi: POI) -> float:
            score = poi.rating or 3.0
            
            # Boost indoor activities on bad weather days
            if not weather.is_suitable_for_outdoor:
                if self._categorize_poi_by_weather(poi) == "indoor":
                    score += 1.0
            else:
                # Boost outdoor activities on good weather days
                if self._categorize_poi_by_weather(poi) == "outdoor":
                    score += 0.5
            
            # Consider popularity
            if poi.popularity_score:
                score += poi.popularity_score / 100
            
            return score
        
        return sorted(pois, key=weather_score, reverse=True)
    
    def get_weather_alerts(
        self,
        weather_data: List[WeatherInfo],
        trip_request: TripRequest
    ) -> List[Dict[str, Any]]:
        """
        Generate weather alerts for trip planning.
        
        Args:
            weather_data: Weather forecast data
            trip_request: Trip request details
            
        Returns:
            List of weather alerts and recommendations
        """
        alerts = []
        
        try:
            for i, weather in enumerate(weather_data):
                day_num = i + 1
                
                # Temperature alerts
                if weather.temperature_high > 35:
                    alerts.append({
                        "day": day_num,
                        "type": "heat_warning",
                        "message": f"Very hot weather expected ({weather.temperature_high}°C). Stay hydrated and seek shade.",
                        "severity": "high"
                    })
                elif weather.temperature_high < 0:
                    alerts.append({
                        "day": day_num,
                        "type": "cold_warning",
                        "message": f"Freezing temperatures expected ({weather.temperature_high}°C). Dress warmly.",
                        "severity": "high"
                    })
                
                # Precipitation alerts
                if weather.precipitation_chance and weather.precipitation_chance > 70:
                    alerts.append({
                        "day": day_num,
                        "type": "rain_warning",
                        "message": f"High chance of rain ({weather.precipitation_chance}%). Plan indoor activities.",
                        "severity": "medium"
                    })
                
                # Wind alerts
                if weather.wind_speed and weather.wind_speed > 25:
                    alerts.append({
                        "day": day_num,
                        "type": "wind_warning",
                        "message": f"Strong winds expected ({weather.wind_speed} km/h). Outdoor activities may be affected.",
                        "severity": "medium"
                    })
                
                # UV alerts
                if weather.uv_index and weather.uv_index > 8:
                    alerts.append({
                        "day": day_num,
                        "type": "uv_warning",
                        "message": f"High UV index ({weather.uv_index}). Use sunscreen and protective clothing.",
                        "severity": "medium"
                    })
            
            logger.info(f"Generated {len(alerts)} weather alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating weather alerts: {e}")
            return []