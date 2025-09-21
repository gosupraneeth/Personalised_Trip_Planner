"""
Itinerary Planner Agent for the Trip Planner ADK application.

This agent creates comprehensive day-by-day itineraries by combining
POIs, weather data, and transport information.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from decimal import Decimal
import uuid
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
                    maps_tool
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
            
            daily_plans.append(day_plan)
            current_date += timedelta(days=1)
        
        return daily_plans
    
    def _distribute_pois_across_days(
        self,
        pois: List[POI],
        num_days: int
    ) -> Dict[int, List[POI]]:
        """Distribute POIs across trip days."""
        if not pois:
            return {}
        
        # Calculate POIs per day
        pois_per_day = max(2, len(pois) // num_days)
        
        distributed = {}
        poi_index = 0
        
        for day in range(num_days):
            day_pois = []
            
            # Add POIs for this day
            for _ in range(pois_per_day):
                if poi_index < len(pois):
                    day_pois.append(pois[poi_index])
                    poi_index += 1
            
            # Distribute remaining POIs
            if day == num_days - 1:  # Last day
                while poi_index < len(pois):
                    day_pois.append(pois[poi_index])
                    poi_index += 1
            
            distributed[day] = day_pois
        
        return distributed
    
    def _create_day_items(
        self,
        day_num: int,
        day_pois: List[POI],
        weather: Optional[WeatherInfo],
        trip_request: TripRequest,
        maps_tool: Optional[MapsApiTool]
    ) -> List[ItineraryItem]:
        """Create itinerary items for a single day."""
        items = []
        
        if not day_pois:
            return items
        
        # Define time slots for the day
        time_slots = self._generate_time_slots(len(day_pois))
        
        for i, poi in enumerate(day_pois):
            # Estimate visit duration
            duration = self._estimate_visit_duration(poi, trip_request.group_type)
            
            # Calculate transport to next POI
            transport_to_next = None
            if i < len(day_pois) - 1 and maps_tool:
                next_poi = day_pois[i + 1]
                transport_to_next = self._calculate_transport(poi, next_poi, maps_tool)
            
            # Estimate cost
            cost_estimate = self._estimate_poi_cost(poi, trip_request)
            
            item = ItineraryItem(
                day=day_num,
                time_slot=time_slots[i] if i < len(time_slots) else "flexible",
                poi=poi,
                estimated_duration=duration,
                transport_to_next=transport_to_next,
                cost_estimate=cost_estimate,
                notes=self._generate_item_notes(poi, weather)
            )
            
            items.append(item)
        
        return items
    
    def _generate_time_slots(self, num_items: int) -> List[str]:
        """Generate time slots for daily activities."""
        if num_items <= 2:
            return ["09:00-12:00", "14:00-17:00"]
        elif num_items == 3:
            return ["09:00-11:30", "12:30-15:00", "15:30-18:00"]
        elif num_items == 4:
            return ["09:00-11:00", "11:30-13:30", "14:30-16:30", "17:00-19:00"]
        else:
            # For more items, distribute evenly
            slots = []
            start_hour = 9
            slot_duration = min(3, 10 // num_items)  # Max 3 hours per slot
            
            for i in range(num_items):
                start = start_hour + (i * slot_duration)
                end = start + slot_duration
                if end > 19:  # Don't go past 7 PM
                    end = 19
                slots.append(f"{start:02d}:00-{end:02d}:00")
            
            return slots
    
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
            "adventure": 240
        }
        
        base_duration = base_durations.get(poi.category.value, 120)
        
        # Adjust for group type
        if group_type == "family":
            base_duration = int(base_duration * 1.2)  # Families take longer
        elif group_type == "solo":
            base_duration = int(base_duration * 0.8)  # Solo travelers move faster
        
        return base_duration
    
    def _calculate_transport(
        self,
        from_poi: POI,
        to_poi: POI,
        maps_tool: MapsApiTool
    ) -> Optional[TransportOption]:
        """Calculate transport between two POIs."""
        try:
            # Get directions between POIs
            from_location = f"{from_poi.coordinates.latitude},{from_poi.coordinates.longitude}"
            to_location = f"{to_poi.coordinates.latitude},{to_poi.coordinates.longitude}"
            
            directions = maps_tool.get_directions(from_location, to_location, mode="walking")
            
            if directions and directions[0].get("legs"):
                leg = directions[0]["legs"][0]
                
                return TransportOption(
                    mode="walking",
                    duration_minutes=leg["duration"]["value"] // 60,
                    distance_km=leg["distance"]["value"] / 1000,
                    cost=Decimal("0"),  # Walking is free
                    route_description=leg.get("summary", "")
                )
            
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
        maps_tool: MapsApiTool
    ) -> List[ItineraryItem]:
        """Update transport information between optimized POIs."""
        updated_items = []
        
        for i, item in enumerate(items):
            updated_item = item.copy()
            
            # Calculate transport to next POI
            if i < len(items) - 1:
                next_poi = items[i + 1].poi
                transport = self._calculate_transport(item.poi, next_poi, maps_tool)
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
        """Create a summary of the itinerary."""
        summary = {
            "destination": itinerary.trip_request.destination,
            "duration_days": len(itinerary.days),
            "total_cost": float(itinerary.total_cost),
            "total_activities": sum(len(day.items) for day in itinerary.days),
            "daily_breakdown": []
        }
        
        for day in itinerary.days:
            day_summary = {
                "day": day.day,
                "date": day.date.isoformat(),
                "activities": len(day.items),
                "estimated_cost": float(day.total_estimated_cost),
                "weather": day.weather.condition.value if day.weather else None
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