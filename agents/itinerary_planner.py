"""
Itinerary Planner Agent for the Trip Planner ADK application.

This agent creates comprehensive day-by-day itineraries by combining
POIs, weather data, and transport information.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import date, timedelta, datetime, time
from decimal import Decimal
import uuid
import math
from adk import LlmAgent
from google.cloud import aiplatform

from schemas import (
    Itinerary, DayPlan, ItineraryItem, POI, TripRequest, 
    WeatherInfo, TransportOption, AgentResponse
)
from tools import MapsApiTool

logger = logging.getLogger(__name__)


class ItineraryPlannerAgent(LlmAgent):
    """Agent for creating comprehensive trip itineraries."""
    
    def __init__(self, vertex_config: Dict[str, Any]):
        """Initialize the Itinerary Planner Agent."""
        super().__init__(
            name="itinerary_planner_agent",
            description="Creates comprehensive day-by-day trip itineraries"
        )
        self.vertex_config = vertex_config
        self.model_name = vertex_config.get("model", "gemini-1.5-pro")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=vertex_config["project_id"],
            location=vertex_config["location"]
        )
        
        logger.info("Itinerary Planner Agent initialized")
    
    def _get_destination_currency(self, destination: str) -> Tuple[str, str, float]:
        """
        Get currency info for destination.
        
        Returns:
            Tuple of (currency_code, currency_symbol, usd_to_local_rate)
        """
        # Currency mapping for major destinations
        currency_mapping = {
            # India
            "bangalore": ("INR", "₹", 83.0),
            "mumbai": ("INR", "₹", 83.0),
            "delhi": ("INR", "₹", 83.0),
            "chennai": ("INR", "₹", 83.0),
            "hyderabad": ("INR", "₹", 83.0),
            "pune": ("INR", "₹", 83.0),
            "kolkata": ("INR", "₹", 83.0),
            "india": ("INR", "₹", 83.0),
            
            # Europe
            "paris": ("EUR", "€", 0.92),
            "london": ("GBP", "£", 0.79),
            "rome": ("EUR", "€", 0.92),
            "barcelona": ("EUR", "€", 0.92),
            "amsterdam": ("EUR", "€", 0.92),
            "berlin": ("EUR", "€", 0.92),
            
            # Asia
            "tokyo": ("JPY", "¥", 149.0),
            "singapore": ("SGD", "S$", 1.35),
            "bangkok": ("THB", "฿", 36.0),
            "kuala lumpur": ("MYR", "RM", 4.7),
            "dubai": ("AED", "د.إ", 3.67),
            
            # North America
            "new york": ("USD", "$", 1.0),
            "los angeles": ("USD", "$", 1.0),
            "toronto": ("CAD", "C$", 1.36),
            "vancouver": ("CAD", "C$", 1.36),
            
            # Others
            "sydney": ("AUD", "A$", 1.52),
            "melbourne": ("AUD", "A$", 1.52),
        }
        
        destination_lower = destination.lower()
        
        # Try exact match first
        if destination_lower in currency_mapping:
            return currency_mapping[destination_lower]
        
        # Try partial matches for countries/regions
        for key, value in currency_mapping.items():
            if key in destination_lower or destination_lower in key:
                return value
        
        # Default to USD
        return ("USD", "$", 1.0)
    
    def _format_currency(self, amount: Decimal, destination: str) -> str:
        """Format currency amount based on destination."""
        currency_code, symbol, rate = self._get_destination_currency(destination)
        local_amount = float(amount) * rate
        
        if currency_code == "JPY":
            # No decimal places for JPY
            return f"{symbol}{int(local_amount)}"
        elif currency_code == "INR":
            # Indian number formatting with commas
            return f"{symbol}{local_amount:,.0f}"
        else:
            return f"{symbol}{local_amount:.2f}"
    
    def create_itinerary(
        self,
        trip_request: TripRequest,
        pois: List[POI],
        weather_data: List[WeatherInfo],
        maps_tool: Optional[MapsApiTool] = None
    ) -> AgentResponse:
        """
        Create a comprehensive itinerary for the trip.
        
        Args:
            trip_request: Trip request details
            pois: Available points of interest
            weather_data: Weather forecast for trip dates
            maps_tool: Maps API tool for transport calculations
            
        Returns:
            AgentResponse with generated itinerary
        """
        try:
            # Generate itinerary ID
            itinerary_id = str(uuid.uuid4())
            
            # Create daily plans
            daily_plans = self._create_daily_plans(
                trip_request,
                pois,
                weather_data,
                maps_tool
            )
            
            # Calculate total cost
            total_cost = self._calculate_total_cost(daily_plans)
            
            # Create itinerary object
            itinerary = Itinerary(
                id=itinerary_id,
                trip_request=trip_request,
                days=daily_plans,
                total_cost=total_cost,
                metadata={
                    "total_pois": sum(len(day.items) for day in daily_plans),
                    "weather_considered": len(weather_data) > 0,
                    "transport_optimized": maps_tool is not None
                }
            )
            
            # Generate AI-enhanced descriptions and tips
            enhanced_itinerary = self._enhance_itinerary_with_ai(itinerary)
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "itinerary": enhanced_itinerary.dict(),
                    "summary": self._create_itinerary_summary(enhanced_itinerary)
                },
                message=f"Successfully created {trip_request.duration_days}-day itinerary"
            )
            
        except Exception as e:
            logger.error(f"Error creating itinerary: {e}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def optimize_itinerary(
        self,
        itinerary: Itinerary,
        maps_tool: MapsApiTool
    ) -> AgentResponse:
        """
        Optimize an existing itinerary for travel time and efficiency.
        
        Args:
            itinerary: Existing itinerary to optimize
            maps_tool: Maps API tool for distance calculations
            
        Returns:
            AgentResponse with optimized itinerary
        """
        try:
            optimized_days = []
            
            for day_plan in itinerary.days:
                if len(day_plan.items) <= 1:
                    optimized_days.append(day_plan)
                    continue
                
                # Optimize POI order for this day
                optimized_items = self._optimize_daily_route(
                    day_plan.items,
                    maps_tool
                )
                
                # Update transport information
                updated_items = self._update_transport_info(
                    optimized_items,
                    maps_tool,
                    itinerary.trip_request.destination
                )
                
                # Create updated day plan
                optimized_day = DayPlan(
                    day=day_plan.day,
                    date=day_plan.date,
                    items=updated_items,
                    weather=day_plan.weather,
                    total_estimated_cost=self._calculate_day_cost(updated_items),
                    notes=day_plan.notes
                )
                
                optimized_days.append(optimized_day)
            
            # Create optimized itinerary
            optimized_itinerary = Itinerary(
                id=itinerary.id,
                trip_request=itinerary.trip_request,
                days=optimized_days,
                total_cost=self._calculate_total_cost(optimized_days),
                version=itinerary.version + 1,
                metadata=itinerary.metadata
            )
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "itinerary": optimized_itinerary.dict(),
                    "optimization_summary": self._create_optimization_summary(itinerary, optimized_itinerary)
                },
                message="Successfully optimized itinerary"
            )
            
        except Exception as e:
            logger.error(f"Error optimizing itinerary: {e}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def _create_daily_plans(
        self,
        trip_request: TripRequest,
        pois: List[POI],
        weather_data: List[WeatherInfo],
        maps_tool: Optional[MapsApiTool]
    ) -> List[DayPlan]:
        """Create daily plans for the trip."""
        daily_plans = []
        current_date = trip_request.start_date
        
        # Distribute POIs across days
        pois_per_day = self._distribute_pois_across_days(pois, trip_request.duration_days)
        
        for day_num in range(trip_request.duration_days):
            # Get weather for this day
            day_weather = None
            if day_num < len(weather_data):
                day_weather = weather_data[day_num]
            
            # Get POIs for this day
            day_pois = pois_per_day.get(day_num, [])
            
            # Create itinerary items for this day
            day_items = self._create_day_items(
                day_num + 1,
                day_pois,
                day_weather,
                trip_request,
                maps_tool
            )
            
            # Create day plan
            day_plan = DayPlan(
                day=day_num + 1,
                date=current_date,
                items=day_items,
                weather=day_weather,
                total_estimated_cost=self._calculate_day_cost(day_items),
                notes=self._generate_day_notes(day_weather, day_pois)
            )
            
            # Validate the daily schedule
            if not self._validate_daily_schedule(day_plan):
                logger.warning(f"Day {day_num + 1} schedule may be too packed")
            
            daily_plans.append(day_plan)
            current_date += timedelta(days=1)
        
        return daily_plans
    
    def _distribute_pois_across_days(
        self,
        pois: List[POI],
        num_days: int
    ) -> Dict[int, List[POI]]:
        """Distribute POIs across trip days based on time constraints and priority."""
        if not pois:
            return {}
        
        distributed = {}
        remaining_pois = pois.copy()
        
        # Daily time budget (8 hours = 480 minutes, leave buffer for meals and transport)
        daily_time_budget = 420  # 7 hours in minutes
        
        for day in range(num_days):
            day_pois = []
            day_time_used = 0
            
            # Reserve time for meals if not explicitly included
            meal_time_reserved = 120  # 2 hours for meals
            available_time = daily_time_budget - meal_time_reserved
            
            # Try to fill the day with POIs based on time and priority
            pois_to_remove = []
            
            for poi in remaining_pois:
                poi_duration = poi.estimated_visit_duration or self._estimate_visit_duration(poi, "couple")
                
                # Add buffer time between activities (15 minutes for travel/rest)
                buffer_time = 15 if day_pois else 0
                total_time_needed = poi_duration + buffer_time
                
                # Check if we can fit this POI
                if day_time_used + total_time_needed <= available_time:
                    day_pois.append(poi)
                    day_time_used += total_time_needed
                    pois_to_remove.append(poi)
                    
                    # Don't overfill the day - aim for 4-6 activities max
                    if len(day_pois) >= 6:
                        break
            
            # Remove scheduled POIs from remaining list
            for poi in pois_to_remove:
                remaining_pois.remove(poi)
            
            distributed[day] = day_pois
        
        # If there are still remaining POIs, try to fit them in existing days
        for poi in remaining_pois:
            for day in range(num_days):
                if len(distributed[day]) < 4:  # Only add to days with fewer activities
                    distributed[day].append(poi)
                    break
        
        return distributed
    
    def _create_day_items(
        self,
        day_num: int,
        day_pois: List[POI],
        weather: Optional[WeatherInfo],
        trip_request: TripRequest,
        maps_tool: Optional[MapsApiTool]
    ) -> List[ItineraryItem]:
        """Create itinerary items for a single day with intelligent timing based on place characteristics."""
        items = []
        
        if not day_pois:
            return items
        
        # Get optimal timing for each POI
        poi_timings = []
        current_date = trip_request.start_date + timedelta(days=day_num - 1)
        
        for poi in day_pois:
            time_category, optimal_start_minutes, reasoning = self._get_optimal_visit_time(poi, weather, current_date)
            duration = poi.estimated_visit_duration or self._estimate_visit_duration(poi, trip_request.group_type)
            
            poi_timings.append({
                'poi': poi,
                'time_category': time_category,
                'optimal_start_minutes': optimal_start_minutes,
                'duration': duration,
                'reasoning': reasoning
            })
        
        # Sort POIs by optimal timing to create natural flow
        poi_timings.sort(key=lambda x: x['optimal_start_minutes'])
        
        # Schedule activities with intelligent timing
        current_time = None
        lunch_break_added = False
        
        for i, poi_timing in enumerate(poi_timings):
            poi = poi_timing['poi']
            duration = poi_timing['duration']
            optimal_start = poi_timing['optimal_start_minutes']
            time_category = poi_timing['time_category']
            reasoning = poi_timing['reasoning']
            
            # Determine actual start time
            if current_time is None:
                # First activity - use optimal time
                start_time = optimal_start
            else:
                # Subsequent activities - consider both optimal time and logical flow
                min_start_after_previous = current_time + 15  # 15 min buffer
                
                # If optimal time is much later, use it (e.g., sunset viewing)
                if optimal_start > min_start_after_previous + 120:  # 2+ hours gap
                    start_time = optimal_start
                    # Add a break note if there's a big gap
                    if optimal_start > current_time + 180:  # 3+ hours gap
                        reasoning += f" | Break time: {self._minutes_to_time_string(current_time)} - {self._minutes_to_time_string(optimal_start)}"
                else:
                    # Use the later of optimal time or after previous activity
                    start_time = max(optimal_start, min_start_after_previous)
            
            # Add lunch break if needed (around lunch time and no lunch break yet)
            if (start_time >= 12 * 60 and not lunch_break_added and 
                poi.category.value != "restaurant" and current_time is not None and 
                current_time < 12 * 60):
                
                lunch_start = max(current_time + 15, 12 * 60)  # 12:00 PM
                start_time = max(start_time, lunch_start + 60)  # After 1-hour lunch
                lunch_break_added = True
                reasoning += " | Lunch break: 12:00-13:00"
            
            # Calculate end time
            end_time = start_time + duration
            
            # Create time slot string with category info
            time_slot = f"{self._minutes_to_time_string(start_time)} - {self._minutes_to_time_string(end_time)} ({duration} min)"
            if time_category in ["SUNRISE", "SUNSET"]:
                time_slot += f" [{time_category}]"
            
            # Calculate transport to next POI
            transport_to_next = None
            travel_time = 0
            if i < len(poi_timings) - 1 and maps_tool:
                next_poi = poi_timings[i + 1]['poi']
                transport_to_next = self._calculate_transport(poi, next_poi, maps_tool, trip_request.destination)
                travel_time = transport_to_next.duration_minutes if transport_to_next else 15
            
            # Estimate cost
            cost_estimate = self._estimate_poi_cost(poi, trip_request)
            
            # Generate enhanced notes with timing reasoning
            notes = self._generate_enhanced_item_notes(poi, weather, duration, reasoning, time_category)
            
            item = ItineraryItem(
                day=day_num,
                time_slot=time_slot,
                poi=poi,
                estimated_duration=duration,
                transport_to_next=transport_to_next,
                cost_estimate=cost_estimate,
                notes=notes
            )
            
            items.append(item)
            
            # Update current time for next activity
            current_time = end_time + travel_time
            
            # Don't schedule past 11 PM for most activities (except nightlife)
            if current_time > 23 * 60 and poi.category.value != "nightlife":
                break
        
        return items
    
    def _minutes_to_time_string(self, minutes: int) -> str:
        """Convert minutes from midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _calculate_sunrise_sunset(self, poi: POI, date_obj: date) -> Tuple[int, int]:
        """Calculate sunrise and sunset times in minutes from midnight for a given location and date."""
        try:
            # Simplified sunrise/sunset calculation (for production, use a proper library like astral)
            lat = math.radians(poi.coordinates.latitude)
            
            # Day of year
            day_of_year = date_obj.timetuple().tm_yday
            
            # Solar declination
            declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
            declination = math.radians(declination)
            
            # Hour angle
            hour_angle = math.acos(-math.tan(lat) * math.tan(declination))
            hour_angle = math.degrees(hour_angle)
            
            # Sunrise and sunset in decimal hours
            sunrise_decimal = 12 - hour_angle / 15
            sunset_decimal = 12 + hour_angle / 15
            
            # Convert to minutes from midnight
            sunrise_minutes = int(sunrise_decimal * 60)
            sunset_minutes = int(sunset_decimal * 60)
            
            # Clamp to reasonable ranges
            sunrise_minutes = max(300, min(sunrise_minutes, 420))  # Between 5:00 and 7:00 AM
            sunset_minutes = max(1020, min(sunset_minutes, 1200))  # Between 5:00 and 8:00 PM
            
            return sunrise_minutes, sunset_minutes
            
        except Exception as e:
            logger.warning(f"Could not calculate sunrise/sunset: {e}")
            # Default sunrise at 6:30 AM, sunset at 6:30 PM
            return 390, 1110
    
    def _get_optimal_visit_time(self, poi: POI, weather: Optional[WeatherInfo], date_obj: date) -> Tuple[str, int, str]:
        """
        Use AI to determine optimal visit time for a POI based on its characteristics and weather.
        
        Returns:
            Tuple of (time_category, preferred_start_minutes, reasoning)
        """
        try:
            sunrise_minutes, sunset_minutes = self._calculate_sunrise_sunset(poi, date_obj)
            
            # Create AI prompt for optimal timing
            timing_prompt = f"""
Analyze the optimal visit time for this place:

Place: {poi.name}
Category: {poi.category.value}
Rating: {poi.rating or 'N/A'}
Description: {poi.description or 'N/A'}
Weather: {weather.condition.value if weather else 'Unknown'} 
Temperature High: {weather.temperature_high if weather else 'Unknown'}°C
Sunrise: {self._minutes_to_time_string(sunrise_minutes)}
Sunset: {self._minutes_to_time_string(sunset_minutes)}

Consider these factors:
1. Place type and typical operating hours
2. Weather conditions and temperature
3. Sunrise/sunset times for photography opportunities
4. Crowd patterns and best experience timing
5. Cultural/religious considerations

Respond with ONLY this format:
TIME_CATEGORY: [SUNRISE/EARLY_MORNING/MORNING/AFTERNOON/SUNSET/EVENING/NIGHT]
START_TIME: [HH:MM in 24-hour format]
REASONING: [Brief explanation in 1-2 sentences]

Examples:
- Beach viewpoints: SUNRISE, 05:30, Best for sunrise photography and cooler temperatures
- Temples: EARLY_MORNING, 06:00, Peaceful atmosphere for prayers and fewer crowds
- Museums: MORNING, 10:00, Optimal lighting and moderate crowds
- Markets: EVENING, 17:30, Best atmosphere and cooler temperatures
- Restaurants: EVENING, 19:00, Typical dinner time with good ambiance
"""
            
            ai_response = self._call_vertex_ai(timing_prompt)
            
            if ai_response:
                return self._parse_timing_response(ai_response, sunrise_minutes, sunset_minutes)
            else:
                # Fallback to rule-based timing
                return self._get_rule_based_timing(poi, weather, sunrise_minutes, sunset_minutes)
                
        except Exception as e:
            logger.error(f"Error determining optimal visit time: {e}")
            return self._get_rule_based_timing(poi, weather, 390, 1110)
    
    def _parse_timing_response(self, response: str, sunrise_minutes: int, sunset_minutes: int) -> Tuple[str, int, str]:
        """Parse AI response for optimal timing."""
        try:
            lines = response.strip().split('\n')
            time_category = ""
            start_time = ""
            reasoning = ""
            
            for line in lines:
                if line.startswith("TIME_CATEGORY:"):
                    time_category = line.split(":", 1)[1].strip()
                elif line.startswith("START_TIME:"):
                    start_time = line.split(":", 1)[1].strip()
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
            
            # Convert start_time to minutes
            if start_time and ":" in start_time:
                hours, minutes = map(int, start_time.split(":"))
                start_minutes = hours * 60 + minutes
            else:
                # Fallback based on category
                category_times = {
                    "SUNRISE": sunrise_minutes - 30,
                    "EARLY_MORNING": 360,  # 6:00 AM
                    "MORNING": 540,        # 9:00 AM
                    "AFTERNOON": 780,      # 1:00 PM
                    "SUNSET": sunset_minutes - 60,
                    "EVENING": 1080,       # 6:00 PM
                    "NIGHT": 1200          # 8:00 PM
                }
                start_minutes = category_times.get(time_category, 540)
            
            return time_category, start_minutes, reasoning
            
        except Exception as e:
            logger.warning(f"Could not parse timing response: {e}")
            return "MORNING", 540, "Default morning timing"
    
    def _get_rule_based_timing(self, poi: POI, weather: Optional[WeatherInfo], sunrise_minutes: int, sunset_minutes: int) -> Tuple[str, int, str]:
        """Fallback rule-based timing when AI is not available."""
        category = poi.category.value
        
        # Rule-based timing decisions
        if category in ["beach", "park"] and poi.name.lower().find("sunrise") != -1:
            return "SUNRISE", sunrise_minutes - 30, "Best for sunrise viewing"
        elif category in ["beach", "park"] and poi.name.lower().find("sunset") != -1:
            return "SUNSET", sunset_minutes - 60, "Perfect for sunset viewing"
        elif category == "religious":
            return "EARLY_MORNING", 360, "Peaceful morning prayers"
        elif category == "museum":
            return "MORNING", 600, "Avoid afternoon crowds"
        elif category == "restaurant":
            if "breakfast" in poi.name.lower():
                return "EARLY_MORNING", 480, "Breakfast time"
            elif "lunch" in poi.name.lower():
                return "AFTERNOON", 720, "Lunch time"
            else:
                return "EVENING", 1140, "Dinner time"
        elif category == "nightlife":
            return "NIGHT", 1260, "Evening entertainment"
        elif category in ["shopping", "market"]:
            # Consider weather for market timing
            if weather and weather.temperature_high and weather.temperature_high > 30:
                return "EVENING", 1020, "Cooler evening shopping"
            else:
                return "AFTERNOON", 840, "Good shopping hours"
        elif category in ["adventure", "amusement_park"]:
            return "MORNING", 540, "Full day adventure"
        else:
            return "MORNING", 540, "Standard morning visit"
    
    def _generate_enhanced_item_notes(self, poi: POI, weather: Optional[WeatherInfo], duration: int, timing_reasoning: str = "", time_category: str = "") -> str:
        """Generate enhanced notes for itinerary items with timing intelligence."""
        notes = []
        
        # Add POI description if available
        if poi.description:
            notes.append(poi.description)
        
        # Add timing reasoning from AI
        if timing_reasoning:
            notes.append(f"🕘 {timing_reasoning}")
        
        # Add special timing alerts
        if time_category == "SUNRISE":
            notes.append("🌅 Early morning activity - dress warmly and bring camera")
        elif time_category == "SUNSET":
            notes.append("🌇 Perfect for sunset photography and romantic atmosphere")
        elif time_category == "NIGHT":
            notes.append("🌙 Evening activity - check safety and transportation")
        
        # Add duration note
        duration_hours = duration // 60
        duration_mins = duration % 60
        if duration_hours > 0:
            if duration_mins > 0:
                notes.append(f"⏱️ Estimated visit time: {duration_hours}h {duration_mins}m")
            else:
                notes.append(f"⏱️ Estimated visit time: {duration_hours}h")
        else:
            notes.append(f"⏱️ Estimated visit time: {duration_mins}m")
        
        # Add weather-related notes with more intelligence
        if weather and poi.category.value in ["park", "beach", "attraction", "adventure"]:
            if weather.condition and "rain" in weather.condition.lower():
                notes.append("☔ Weather alert - indoor backup recommended")
            elif weather.temperature_high:
                if weather.temperature_high > 35:
                    notes.append("🔥 Very hot - early morning or evening visit recommended")
                elif weather.temperature_high > 30:
                    notes.append("🌞 Hot weather - bring water and sun protection")
                elif weather.temperature_high < 10:
                    notes.append("🧥 Cold weather - dress warmly")
                elif weather.temperature_high < 15:
                    notes.append("🧥 Cool weather - light jacket recommended")
        
        # Add rating info if available
        if poi.rating and poi.rating >= 4.5:
            notes.append(f"⭐ Exceptional ({poi.rating}/5)")
        elif poi.rating and poi.rating >= 4.0:
            notes.append(f"⭐ Highly rated ({poi.rating}/5)")
        
        # Add category-specific tips
        if poi.category.value == "religious":
            notes.append("🙏 Dress modestly and respect local customs")
        elif poi.category.value == "museum":
            notes.append("🎫 Consider booking tickets in advance")
        elif poi.category.value == "restaurant":
            notes.append("🍽️ Check for reservations if upscale dining")
        elif poi.category.value == "beach":
            notes.append("🏖️ Bring sunscreen, water, and beach essentials")
        elif poi.category.value == "adventure":
            notes.append("👟 Wear appropriate clothing and footwear")
        
        # Add opening hours reminder if available
        if poi.opening_hours:
            notes.append("💡 Verify opening hours before visiting")
        
        return " | ".join(notes)
    
    def _estimate_visit_duration(self, poi: POI, group_type: str) -> int:
        """Estimate visit duration for a POI."""
        if poi.estimated_visit_duration:
            return poi.estimated_visit_duration
        
        # Default durations by category (in minutes)
        base_durations = {
            "restaurant": 90,
            "attraction": 120,
            "museum": 150,
            "park": 90,
            "shopping": 120,
            "nightlife": 180,
            "accommodation": 30,
            "transport": 15,
            "entertainment": 180,
            "religious": 60,
            "beach": 180,
            "adventure": 240,
            "tourist_attraction": 120,
            "amusement_park": 240,
            "zoo": 180,
            "aquarium": 150
        }
        
        base_duration = base_durations.get(poi.category.value, 120)
        
        # Adjust for group type
        group_multipliers = {
            "family": 1.3,  # Families take longer
            "couple": 1.0,
            "solo": 0.8,    # Solo travelers move faster
            "friends": 1.1,
            "business": 0.9
        }
        
        duration = base_duration * group_multipliers.get(group_type, 1.0)
        
        # Adjust for rating (higher rated places deserve more time)
        if poi.rating:
            if poi.rating >= 4.5:
                duration *= 1.2
            elif poi.rating >= 4.0:
                duration *= 1.1
            elif poi.rating < 3.0:
                duration *= 0.8
        
            return int(duration)
    
    def _validate_daily_schedule(self, day_plan: DayPlan) -> bool:
        """Validate that a daily schedule is reasonable and not overpacked."""
        if not day_plan.items:
            return True
        
        total_duration = sum(item.estimated_duration for item in day_plan.items)
        
        # Check if total time exceeds reasonable daily limit (7-8 hours)
        if total_duration > 480:  # 8 hours
            logger.warning(f"Day {day_plan.day} schedule exceeds 8 hours ({total_duration} minutes)")
            return False
        
        # Check if too many activities (more than 6 is usually too hectic)
        if len(day_plan.items) > 6:
            logger.warning(f"Day {day_plan.day} has too many activities ({len(day_plan.items)})")
            return False
        
        return True        # Adjust for group type
        if group_type == "family":
            base_duration = int(base_duration * 1.2)  # Families take longer
        elif group_type == "solo":
            base_duration = int(base_duration * 0.8)  # Solo travelers move faster
        
        return base_duration
    
    def _calculate_transport(
        self,
        from_poi: POI,
        to_poi: POI,
        maps_tool: MapsApiTool,
        destination: str = "unknown"
    ) -> Optional[TransportOption]:
        """Calculate transport between two POIs with multiple options."""
        try:
            # Get directions between POIs
            from_location = f"{from_poi.coordinates.latitude},{from_poi.coordinates.longitude}"
            to_location = f"{to_poi.coordinates.latitude},{to_poi.coordinates.longitude}"
            
            directions = maps_tool.get_directions(from_location, to_location, mode="walking")
            
            if directions and directions[0].get("legs"):
                leg = directions[0]["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                walking_duration = leg["duration"]["value"] // 60
                
                # Calculate costs for different transport modes
                base_taxi_rate = 0.5  # USD per km
                base_public_rate = 0.3  # USD per km
                
                taxi_cost = max(2.0, distance_km * base_taxi_rate)  # Minimum fare
                public_cost = max(0.5, distance_km * base_public_rate)
                
                # Return walking as primary option with additional info
                transport_option = TransportOption(
                    mode="walking",
                    duration_minutes=walking_duration,
                    distance_km=distance_km,
                    cost=Decimal("0"),  # Walking is free
                    route_description=leg.get("summary", "")
                )
                
                # Add transport alternatives as description
                alternatives = []
                
                if distance_km <= 3.0:  # Show walking for reasonable distances
                    alternatives.append(f"🚶 Walking: {walking_duration} min, Free")
                
                driving_time = max(5, int((distance_km / 25.0) * 60))  # Urban speed
                alternatives.append(f"🚗 Taxi: {driving_time} min, {self._format_currency(Decimal(str(taxi_cost)), destination)}")
                
                if distance_km > 0.5:  # Public transport for longer distances
                    public_time = int((distance_km / 15.0) * 60) + 5  # Add wait time
                    alternatives.append(f"🚌 Public: {public_time} min, {self._format_currency(Decimal(str(public_cost)), destination)}")
                
                if distance_km > 2.0:  # Ride-sharing for longer distances
                    rideshare_cost = taxi_cost * 0.8
                    alternatives.append(f"📱 Uber/Ola: {driving_time + 3} min, {self._format_currency(Decimal(str(rideshare_cost)), destination)}")
                
                transport_option.route_description = f"{leg.get('summary', '')} | Options: {' | '.join(alternatives)}"
                
                return transport_option
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not calculate transport: {e}")
            return None
    
    def _estimate_poi_cost(self, poi: POI, trip_request: TripRequest) -> Decimal:
        """Estimate cost for visiting a POI."""
        # Base cost estimates by category and price level
        base_costs = {
            "restaurant": [15, 30, 50, 80],  # By price level 1-4
            "attraction": [10, 20, 35, 60],
            "museum": [8, 15, 25, 40],
            "park": [0, 5, 10, 20],
            "shopping": [20, 50, 100, 200],
            "nightlife": [15, 30, 60, 100],
            "accommodation": [50, 100, 200, 400],
            "transport": [2, 5, 15, 30],
            "entertainment": [10, 25, 45, 80],
            "religious": [0, 5, 10, 20],
            "beach": [0, 10, 20, 40],
            "adventure": [20, 40, 80, 150]
        }
        
        category_costs = base_costs.get(poi.category.value, [10, 20, 35, 60])
        price_level = poi.price_level or 2
        cost_index = min(price_level - 1, len(category_costs) - 1)
        
        base_cost = category_costs[cost_index]
        
        # Adjust for number of travelers
        if poi.category.value in ["restaurant", "entertainment", "accommodation"]:
            total_cost = Decimal(str(base_cost * trip_request.number_of_travelers))
        else:
            total_cost = Decimal(str(base_cost))
        
        return total_cost
    
    def _generate_day_notes(
        self,
        weather: Optional[WeatherInfo],
        pois: List[POI]
    ) -> Optional[str]:
        """Generate notes for a day plan."""
        notes = []
        
        if weather:
            if not weather.is_suitable_for_outdoor:
                notes.append(f"Weather alert: {weather.condition.value} conditions expected")
            
            if weather.precipitation_chance and weather.precipitation_chance > 50:
                notes.append("Bring umbrella or rain protection")
        
        # Add category-specific notes
        categories = [poi.category.value for poi in pois]
        if "restaurant" in categories:
            notes.append("Consider making dinner reservations")
        
        return "; ".join(notes) if notes else None
    
    def _generate_item_notes(
        self,
        poi: POI,
        weather: Optional[WeatherInfo]
    ) -> Optional[str]:
        """Generate notes for an itinerary item."""
        notes = []
        
        if poi.opening_hours:
            notes.append("Check opening hours before visiting")
        
        if poi.website:
            notes.append("Visit website for tickets/reservations")
        
        if weather and poi.category.value in ["park", "beach", "adventure"]:
            if not weather.is_suitable_for_outdoor:
                notes.append("Weather may affect this outdoor activity")
        
        return "; ".join(notes) if notes else None
    
    def _calculate_day_cost(self, items: List[ItineraryItem]) -> Decimal:
        """Calculate total cost for a day."""
        return sum(item.cost_estimate or Decimal("0") for item in items)
    
    def _calculate_total_cost(self, daily_plans: List[DayPlan]) -> Decimal:
        """Calculate total trip cost."""
        return sum(day.total_estimated_cost for day in daily_plans)
    
    def _optimize_daily_route(
        self,
        items: List[ItineraryItem],
        maps_tool: MapsApiTool
    ) -> List[ItineraryItem]:
        """Optimize the order of POIs for a day to minimize travel time."""
        if len(items) <= 2:
            return items
        
        try:
            # Extract POI coordinates
            pois = [item.poi for item in items]
            coordinates = [(poi.coordinates.latitude, poi.coordinates.longitude) for poi in pois]
            
            # Simple nearest neighbor optimization
            optimized_order = self._nearest_neighbor_tsp(coordinates)
            
            # Reorder items based on optimization
            optimized_items = [items[i] for i in optimized_order]
            
            return optimized_items
            
        except Exception as e:
            logger.warning(f"Could not optimize route: {e}")
            return items
    
    def _nearest_neighbor_tsp(self, coordinates: List[tuple]) -> List[int]:
        """Simple nearest neighbor algorithm for route optimization."""
        if len(coordinates) <= 1:
            return list(range(len(coordinates)))
        
        unvisited = set(range(len(coordinates)))
        current = 0  # Start with first POI
        route = [current]
        unvisited.remove(current)
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: self._distance(coordinates[current], coordinates[x]))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    def _distance(self, coord1: tuple, coord2: tuple) -> float:
        """Calculate approximate distance between two coordinates."""
        import math
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Haversine formula for great circle distance
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def _update_transport_info(
        self,
        items: List[ItineraryItem],
        maps_tool: MapsApiTool,
        destination: str
    ) -> List[ItineraryItem]:
        """Update transport information between optimized POIs."""
        updated_items = []
        
        for i, item in enumerate(items):
            updated_item = item.copy()
            
            # Calculate transport to next POI
            if i < len(items) - 1:
                next_poi = items[i + 1].poi
                transport = self._calculate_transport(item.poi, next_poi, maps_tool, destination)
                updated_item.transport_to_next = transport
            else:
                updated_item.transport_to_next = None
            
            updated_items.append(updated_item)
        
        return updated_items
    
    def _enhance_itinerary_with_ai(self, itinerary: Itinerary) -> Itinerary:
        """Enhance itinerary with AI-generated descriptions and tips."""
        try:
            # Create prompt for AI enhancement
            prompt = self._create_enhancement_prompt(itinerary)
            
            # Call Vertex AI
            response = self._call_vertex_ai(prompt)
            
            if response:
                enhancements = self._parse_enhancement_response(response)
                return self._apply_enhancements(itinerary, enhancements)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error enhancing itinerary with AI: {e}")
            return itinerary
    
    def _create_enhancement_prompt(self, itinerary: Itinerary) -> str:
        """Create prompt for AI enhancement."""
        itinerary_summary = f"Destination: {itinerary.trip_request.destination}\n"
        itinerary_summary += f"Duration: {len(itinerary.days)} days\n"
        itinerary_summary += f"Group: {itinerary.trip_request.group_type.value}\n\n"
        
        for day in itinerary.days:
            itinerary_summary += f"Day {day.day}:\n"
            for item in day.items:
                itinerary_summary += f"- {item.poi.name} ({item.poi.category.value})\n"
            itinerary_summary += "\n"
        
        prompt = f"""
Enhance this travel itinerary with helpful tips and descriptions:

{itinerary_summary}

Provide enhancements in JSON format:
{{
    "overall_tips": ["general tips for this destination"],
    "daily_enhancements": {{
        "1": {{"description": "day description", "tips": ["day-specific tips"]}},
        "2": {{"description": "day description", "tips": ["day-specific tips"]}}
    }}
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
    
    def _parse_enhancement_response(self, response: str) -> Dict[str, Any]:
        """Parse AI enhancement response."""
        try:
            import json
            
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error parsing enhancement response: {e}")
            return {}
    
    def _apply_enhancements(self, itinerary: Itinerary, enhancements: Dict[str, Any]) -> Itinerary:
        """Apply AI enhancements to itinerary."""
        enhanced_metadata = itinerary.metadata.copy()
        
        if "overall_tips" in enhancements:
            enhanced_metadata["ai_tips"] = enhancements["overall_tips"]
        
        enhanced_days = []
        for day in itinerary.days:
            day_key = str(day.day)
            enhanced_notes = day.notes or ""
            
            if "daily_enhancements" in enhancements and day_key in enhancements["daily_enhancements"]:
                day_enhancement = enhancements["daily_enhancements"][day_key]
                
                if "description" in day_enhancement:
                    enhanced_notes += f" {day_enhancement['description']}"
                
                if "tips" in day_enhancement:
                    enhanced_notes += f" Tips: {'; '.join(day_enhancement['tips'])}"
            
            enhanced_day = DayPlan(
                day=day.day,
                date=day.date,
                items=day.items,
                weather=day.weather,
                total_estimated_cost=day.total_estimated_cost,
                notes=enhanced_notes.strip() or None
            )
            
            enhanced_days.append(enhanced_day)
        
        return Itinerary(
            id=itinerary.id,
            trip_request=itinerary.trip_request,
            days=enhanced_days,
            total_cost=itinerary.total_cost,
            created_at=itinerary.created_at,
            updated_at=itinerary.updated_at,
            version=itinerary.version,
            metadata=enhanced_metadata
        )
    
    def _create_itinerary_summary(self, itinerary: Itinerary) -> Dict[str, Any]:
        """Create a comprehensive summary of the itinerary."""
        total_activities = sum(len(day.items) for day in itinerary.days)
        destination = itinerary.trip_request.destination
        
        # Calculate total estimated time
        total_time_minutes = 0
        for day in itinerary.days:
            for item in day.items:
                total_time_minutes += item.estimated_duration
        
        total_hours = total_time_minutes // 60
        
        summary = {
            "destination": destination,
            "duration_days": len(itinerary.days),
            "total_cost": self._format_currency(itinerary.total_cost, destination),
            "total_activities": total_activities,
            "total_estimated_time": f"{total_hours}h {total_time_minutes % 60}m",
            "average_activities_per_day": round(total_activities / len(itinerary.days), 1),
            "daily_breakdown": []
        }
        
        for day in itinerary.days:
            # Calculate day's total time
            day_time_minutes = sum(item.estimated_duration for item in day.items)
            day_hours = day_time_minutes // 60
            
            # Get time range for the day
            if day.items:
                first_time = day.items[0].time_slot.split(' - ')[0]
                last_item = day.items[-1]
                last_time_parts = last_item.time_slot.split(' - ')
                if len(last_time_parts) > 1:
                    last_time = last_time_parts[1].split(' (')[0]  # Remove duration part
                else:
                    last_time = "Evening"
                time_range = f"{first_time} - {last_time}"
            else:
                time_range = "No activities scheduled"
            
            day_summary = {
                "day": day.day,
                "date": day.date.isoformat(),
                "activities": len(day.items),
                "estimated_cost": self._format_currency(day.total_estimated_cost, destination),
                "total_time": f"{day_hours}h {day_time_minutes % 60}m",
                "time_range": time_range,
                "weather": day.weather.condition.value if day.weather and hasattr(day.weather.condition, 'value') else (day.weather.condition if day.weather else None),
                "activity_preview": [item.poi.name for item in day.items]  # Show all activities
            }
            
            summary["daily_breakdown"].append(day_summary)
        
        return summary
    
    def _create_optimization_summary(
        self,
        original: Itinerary,
        optimized: Itinerary
    ) -> Dict[str, Any]:
        """Create summary of optimization changes."""
        return {
            "original_cost": float(original.total_cost),
            "optimized_cost": float(optimized.total_cost),
            "cost_difference": float(optimized.total_cost - original.total_cost),
            "route_optimized": True,
            "version_change": f"{original.version} -> {optimized.version}"
        }