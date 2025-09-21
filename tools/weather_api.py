"""
Weather API tool for the Trip Planner ADK application.

This tool provides weather forecasting and analysis functionality
using mock data based on seasonal patterns and location data.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import random
from adk import Tool

from schemas import WeatherInfo, WeatherCondition

logger = logging.getLogger(__name__)


class WeatherApiTool(Tool):
    """Mock weather tool that provides realistic weather forecasts based on seasonal patterns."""
    
    def __init__(self, api_key: str):
        """Initialize the Weather API tool with mock data generation."""
        super().__init__("weather_api_tool", "Mock weather integration for weather data")
        self.api_key = api_key
        logger.info("Weather API tool initialized with mock data generation")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Weather API operations."""
        if operation == "get_current_weather":
            return self.get_current_weather(**kwargs)
        elif operation == "get_forecast":
            return self.get_forecast(**kwargs)
        elif operation == "get_weather_by_coordinates":
            return self.get_weather_by_coordinates(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a location using realistic mock data.
        
        Args:
            location: Location name (e.g., "Tokyo, Japan")
            
        Returns:
            Current weather data or None if error
        """
        try:
            weather_data = self._generate_realistic_weather(location)
            logger.info(f"Retrieved current weather for {location}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting current weather for {location}: {e}")
            return None
    
    def get_forecast(self, location: str, days: int = 5) -> List[Dict[str, Any]]:
        """
        Get weather forecast for multiple days using realistic mock data.
        
        Args:
            location: Location name
            days: Number of days to forecast (1-5)
            
        Returns:
            List of daily weather forecasts
        """
        try:
            forecast_data = []
            current_date = datetime.now().date()
            
            for i in range(days):
                forecast_date = current_date + timedelta(days=i)
                daily_weather = self._generate_realistic_weather(location, forecast_date)
                daily_weather['date'] = forecast_date.isoformat()
                forecast_data.append(daily_weather)
            
            logger.info(f"Retrieved {len(forecast_data)} days forecast for {location}")
            return forecast_data
            
        except Exception as e:
            logger.error(f"Error getting forecast for {location}: {e}")
            return []
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get current weather by coordinates using realistic mock data.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Current weather data or None if error
        """
        try:
            # Use coordinates to determine general climate zone
            location_name = self._get_location_name_from_coords(lat, lon)
            weather_data = self._generate_realistic_weather(location_name)
            weather_data['coordinates'] = [lat, lon]
            
            logger.info(f"Retrieved weather for coordinates {lat}, {lon}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting weather for coordinates {lat}, {lon}: {e}")
            return None
    
    def _generate_realistic_weather(self, location: str, target_date: date = None) -> Dict[str, Any]:
        """Generate realistic weather data based on location and season."""
        if target_date is None:
            target_date = datetime.now().date()
        
        # Determine season based on date (Northern Hemisphere)
        month = target_date.month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "autumn"
        
        # Climate zones based on location
        location_lower = location.lower()
        climate_zone = self._determine_climate_zone(location_lower)
        
        # Generate temperature based on climate and season
        base_temp, temp_variation = self._get_temperature_range(climate_zone, season)
        temperature = base_temp + random.uniform(-temp_variation, temp_variation)
        
        # Generate weather conditions based on season and climate
        condition = self._get_realistic_condition(climate_zone, season)
        
        # Generate other weather parameters
        humidity = random.randint(30, 90)
        wind_speed = random.uniform(5, 25)
        pressure = random.randint(1000, 1025)
        precipitation_chance = self._get_precipitation_chance(condition, season)
        
        return {
            "location": location,
            "temperature": round(temperature, 1),
            "temperature_high": round(temperature + random.uniform(2, 8), 1),
            "temperature_low": round(temperature - random.uniform(2, 8), 1),
            "humidity": humidity,
            "description": self._get_weather_description(condition),
            "condition": condition,
            "wind_speed": round(wind_speed, 1),
            "pressure": pressure,
            "precipitation_chance": precipitation_chance
        }
    
    def _determine_climate_zone(self, location: str) -> str:
        """Determine climate zone based on location."""
        if any(word in location for word in ['delhi', 'mumbai', 'bangalore', 'chennai', 'hyderabad', 'kolkata', 'india']):
            return 'tropical'
        elif any(word in location for word in ['dubai', 'riyadh', 'cairo', 'desert']):
            return 'desert'
        elif any(word in location for word in ['london', 'paris', 'berlin', 'europe']):
            return 'temperate'
        elif any(word in location for word in ['tokyo', 'seoul', 'beijing']):
            return 'continental'
        elif any(word in location for word in ['singapore', 'bangkok', 'kuala lumpur']):
            return 'equatorial'
        elif any(word in location for word in ['sydney', 'melbourne', 'australia']):
            return 'subtropical'
        else:
            return 'temperate'  # default
    
    def _get_temperature_range(self, climate_zone: str, season: str) -> tuple:
        """Get base temperature and variation for climate zone and season."""
        temp_ranges = {
            'tropical': {
                'winter': (25, 5), 'spring': (30, 5), 'summer': (35, 5), 'autumn': (28, 5)
            },
            'desert': {
                'winter': (20, 8), 'spring': (30, 10), 'summer': (40, 8), 'autumn': (25, 8)
            },
            'temperate': {
                'winter': (5, 8), 'spring': (15, 8), 'summer': (25, 6), 'autumn': (12, 8)
            },
            'continental': {
                'winter': (-5, 10), 'spring': (12, 8), 'summer': (28, 6), 'autumn': (8, 8)
            },
            'equatorial': {
                'winter': (28, 3), 'spring': (30, 3), 'summer': (32, 3), 'autumn': (29, 3)
            },
            'subtropical': {
                'winter': (15, 6), 'spring': (22, 6), 'summer': (30, 5), 'autumn': (20, 6)
            }
        }
        return temp_ranges.get(climate_zone, temp_ranges['temperate'])[season]
    
    def _get_realistic_condition(self, climate_zone: str, season: str) -> str:
        """Get realistic weather condition based on climate and season."""
        conditions_by_climate = {
            'tropical': {
                'winter': ['sunny', 'cloudy'],
                'spring': ['sunny', 'cloudy', 'rainy'],
                'summer': ['rainy', 'stormy', 'cloudy'],
                'autumn': ['sunny', 'cloudy', 'rainy']
            },
            'desert': {
                'winter': ['sunny', 'cloudy'],
                'spring': ['sunny', 'cloudy'],
                'summer': ['sunny', 'sunny', 'sunny'],  # Very sunny
                'autumn': ['sunny', 'cloudy']
            },
            'temperate': {
                'winter': ['cloudy', 'rainy', 'snowy'],
                'spring': ['sunny', 'cloudy', 'rainy'],
                'summer': ['sunny', 'cloudy'],
                'autumn': ['cloudy', 'rainy', 'foggy']
            }
        }
        
        default_conditions = ['sunny', 'cloudy', 'rainy']
        possible_conditions = conditions_by_climate.get(climate_zone, {}).get(season, default_conditions)
        return random.choice(possible_conditions)
    
    def _get_weather_description(self, condition: str) -> str:
        """Get weather description for condition."""
        descriptions = {
            'sunny': 'Clear skies with bright sunshine',
            'cloudy': 'Partly cloudy with some cloud cover',
            'rainy': 'Light to moderate rainfall expected',
            'stormy': 'Thunderstorms with heavy rain',
            'snowy': 'Snow showers with cold temperatures',
            'foggy': 'Misty conditions with reduced visibility'
        }
        return descriptions.get(condition, 'Mild weather conditions')
    
    def _get_precipitation_chance(self, condition: str, season: str) -> int:
        """Get precipitation chance based on condition."""
        precipitation_map = {
            'sunny': 5,
            'cloudy': 20,
            'rainy': 80,
            'stormy': 95,
            'snowy': 90,
            'foggy': 30
        }
        return precipitation_map.get(condition, 10)
    
    def _get_location_name_from_coords(self, lat: float, lon: float) -> str:
        """Get approximate location name from coordinates."""
        # Simple mapping based on major cities coordinates
        if 12 <= lat <= 13 and 77 <= lon <= 78:
            return "Bangalore, India"
        elif 28 <= lat <= 29 and 77 <= lon <= 78:
            return "Delhi, India"
        elif 19 <= lat <= 19.5 and 72 <= lon <= 73:
            return "Mumbai, India"
        else:
            return f"Location at {lat:.2f}, {lon:.2f}"
    
    def get_weather_for_dates(
        self,
        location: str,
        start_date: date,
        end_date: date
    ) -> List[WeatherInfo]:
        """
        Get weather information for specific date range.
        
        Args:
            location: Location name
            start_date: Start date for weather data
            end_date: End date for weather data
            
        Returns:
            List of WeatherInfo objects for each date
        """
        weather_data = []
        
        # For dates in the future (up to 5 days), use forecast
        today = date.today()
        
        if start_date <= today + timedelta(days=5):
            forecast_data = self.get_forecast(location, days=5)
            
            current_date = start_date
            while current_date <= end_date and current_date <= today + timedelta(days=5):
                # Find forecast for this date
                for forecast in forecast_data:
                    forecast_date = datetime.fromisoformat(forecast['date']).date()
                    if forecast_date == current_date:
                        weather_info = self._convert_to_weather_info(forecast, current_date)
                        weather_data.append(weather_info)
                        break
                
                current_date += timedelta(days=1)
        
        # For dates beyond 5 days, use historical averages or mock data
        # In a real implementation, you might use a different API for historical data
        current_date = max(start_date, today + timedelta(days=6))
        while current_date <= end_date:
            # Create mock weather data based on seasonal averages
            mock_weather = self._generate_mock_weather(location, current_date)
            weather_data.append(mock_weather)
            current_date += timedelta(days=1)
        
        return weather_data
    
    def _process_forecast_data(self, forecast_list: List[Dict], days: int) -> List[Dict[str, Any]]:
        """Process raw forecast data into daily summaries."""
        daily_data = {}
        
        for item in forecast_list[:days * 8]:  # 8 forecasts per day (3-hour intervals)
            dt_txt = item['dt_txt']
            date_str = dt_txt.split(' ')[0]
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'temps': [],
                    'conditions': [],
                    'humidity': [],
                    'wind_speed': [],
                    'precipitation': 0
                }
            
            main = item['main']
            weather = item['weather'][0]
            wind = item.get('wind', {})
            rain = item.get('rain', {})
            snow = item.get('snow', {})
            
            daily_data[date_str]['temps'].append(main['temp'])
            daily_data[date_str]['conditions'].append(weather['main'])
            daily_data[date_str]['humidity'].append(main['humidity'])
            daily_data[date_str]['wind_speed'].append(wind.get('speed', 0))
            
            # Add precipitation
            precip = rain.get('3h', 0) + snow.get('3h', 0)
            daily_data[date_str]['precipitation'] += precip
        
        # Convert to daily summaries
        daily_forecasts = []
        for date_str, data in daily_data.items():
            if len(data['temps']) > 0:
                daily_forecast = {
                    'date': date_str,
                    'temp_high': max(data['temps']),
                    'temp_low': min(data['temps']),
                    'condition': self._get_dominant_condition(data['conditions']),
                    'humidity': sum(data['humidity']) / len(data['humidity']),
                    'wind_speed': sum(data['wind_speed']) / len(data['wind_speed']),
                    'precipitation': data['precipitation']
                }
                daily_forecasts.append(daily_forecast)
        
        return daily_forecasts[:days]
    
    def _get_dominant_condition(self, conditions: List[str]) -> str:
        """Get the most common weather condition for the day."""
        condition_count = {}
        for condition in conditions:
            condition_count[condition] = condition_count.get(condition, 0) + 1
        
        return max(condition_count, key=condition_count.get)
    
    def _convert_to_weather_info(self, forecast_data: Dict[str, Any], forecast_date: date) -> WeatherInfo:
        """Convert forecast data to WeatherInfo object."""
        condition_map = {
            'Clear': WeatherCondition.SUNNY,
            'Clouds': WeatherCondition.CLOUDY,
            'Rain': WeatherCondition.RAINY,
            'Drizzle': WeatherCondition.RAINY,
            'Thunderstorm': WeatherCondition.STORMY,
            'Snow': WeatherCondition.SNOWY,
            'Mist': WeatherCondition.FOGGY,
            'Fog': WeatherCondition.FOGGY
        }
        
        condition_str = forecast_data.get('condition', 'Clear')
        condition = condition_map.get(condition_str, WeatherCondition.SUNNY)
        
        temp_high = forecast_data.get('temp_high', 20)
        temp_low = forecast_data.get('temp_low', 15)
        humidity = forecast_data.get('humidity', 50)
        wind_speed = forecast_data.get('wind_speed', 5)
        precipitation = forecast_data.get('precipitation', 0)
        
        # Determine if suitable for outdoor activities
        is_suitable = self._is_suitable_for_outdoor(condition, temp_high, temp_low, wind_speed, precipitation)
        
        return WeatherInfo(
            date=forecast_date,
            condition=condition,
            temperature_high=temp_high,
            temperature_low=temp_low,
            humidity=int(humidity),
            precipitation_chance=min(int(precipitation * 10), 100),  # Convert to percentage
            wind_speed=wind_speed,
            uv_index=self._estimate_uv_index(condition),
            is_suitable_for_outdoor=is_suitable
        )
    
    def _generate_mock_weather(self, location: str, forecast_date: date) -> WeatherInfo:
        """Generate mock weather data for dates beyond forecast range."""
        # Simple seasonal weather patterns
        month = forecast_date.month
        
        if month in [12, 1, 2]:  # Winter
            temp_high = 10
            temp_low = 0
            condition = WeatherCondition.CLOUDY
        elif month in [3, 4, 5]:  # Spring
            temp_high = 20
            temp_low = 10
            condition = WeatherCondition.SUNNY
        elif month in [6, 7, 8]:  # Summer
            temp_high = 30
            temp_low = 20
            condition = WeatherCondition.SUNNY
        else:  # Autumn
            temp_high = 18
            temp_low = 8
            condition = WeatherCondition.CLOUDY
        
        # Add some randomness based on location hash
        location_hash = hash(location) % 10
        temp_adjustment = location_hash - 5
        temp_high += temp_adjustment
        temp_low += temp_adjustment
        
        is_suitable = self._is_suitable_for_outdoor(condition, temp_high, temp_low, 5, 0)
        
        return WeatherInfo(
            date=forecast_date,
            condition=condition,
            temperature_high=temp_high,
            temperature_low=temp_low,
            humidity=60,
            precipitation_chance=20,
            wind_speed=5.0,
            uv_index=self._estimate_uv_index(condition),
            is_suitable_for_outdoor=is_suitable
        )
    
    def _is_suitable_for_outdoor(
        self,
        condition: WeatherCondition,
        temp_high: float,
        temp_low: float,
        wind_speed: float,
        precipitation: float
    ) -> bool:
        """Determine if weather is suitable for outdoor activities."""
        # Check for extreme conditions
        if condition in [WeatherCondition.STORMY, WeatherCondition.SNOWY]:
            return False
        
        if temp_high < -5 or temp_high > 40:  # Extreme temperatures
            return False
        
        if wind_speed > 25:  # Very windy
            return False
        
        if precipitation > 5:  # Heavy precipitation
            return False
        
        if condition == WeatherCondition.RAINY and precipitation > 1:
            return False
        
        return True
    
    def _estimate_uv_index(self, condition: WeatherCondition) -> int:
        """Estimate UV index based on weather condition."""
        uv_map = {
            WeatherCondition.SUNNY: 8,
            WeatherCondition.CLOUDY: 4,
            WeatherCondition.RAINY: 2,
            WeatherCondition.SNOWY: 2,
            WeatherCondition.STORMY: 1,
            WeatherCondition.FOGGY: 3
        }
        
        return uv_map.get(condition, 5)
    
    def analyze_weather_suitability(
        self,
        weather_data: List[WeatherInfo],
        activity_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Analyze weather suitability for different types of activities.
        
        Args:
            weather_data: List of weather information
            activity_type: Type of activity ("outdoor", "indoor", "general")
            
        Returns:
            Weather analysis with recommendations
        """
        analysis = {
            'total_days': len(weather_data),
            'suitable_days': 0,
            'unsuitable_days': 0,
            'recommendations': [],
            'best_days': [],
            'worst_days': []
        }
        
        for i, weather in enumerate(weather_data):
            day_score = self._calculate_day_score(weather, activity_type)
            
            if weather.is_suitable_for_outdoor:
                analysis['suitable_days'] += 1
                analysis['best_days'].append({
                    'day': i + 1,
                    'date': weather.date.isoformat(),
                    'score': day_score,
                    'condition': weather.condition.value
                })
            else:
                analysis['unsuitable_days'] += 1
                analysis['worst_days'].append({
                    'day': i + 1,
                    'date': weather.date.isoformat(),
                    'score': day_score,
                    'condition': weather.condition.value
                })
        
        # Sort best and worst days by score
        analysis['best_days'].sort(key=lambda x: x['score'], reverse=True)
        analysis['worst_days'].sort(key=lambda x: x['score'])
        
        # Generate recommendations
        if analysis['suitable_days'] > analysis['unsuitable_days']:
            analysis['recommendations'].append("Weather conditions are generally favorable for outdoor activities.")
        else:
            analysis['recommendations'].append("Consider planning more indoor activities due to weather conditions.")
        
        return analysis
    
    def _calculate_day_score(self, weather: WeatherInfo, activity_type: str) -> float:
        """Calculate a weather suitability score for a day."""
        score = 50  # Base score
        
        # Temperature score
        if 15 <= weather.temperature_high <= 28:
            score += 20
        elif 10 <= weather.temperature_high <= 35:
            score += 10
        else:
            score -= 10
        
        # Condition score
        condition_scores = {
            WeatherCondition.SUNNY: 30,
            WeatherCondition.CLOUDY: 15,
            WeatherCondition.RAINY: -20,
            WeatherCondition.SNOWY: -25,
            WeatherCondition.STORMY: -30,
            WeatherCondition.FOGGY: -5
        }
        score += condition_scores.get(weather.condition, 0)
        
        # Precipitation penalty
        if weather.precipitation_chance:
            score -= weather.precipitation_chance * 0.3
        
        # Wind penalty
        if weather.wind_speed and weather.wind_speed > 15:
            score -= (weather.wind_speed - 15) * 2
        
        return max(0, min(100, score))  # Clamp between 0 and 100