"""
Place Finder Agent for the Trip Planner ADK application.

This agent discovers and retrieves points of interest (POIs) for a given destination
using Google Maps API and cached data from BigQuery.
"""

import logging
from typing import Dict, Any, Optional, List
from adk import LlmAgent
from google.cloud import aiplatform

from schemas import POI, POICategory, TripRequest, AgentResponse, Coordinates, Address
from tools import MapsApiTool, BigQueryTool

logger = logging.getLogger(__name__)


class PlaceFinderAgent(LlmAgent):
    """Agent for discovering and retrieving points of interest."""
    
    def __init__(self, vertex_config: Dict[str, Any]):
        """Initialize the Place Finder Agent."""
        super().__init__(
            name="place_finder_agent",
            description="Discovers and retrieves points of interest for trip destinations"
        )
        self.vertex_config = vertex_config
        self.model_name = vertex_config.get("model", "gemini-1.5-pro")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=vertex_config["project_id"],
            location=vertex_config["location"]
        )
        
        logger.info("Place Finder Agent initialized")
    
    def find_places(
        self,
        trip_request: TripRequest,
        maps_tool: MapsApiTool,
        bigquery_tool: BigQueryTool,
        radius: int = 10000,
        max_places: int = 50
    ) -> AgentResponse:
        """
        Find places of interest for a trip destination.
        
        Args:
            trip_request: Trip request details
            maps_tool: Google Maps API tool
            bigquery_tool: BigQuery caching tool
            radius: Search radius in meters
            max_places: Maximum number of places to return
            
        Returns:
            AgentResponse with found places
        """
        try:
            # First, try to get cached places
            cached_places = self._get_cached_places(
                bigquery_tool,
                trip_request.destination,
                radius / 1000,  # Convert to km
                trip_request.special_interests
            )
            
            if cached_places and len(cached_places) >= max_places // 2:
                logger.info(f"Found {len(cached_places)} cached places for {trip_request.destination}")
                pois = [self._convert_cached_to_poi(place) for place in cached_places[:max_places]]
            else:
                # Search for new places using Maps API
                pois = self._search_new_places(
                    maps_tool,
                    bigquery_tool,
                    trip_request,
                    radius,
                    max_places
                )
            
            # Filter and rank places based on trip requirements
            filtered_pois = self._filter_places_for_trip(pois, trip_request)
            
            # Use AI to enhance place recommendations
            enhanced_pois = self._enhance_recommendations(filtered_pois, trip_request)
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "places": [poi.dict() for poi in enhanced_pois],
                    "total_found": len(enhanced_pois),
                    "search_radius": radius,
                    "destination": trip_request.destination
                },
                message=f"Found {len(enhanced_pois)} places for {trip_request.destination}"
            )
            
        except Exception as e:
            logger.error(f"Error finding places: {e}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def search_places_by_category(
        self,
        location: str,
        category: POICategory,
        maps_tool: MapsApiTool,
        limit: int = 20
    ) -> List[POI]:
        """
        Search for places by specific category.
        
        Args:
            location: Location to search around
            category: POI category to search for
            maps_tool: Google Maps API tool
            limit: Maximum number of results
            
        Returns:
            List of POI objects
        """
        try:
            # Map our categories to Google Places types
            category_mapping = {
                POICategory.RESTAURANT: "restaurant",
                POICategory.ATTRACTION: "tourist_attraction",
                POICategory.MUSEUM: "museum",
                POICategory.PARK: "park",
                POICategory.SHOPPING: "shopping_mall",
                POICategory.NIGHTLIFE: "night_club",
                POICategory.ACCOMMODATION: "lodging",
                POICategory.TRANSPORT: "subway_station",
                POICategory.ENTERTAINMENT: "movie_theater",
                POICategory.RELIGIOUS: "church",
                POICategory.BEACH: "natural_feature",
                POICategory.ADVENTURE: "amusement_park"
            }
            
            google_type = category_mapping.get(category, "point_of_interest")
            
            places = maps_tool.search_nearby_places(
                location=location,
                place_type=google_type,
                radius=5000
            )
            
            pois = []
            for place in places[:limit]:
                try:
                    poi = maps_tool.convert_to_poi(place)
                    pois.append(poi)
                except Exception as e:
                    logger.warning(f"Error converting place to POI: {e}")
                    continue
            
            logger.info(f"Found {len(pois)} {category.value} places near {location}")
            return pois
            
        except Exception as e:
            logger.error(f"Error searching places by category: {e}")
            return []
    
    def _get_cached_places(
        self,
        bigquery_tool: BigQueryTool,
        destination: str,
        radius_km: float,
        interests: List[str]
    ) -> List[Dict[str, Any]]:
        """Get cached places from BigQuery."""
        try:
            # Try to get places by destination name first
            places = bigquery_tool.get_popular_pois(destination, limit=30)
            
            if not places:
                # If no places found by name, try coordinates-based search
                # This would require geocoding the destination first
                places = []
            
            # Filter by interests if provided
            if interests and places:
                places = self._filter_by_interests(places, interests)
            
            return places
            
        except Exception as e:
            logger.error(f"Error getting cached places: {e}")
            return []
    
    def _search_new_places(
        self,
        maps_tool: MapsApiTool,
        bigquery_tool: BigQueryTool,
        trip_request: TripRequest,
        radius: int,
        max_places: int
    ) -> List[POI]:
        """Search for new places using Maps API."""
        pois = []
        
        try:
            # Define place types to search based on interests
            place_types = self._get_place_types_from_interests(trip_request.special_interests)
            
            # If no specific interests, use default types
            if not place_types:
                place_types = ["tourist_attraction", "restaurant", "museum", "park"]
            
            for place_type in place_types:
                if len(pois) >= max_places:
                    break
                
                places = maps_tool.search_nearby_places(
                    location=trip_request.destination,
                    place_type=place_type,
                    radius=radius
                )
                
                for place in places:
                    if len(pois) >= max_places:
                        break
                    
                    try:
                        poi = maps_tool.convert_to_poi(place)
                        pois.append(poi)
                        
                        # Cache the POI for future use
                        bigquery_tool.cache_poi(poi)
                        
                    except Exception as e:
                        logger.warning(f"Error converting place to POI: {e}")
                        continue
            
            logger.info(f"Found {len(pois)} new places for {trip_request.destination}")
            return pois
            
        except Exception as e:
            logger.error(f"Error searching new places: {e}")
            return []
    
    def _filter_places_for_trip(self, pois: List[POI], trip_request: TripRequest) -> List[POI]:
        """Filter places based on trip requirements."""
        filtered_pois = []
        
        for poi in pois:
            # Check if place is suitable for group type
            if trip_request.group_type in poi.suitable_for_groups or not poi.suitable_for_groups:
                # Check budget compatibility
                if self._is_budget_compatible(poi, trip_request.budget_range):
                    # Check accessibility if needed
                    if self._meets_accessibility_needs(poi, trip_request.accessibility_needs):
                        filtered_pois.append(poi)
        
        return filtered_pois
    
    def _enhance_poi_details(self, poi: POI, trip_request: TripRequest) -> POI:
        """Enhance POI with better descriptions and time estimates."""
        try:
            # Generate AI description if not exists or is too short
            if not poi.description or len(poi.description) < 50:
                description_prompt = f"""
Generate a concise, engaging description (1-2 sentences, max 100 words) for this place:

Name: {poi.name}
Category: {poi.category.value}
Rating: {poi.rating or 'N/A'}
Address: {poi.address.formatted_address if poi.address else 'N/A'}

Focus on what makes this place special and why travelers would want to visit. 
Example format: "Lalbagh Botanical Garden, a beautiful sprawling garden with diverse flora and fauna, perfect for peaceful walks and nature photography."
"""
                ai_description = self._call_vertex_ai(description_prompt)
                if ai_description and len(ai_description) > 20:
                    poi.description = ai_description.strip().replace('"', '')
            
            # Estimate visit duration if not set
            if not poi.estimated_visit_duration:
                poi.estimated_visit_duration = self._estimate_visit_duration_by_category(
                    poi.category.value, 
                    trip_request.group_type,
                    poi.rating or 3.0
                )
            
            # Calculate priority score
            poi.popularity_score = self._calculate_priority_score(poi, trip_request)
            
            return poi
            
        except Exception as e:
            logger.error(f"Error enhancing POI details: {e}")
            return poi
    
    def _estimate_visit_duration_by_category(self, category: str, group_type: str, rating: float) -> int:
        """Estimate visit duration based on category, group type, and rating."""
        # Base durations in minutes by category
        base_durations = {
            "restaurant": 90,
            "attraction": 120,
            "museum": 180,
            "park": 90,
            "shopping": 120,
            "nightlife": 150,
            "accommodation": 30,
            "transport": 15,
            "entertainment": 180,
            "religious": 60,
            "beach": 180,
            "adventure": 240,
            "tourist_attraction": 120,
            "amusement_park": 240,
            "zoo": 180,
            "aquarium": 150,
            "library": 90,
            "church": 45,
            "temple": 60,
            "mosque": 45,
            "synagogue": 45
        }
        
        base_duration = base_durations.get(category, 120)
        
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
        if rating >= 4.5:
            duration *= 1.2
        elif rating >= 4.0:
            duration *= 1.1
        elif rating < 3.0:
            duration *= 0.8
        
        return int(duration)
    
    def _calculate_priority_score(self, poi: POI, trip_request: TripRequest) -> float:
        """Calculate priority score for POI based on various factors."""
        score = 0.0
        
        # Base score from rating
        if poi.rating:
            score += poi.rating * 15  # Max 75 points
        
        # Review count factor (more reviews = more reliable)
        if poi.review_count:
            review_score = min(poi.review_count / 100, 10)  # Max 10 points
            score += review_score
        
        # Category relevance to interests
        if trip_request.special_interests:
            category_keywords = {
                "restaurant": ["food", "dining", "cuisine"],
                "museum": ["culture", "history", "art"],
                "park": ["nature", "outdoor", "relaxation"],
                "attraction": ["sightseeing", "tourist", "landmark"],
                "shopping": ["shopping", "market", "souvenir"],
                "religious": ["spiritual", "temple", "church"],
                "beach": ["beach", "water", "swimming"],
                "adventure": ["adventure", "sports", "thrill"]
            }
            
            poi_keywords = category_keywords.get(poi.category.value, [])
            for interest in trip_request.special_interests:
                if any(keyword in interest.lower() for keyword in poi_keywords):
                    score += 10  # Bonus for matching interests
        
        # Price level consideration (budget-friendly gets bonus)
        if poi.price_level:
            if trip_request.budget_range == "budget" and poi.price_level <= 2:
                score += 5
            elif trip_request.budget_range == "luxury" and poi.price_level >= 3:
                score += 5
            elif trip_request.budget_range == "mid-range" and poi.price_level == 2:
                score += 5
        
        return min(score, 100.0)  # Cap at 100

    def _enhance_recommendations(self, pois: List[POI], trip_request: TripRequest) -> List[POI]:
        """Use AI to enhance and rank place recommendations."""
        try:
            if not pois:
                return pois
            
            # First enhance each POI with descriptions and time estimates
            enhanced_pois = []
            for poi in pois:
                enhanced_poi = self._enhance_poi_details(poi, trip_request)
                enhanced_pois.append(enhanced_poi)
            
            # Sort by priority score first
            enhanced_pois.sort(key=lambda p: p.popularity_score or 0, reverse=True)
            
            # Take top POIs for AI ranking (to avoid token limits)
            top_pois = enhanced_pois[:20] if len(enhanced_pois) > 20 else enhanced_pois
            
            # Create prompt for AI ranking
            prompt = self._create_ranking_prompt(top_pois, trip_request)
            
            # Call Vertex AI
            response = self._call_vertex_ai(prompt)
            
            if response:
                # Parse AI response to get ranking
                ranked_top_pois = self._parse_ranking_response(response, top_pois)
                # Add remaining POIs at the end
                remaining_pois = enhanced_pois[20:] if len(enhanced_pois) > 20 else []
                return ranked_top_pois + remaining_pois
            else:
                # Fallback to priority score ranking
                return enhanced_pois
                
        except Exception as e:
            logger.error(f"Error enhancing recommendations: {e}")
            return pois
    
    def _get_place_types_from_interests(self, interests: List[str]) -> List[str]:
        """Map user interests to Google Places types."""
        interest_mapping = {
            "food": ["restaurant", "cafe", "meal_takeaway"],
            "dining": ["restaurant", "cafe"],
            "sightseeing": ["tourist_attraction", "museum", "church"],
            "history": ["museum", "church", "cemetery"],
            "art": ["art_gallery", "museum"],
            "nature": ["park", "zoo", "aquarium"],
            "shopping": ["shopping_mall", "store"],
            "nightlife": ["night_club", "bar"],
            "entertainment": ["movie_theater", "amusement_park"],
            "religious": ["church", "mosque", "temple"],
            "adventure": ["amusement_park", "zoo"],
            "culture": ["museum", "art_gallery", "church"],
            "beach": ["natural_feature"],
            "sports": ["stadium", "gym"]
        }
        
        place_types = set()
        for interest in interests:
            interest_lower = interest.lower()
            for key, types in interest_mapping.items():
                if key in interest_lower:
                    place_types.update(types)
        
        return list(place_types)
    
    def _is_budget_compatible(self, poi: POI, budget_range: str) -> bool:
        """Check if POI price level is compatible with budget range."""
        if not poi.price_level:
            return True  # No price info, assume compatible
        
        budget_mapping = {
            "budget": [1, 2],
            "moderate": [1, 2, 3],
            "luxury": [2, 3, 4],
            "premium": [3, 4]
        }
        
        allowed_levels = budget_mapping.get(budget_range, [1, 2, 3, 4])
        return poi.price_level in allowed_levels
    
    def _meets_accessibility_needs(self, poi: POI, accessibility_needs: List[str]) -> bool:
        """Check if POI meets accessibility requirements."""
        if not accessibility_needs:
            return True
        
        poi_features = [feature.lower() for feature in poi.accessibility_features]
        
        for need in accessibility_needs:
            need_lower = need.lower()
            if "wheelchair" in need_lower and "wheelchair" not in " ".join(poi_features):
                return False
            # Add more accessibility checks as needed
        
        return True
    
    def _filter_by_interests(self, places: List[Dict[str, Any]], interests: List[str]) -> List[Dict[str, Any]]:
        """Filter cached places by user interests."""
        if not interests:
            return places
        
        filtered = []
        interest_keywords = [interest.lower() for interest in interests]
        
        for place in places:
            place_text = f"{place.get('name', '')} {place.get('description', '')} {place.get('category', '')}".lower()
            
            for keyword in interest_keywords:
                if keyword in place_text:
                    filtered.append(place)
                    break
        
        return filtered if filtered else places  # Return all if no matches
    
    def _convert_cached_to_poi(self, cached_place: Dict[str, Any]) -> POI:
        """Convert cached place data to POI object."""
        return POI(
            id=cached_place.get("poi_id", ""),
            name=cached_place.get("name", ""),
            description=cached_place.get("description"),
            category=POICategory(cached_place.get("category", "attraction")),
            coordinates=Coordinates(
                latitude=cached_place.get("latitude", 0.0),
                longitude=cached_place.get("longitude", 0.0)
            ),
            address=Address(**cached_place.get("address", {})),
            rating=cached_place.get("rating"),
            review_count=cached_place.get("review_count", 0),
            price_level=cached_place.get("price_level"),
            opening_hours=cached_place.get("opening_hours", {}),
            website=cached_place.get("website"),
            phone=cached_place.get("phone"),
            photos=cached_place.get("photos", []),
            amenities=cached_place.get("amenities", []),
            suitable_for_groups=[],  # Would need to parse from cached data
            estimated_visit_duration=cached_place.get("estimated_visit_duration"),
            popularity_score=cached_place.get("popularity_score"),
            accessibility_features=cached_place.get("accessibility_features", [])
        )
    
    def _create_ranking_prompt(self, pois: List[POI], trip_request: TripRequest) -> str:
        """Create prompt for AI-based place ranking."""
        places_text = ""
        for i, poi in enumerate(pois[:20]):  # Limit to first 20 for prompt size
            places_text += f"{i+1}. {poi.name} - {poi.category.value} - Rating: {poi.rating or 'N/A'} - {poi.description or 'No description'}\n"
        
        prompt = f"""
You are a travel expert helping to rank places of interest for a trip. 

Trip Details:
- Destination: {trip_request.destination}
- Group Type: {trip_request.group_type.value}
- Budget Range: {trip_request.budget_range.value}
- Number of Travelers: {trip_request.number_of_travelers}
- Special Interests: {', '.join(trip_request.special_interests) if trip_request.special_interests else 'None specified'}
- Trip Duration: {trip_request.duration_days} days

Places to Rank:
{places_text}

Rank these places from most to least suitable for this trip. Consider:
1. Relevance to special interests
2. Suitability for group type and size
3. Budget compatibility
4. Overall quality (rating and reviews)
5. Uniqueness and must-see factor

Return only the ranking as numbers separated by commas (e.g., "3,1,7,2,5,4,6").
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
    
    def _parse_ranking_response(self, response: str, pois: List[POI]) -> List[POI]:
        """Parse AI ranking response and reorder POIs."""
        try:
            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response)
            
            if not numbers:
                return pois
            
            # Convert to indices (subtract 1)
            indices = [int(num) - 1 for num in numbers if int(num) <= len(pois)]
            
            # Reorder POIs based on ranking
            ranked_pois = []
            used_indices = set()
            
            for idx in indices:
                if 0 <= idx < len(pois) and idx not in used_indices:
                    ranked_pois.append(pois[idx])
                    used_indices.add(idx)
            
            # Add any remaining POIs
            for i, poi in enumerate(pois):
                if i not in used_indices:
                    ranked_pois.append(poi)
            
            return ranked_pois
            
        except Exception as e:
            logger.error(f"Error parsing ranking response: {e}")
            return pois